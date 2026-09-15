import re
from datetime import date
from decimal import Decimal

from app.db import Store
from app.models import Availability, Practitioner, User


class UserRepository:
    def __init__(self, db: Store):
        self.db = db

    def by_email(self, email: str) -> User | None:
        return self.db.find_one(User, {"email": email.strip().lower()})

    def add(self, user: User) -> User:
        return self.db.insert(user)


class DoctorRepository:
    def __init__(self, db: Store):
        self.db = db

    def query(
        self,
        search: str | None = None,
        specialty: str | None = None,
        city: str | None = None,
        state: str | None = None,
        country: str | None = None,
        max_fee: Decimal | None = None,
        available_date: date | None = None,
        verified_only: bool = False,
    ) -> dict:
        query = {}
        if search:
            term = re.escape(search.strip())
            query["$or"] = [
                {field: {"$regex": term, "$options": "i"}}
                for field in ["first_name", "last_name", "specialty"]
            ] + [
                {
                    "$expr": {
                        "$regexMatch": {
                            "input": {"$concat": ["$first_name", " ", "$last_name"]},
                            "regex": term,
                            "options": "i",
                        }
                    }
                }
            ]
        if specialty:
            query["specialty"] = specialty
        for field, value in [("city", city), ("state", state), ("country", country)]:
            if value:
                query[field] = {"$regex": "^" + re.escape(value) + "$", "$options": "i"}
        if max_fee is not None:
            query["consultation_fee"] = {"$lte": max_fee}
        if verified_only:
            query["verification_status"] = "verified"
        if available_date:
            slots = self.db.find(Availability, {"date": available_date, "status": "available"})
            query["id"] = {"$in": list({slot.practitioner_id for slot in slots})}
        return query

    def get(self, doctor_id: str) -> Practitioner | None:
        return self.db.get(Practitioner, doctor_id)
