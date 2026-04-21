import os
import sys
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../shared_libraries/python")))

from platform_lib.auth import decode_access_token
from platform_lib.metadata_store import MetadataStore

from app.config import settings


security = HTTPBearer(auto_error=False)
store = MetadataStore(settings.DATABASE_URL)
store.ensure_schema()


def get_store() -> MetadataStore:
    return store


def get_current_identity(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict[str, Any]:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token required.")

    try:
        return decode_access_token(credentials.credentials, settings.JWT_SECRET_KEY)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


def enforce_org_access(org_id: str, identity: dict[str, Any]) -> None:
    if identity.get("role") == "platform_admin":
        return
    if identity.get("org_id") != org_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant scope violation.")
