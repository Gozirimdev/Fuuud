from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo.errors import PyMongoError

from app.api import router
from app.core.config import get_settings
from app.db import get_client

settings = get_settings()
settings.validate_security()
app = FastAPI(title="FUUUD API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(router)


@app.get("/ready")
def ready():
    try:
        get_client().admin.command("ping")
    except PyMongoError:
        raise HTTPException(503, "Database is unavailable") from None
    return {"status": "ok"}
