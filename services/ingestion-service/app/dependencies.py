import os
import sys

from fastapi import Header, HTTPException, status

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../shared_libraries/python")))

from platform_lib.metadata_store import MetadataStore

from app.config import settings


store = MetadataStore(settings.DATABASE_URL)
store.ensure_schema()


def get_store() -> MetadataStore:
    return store


def authenticate_ingest_key(x_api_key: str = Header(..., alias="X-API-Key")):
    record = store.authenticate_api_key(x_api_key)
    if record is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid ingestion API key.")
    return record
