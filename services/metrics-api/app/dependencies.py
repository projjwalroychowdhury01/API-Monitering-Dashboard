import os
import sys

from fastapi import Request

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../shared_libraries/python")))

from platform_lib.metadata_store import MetadataStore

from app.config import settings


store = MetadataStore(settings.DATABASE_URL)
store.ensure_schema()


def get_store() -> MetadataStore:
    return store


def resolve_tenant_id(request: Request, tenant_id: str | None = None) -> str:
    return tenant_id or request.headers.get("X-Tenant-ID") or "demo-tenant"
