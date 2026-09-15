"""MongoDB connection, BSON mapping and transaction-scoped document access."""

from collections.abc import Callable, Generator
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from functools import lru_cache
from typing import TypeVar

from bson import Decimal128, ObjectId
from pymongo import MongoClient, ReturnDocument
from pymongo.client_session import ClientSession
from pymongo.database import Database
from pymongo.read_concern import ReadConcern
from pymongo.write_concern import WriteConcern

from app.core.config import get_settings
from app.models import Document

T = TypeVar("T", bound=Document)
R = TypeVar("R")


def encode(value, key=""):
    if isinstance(value, dict):
        return {
            ("_id" if k == "id" else k): encode(v, key if k.startswith("$") else k)
            for k, v in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [encode(v, key) for v in value]
    if value is None:
        return None
    if (key == "id" or key == "_id" or key.endswith("_id")) and isinstance(value, str):
        return ObjectId(value)
    if isinstance(value, Decimal):
        return Decimal128(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (date, time)) and not isinstance(value, datetime):
        return value.isoformat()
    return value


def decode(value):
    if isinstance(value, dict):
        return {("id" if k == "_id" else k): decode(v) for k, v in value.items()}
    if isinstance(value, list):
        return [decode(v) for v in value]
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, Decimal128):
        return value.to_decimal()
    return value


@lru_cache
def get_client() -> MongoClient:
    uri = get_settings().mongodb_uri.get_secret_value()
    if not uri.startswith(("mongodb://", "mongodb+srv://")):
        raise RuntimeError("MONGODB_URI must be a MongoDB connection URI.")
    return MongoClient(
        uri,
        tz_aware=True,
        serverSelectionTimeoutMS=10000,
        connectTimeoutMS=10000,
        appname="fuuud-api",
    )


class Store:
    def __init__(self, database: Database, session: ClientSession | None = None):
        self.database = database
        self.session = session

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def collection(self, model: type[T]):
        return self.database[model.collection]

    def get(self, model: type[T], item_id: str) -> T | None:
        return self.find_one(model, {"id": item_id})

    def find_one(self, model: type[T], query=None) -> T | None:
        data = self.collection(model).find_one(encode(query or {}), session=self.session)
        return model.model_validate(decode(data)) if data else None

    def find(self, model: type[T], query=None, *, sort=None, skip=0, limit=0) -> list[T]:
        cursor = self.collection(model).find(encode(query or {}), session=self.session)
        if sort:
            cursor = cursor.sort(sort)
        return [model.model_validate(decode(d)) for d in cursor.skip(skip).limit(limit)]

    def count(self, model: type[T], query=None) -> int:
        return self.collection(model).count_documents(encode(query or {}), session=self.session)

    def insert(self, item: T) -> T:
        self.collection(type(item)).insert_one(encode(item.model_dump()), session=self.session)
        return item

    def save(self, item: T) -> T:
        # Intended for fixtures and seed tooling; service writes use conditional updates.
        self.collection(type(item)).replace_one(
            {"_id": ObjectId(item.id)}, encode(item.model_dump()), session=self.session
        )
        return item

    def update(self, model: type[T], query: dict, changes: dict, *, many=False):
        collection = self.collection(model)
        method = collection.update_many if many else collection.update_one
        return method(encode(query), encode(changes), session=self.session)

    def claim(self, model: type[T], query: dict, changes: dict, *, sort=None) -> T | None:
        data = self.collection(model).find_one_and_update(
            encode(query),
            encode(changes),
            sort=sort,
            return_document=ReturnDocument.AFTER,
            session=self.session,
        )
        return model.model_validate(decode(data)) if data else None

    def transaction(self, callback: Callable[["Store"], R]) -> R:
        if self.session is not None:
            return callback(self)
        with self.database.client.start_session() as session:
            return session.with_transaction(
                lambda active: callback(Store(self.database, active)),
                read_concern=ReadConcern("snapshot"),
                write_concern=WriteConcern("majority"),
            )


def get_store() -> Store:
    return Store(get_client()[get_settings().mongodb_database])


def get_db() -> Generator[Store]:
    yield get_store()
