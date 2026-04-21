from __future__ import annotations

from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.config import settings
from app.dependencies import enforce_org_access, get_current_identity, get_store

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../shared_libraries/python")))

from platform_lib.auth import create_access_token
from platform_lib.metadata_store import MetadataStore
from platform_lib.replay import sanitize_headers, sanitize_payload


router = APIRouter(prefix="/v1", tags=["control-plane"])


class CreateOrgRequest(BaseModel):
    name: str
    slug: str
    description: str | None = None


class CreateUserRequest(BaseModel):
    org_id: str
    email: str
    full_name: str
    role: str = "viewer"


class CreateApiKeyRequest(BaseModel):
    org_id: str
    name: str
    scopes: list[str] = Field(default_factory=lambda: ["ingest:write"])


class CreateAlertRuleRequest(BaseModel):
    org_id: str
    name: str
    metric_name: str
    operator: str = "gt"
    threshold: float
    severity: str = "warning"
    enabled: bool = True
    cool_down_seconds: int = 300


class TokenRequest(BaseModel):
    org_id: str
    user_id: str
    role: str = "admin"
    email: str | None = None


class CreateReplayRequest(BaseModel):
    org_id: str
    endpoint_id: str
    method: str = "GET"
    url: str
    headers: dict[str, Any] = Field(default_factory=dict)
    body: Any | None = None
    execute_immediately: bool = True


@router.post("/auth/token")
def issue_access_token(payload: TokenRequest):
    token = create_access_token(
        {
            "sub": payload.user_id,
            "org_id": payload.org_id,
            "role": payload.role,
            "email": payload.email,
        },
        settings.JWT_SECRET_KEY,
        settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    return {"status": "success", "data": {"access_token": token, "token_type": "bearer"}}


@router.post("/orgs", status_code=status.HTTP_201_CREATED)
def create_org(payload: CreateOrgRequest, store: MetadataStore = Depends(get_store)):
    org = store.create_org(payload.name, payload.slug, payload.description)
    return {"status": "success", "data": org.model_dump()}


@router.get("/orgs")
def list_orgs(
    _: dict[str, Any] = Depends(get_current_identity),
    store: MetadataStore = Depends(get_store),
):
    return {"status": "success", "data": [org.model_dump() for org in store.list_orgs()]}


@router.post("/users", status_code=status.HTTP_201_CREATED)
def create_user(
    payload: CreateUserRequest,
    identity: dict[str, Any] = Depends(get_current_identity),
    store: MetadataStore = Depends(get_store),
):
    enforce_org_access(payload.org_id, identity)
    user = store.create_user(payload.org_id, payload.email, payload.full_name, payload.role)
    return {"status": "success", "data": user.model_dump()}


@router.get("/users")
def list_users(
    org_id: str,
    identity: dict[str, Any] = Depends(get_current_identity),
    store: MetadataStore = Depends(get_store),
):
    enforce_org_access(org_id, identity)
    return {"status": "success", "data": [user.model_dump() for user in store.list_users(org_id)]}


@router.post("/api-keys", status_code=status.HTTP_201_CREATED)
def create_api_key(
    payload: CreateApiKeyRequest,
    identity: dict[str, Any] = Depends(get_current_identity),
    store: MetadataStore = Depends(get_store),
):
    enforce_org_access(payload.org_id, identity)
    record = store.create_api_key(payload.org_id, payload.name, payload.scopes, identity.get("sub"))
    return {"status": "success", "data": record.model_dump()}


@router.get("/api-keys")
def list_api_keys(
    org_id: str,
    identity: dict[str, Any] = Depends(get_current_identity),
    store: MetadataStore = Depends(get_store),
):
    enforce_org_access(org_id, identity)
    return {"status": "success", "data": [item.model_dump() for item in store.list_api_keys(org_id)]}


@router.post("/alerts", status_code=status.HTTP_201_CREATED)
def create_alert_rule(
    payload: CreateAlertRuleRequest,
    identity: dict[str, Any] = Depends(get_current_identity),
    store: MetadataStore = Depends(get_store),
):
    enforce_org_access(payload.org_id, identity)
    rule = store.create_alert_rule(
        payload.org_id,
        payload.name,
        payload.metric_name,
        payload.operator,
        payload.threshold,
        payload.severity,
        payload.enabled,
        payload.cool_down_seconds,
    )
    return {"status": "success", "data": rule.model_dump()}


@router.get("/alerts")
def list_alert_rules(
    org_id: str,
    identity: dict[str, Any] = Depends(get_current_identity),
    store: MetadataStore = Depends(get_store),
):
    enforce_org_access(org_id, identity)
    return {"status": "success", "data": [rule.model_dump() for rule in store.list_alert_rules(org_id)]}


@router.get("/incidents")
def list_incidents(
    org_id: str,
    identity: dict[str, Any] = Depends(get_current_identity),
    store: MetadataStore = Depends(get_store),
):
    enforce_org_access(org_id, identity)
    return {"status": "success", "data": [incident.model_dump() for incident in store.list_incidents(org_id)]}


@router.get("/incidents/{incident_id}")
def get_incident(
    incident_id: str,
    identity: dict[str, Any] = Depends(get_current_identity),
    store: MetadataStore = Depends(get_store),
):
    incident = store.get_incident(incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found.")
    enforce_org_access(incident.org_id, identity)
    return {"status": "success", "data": incident.model_dump()}


@router.get("/incidents/{incident_id}/timeline")
def get_incident_timeline(
    incident_id: str,
    identity: dict[str, Any] = Depends(get_current_identity),
    store: MetadataStore = Depends(get_store),
):
    incident = store.get_incident(incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found.")
    enforce_org_access(incident.org_id, identity)
    return {
        "status": "success",
        "data": [event.model_dump() for event in store.get_incident_timeline(incident_id)],
    }


@router.post("/replay", status_code=status.HTTP_202_ACCEPTED)
def create_replay_job(
    payload: CreateReplayRequest,
    identity: dict[str, Any] = Depends(get_current_identity),
    store: MetadataStore = Depends(get_store),
):
    enforce_org_access(payload.org_id, identity)
    sanitized_headers = sanitize_headers(payload.headers)
    sanitized_body = sanitize_payload(payload.body, settings.REPLAY_MAX_BODY_BYTES)
    replay_job = store.create_replay_job(
        payload.org_id,
        payload.endpoint_id,
        payload.method.upper(),
        payload.url,
        sanitized_headers,
        sanitized_body,
    )

    response_data: dict[str, Any] = {}
    if payload.execute_immediately:
        try:
            response = httpx.request(
                payload.method.upper(),
                payload.url,
                headers=sanitized_headers,
                json=sanitized_body if isinstance(sanitized_body, (dict, list)) else None,
                content=sanitized_body if isinstance(sanitized_body, str) else None,
                timeout=20.0,
            )
            response_data = {
                "status_code": response.status_code,
                "body": sanitize_payload(_parse_response_body(response), settings.REPLAY_MAX_BODY_BYTES),
            }
            store.update_replay_job_result(replay_job.id, "completed", response.status_code, response_data["body"])
        except Exception as exc:  # pragma: no cover - network can be intentionally unavailable in tests
            response_data = {"error": str(exc)}
            store.update_replay_job_result(replay_job.id, "failed", None, response_data)

    result = store.get_replay_job(replay_job.id)
    return {"status": "success", "data": {"job": result.model_dump() if result else replay_job.model_dump(), "result": response_data}}


@router.get("/replay/{replay_job_id}")
def get_replay_job(
    replay_job_id: str,
    identity: dict[str, Any] = Depends(get_current_identity),
    store: MetadataStore = Depends(get_store),
):
    replay_job = store.get_replay_job(replay_job_id)
    if replay_job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Replay job not found.")
    enforce_org_access(replay_job.org_id, identity)
    return {"status": "success", "data": replay_job.model_dump()}


def _parse_response_body(response: httpx.Response) -> Any:
    content_type = response.headers.get("content-type", "")
    if "application/json" in content_type:
        return response.json()
    return response.text
