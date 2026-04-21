from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import urlparse
from uuid import uuid4

from pydantic import BaseModel, Field

from .auth import generate_api_key, hash_api_key


class Organization(BaseModel):
    id: str
    name: str
    slug: str
    description: str | None = None
    created_at: datetime


class PlatformUser(BaseModel):
    id: str
    org_id: str
    email: str
    full_name: str
    role: str = "viewer"
    created_at: datetime


class ApiKeyRecord(BaseModel):
    id: str
    org_id: str
    name: str
    key_prefix: str
    scopes: list[str] = Field(default_factory=list)
    created_by: str | None = None
    created_at: datetime
    raw_api_key: str | None = None


class AlertRule(BaseModel):
    id: str
    org_id: str
    name: str
    metric_name: str
    operator: str
    threshold: float
    severity: str
    enabled: bool
    cool_down_seconds: int
    created_at: datetime


class Incident(BaseModel):
    id: str
    org_id: str
    source_key: str
    title: str
    severity: str
    summary: str
    status: str
    created_at: datetime
    updated_at: datetime
    evidence: dict[str, Any] = Field(default_factory=dict)


class IncidentEvent(BaseModel):
    id: str
    incident_id: str
    event_type: str
    message: str
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class ReplayJob(BaseModel):
    id: str
    org_id: str
    endpoint_id: str
    method: str
    url: str
    request_headers: dict[str, Any] = Field(default_factory=dict)
    request_body: Any | None = None
    response_status: int | None = None
    response_body: Any | None = None
    status: str
    created_at: datetime
    updated_at: datetime


@dataclass
class _SqlDialect:
    placeholder: str
    json_type: str


class MetadataStore:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        self.is_sqlite = database_url.startswith("sqlite:///")
        self.dialect = _SqlDialect(placeholder="?", json_type="TEXT") if self.is_sqlite else _SqlDialect(
            placeholder="%s",
            json_type="JSON"
        )

        if self.is_sqlite:
            self.sqlite_path = Path(database_url.replace("sqlite:///", "", 1))
            self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connection(self) -> Iterator[Any]:
        if self.is_sqlite:
            conn = sqlite3.connect(self.sqlite_path)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
                conn.commit()
            finally:
                conn.close()
            return

        try:
            import psycopg
        except ImportError as exc:
            raise RuntimeError("psycopg is required for PostgreSQL metadata storage.") from exc

        conn = psycopg.connect(self.database_url)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def ensure_schema(self) -> None:
        statements = [
            f"""
            CREATE TABLE IF NOT EXISTS organizations (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                slug TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TEXT NOT NULL
            )
            """,
            f"""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                org_id TEXT NOT NULL,
                email TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """,
            f"""
            CREATE TABLE IF NOT EXISTS api_keys (
                id TEXT PRIMARY KEY,
                org_id TEXT NOT NULL,
                name TEXT NOT NULL,
                key_prefix TEXT NOT NULL,
                hashed_key TEXT NOT NULL,
                scopes {self.dialect.json_type} NOT NULL,
                created_by TEXT,
                created_at TEXT NOT NULL
            )
            """,
            f"""
            CREATE TABLE IF NOT EXISTS alert_rules (
                id TEXT PRIMARY KEY,
                org_id TEXT NOT NULL,
                name TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                operator TEXT NOT NULL,
                threshold REAL NOT NULL,
                severity TEXT NOT NULL,
                enabled INTEGER NOT NULL,
                cool_down_seconds INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
            """,
            f"""
            CREATE TABLE IF NOT EXISTS incidents (
                id TEXT PRIMARY KEY,
                org_id TEXT NOT NULL,
                source_key TEXT NOT NULL,
                title TEXT NOT NULL,
                severity TEXT NOT NULL,
                summary TEXT NOT NULL,
                status TEXT NOT NULL,
                evidence {self.dialect.json_type} NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """,
            f"""
            CREATE TABLE IF NOT EXISTS incident_events (
                id TEXT PRIMARY KEY,
                incident_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                message TEXT NOT NULL,
                payload {self.dialect.json_type} NOT NULL,
                created_at TEXT NOT NULL
            )
            """,
            f"""
            CREATE TABLE IF NOT EXISTS replay_jobs (
                id TEXT PRIMARY KEY,
                org_id TEXT NOT NULL,
                endpoint_id TEXT NOT NULL,
                method TEXT NOT NULL,
                url TEXT NOT NULL,
                request_headers {self.dialect.json_type} NOT NULL,
                request_body {self.dialect.json_type},
                response_status INTEGER,
                response_body {self.dialect.json_type},
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """,
        ]
        with self.connection() as conn:
            cursor = conn.cursor()
            for statement in statements:
                cursor.execute(statement)

    def create_org(self, name: str, slug: str, description: str | None = None) -> Organization:
        org = Organization(id=slug, name=name, slug=slug, description=description, created_at=_utcnow())
        self._execute(
            "INSERT INTO organizations (id, name, slug, description, created_at) VALUES ({}, {}, {}, {}, {})".format(
                *([self.dialect.placeholder] * 5)
            ),
            (org.id, org.name, org.slug, org.description, org.created_at.isoformat()),
        )
        return org

    def list_orgs(self) -> list[Organization]:
        rows = self._fetchall("SELECT * FROM organizations ORDER BY created_at DESC")
        return [Organization(**self._row_to_dict(row)) for row in rows]

    def create_user(self, org_id: str, email: str, full_name: str, role: str = "viewer") -> PlatformUser:
        user = PlatformUser(
            id=str(uuid4()),
            org_id=org_id,
            email=email,
            full_name=full_name,
            role=role,
            created_at=_utcnow(),
        )
        self._execute(
            "INSERT INTO users (id, org_id, email, full_name, role, created_at) VALUES ({}, {}, {}, {}, {}, {})".format(
                *([self.dialect.placeholder] * 6)
            ),
            (user.id, user.org_id, user.email, user.full_name, user.role, user.created_at.isoformat()),
        )
        return user

    def list_users(self, org_id: str) -> list[PlatformUser]:
        rows = self._fetchall(
            f"SELECT * FROM users WHERE org_id = {self.dialect.placeholder} ORDER BY created_at DESC",
            (org_id,),
        )
        return [PlatformUser(**self._row_to_dict(row)) for row in rows]

    def create_api_key(
        self,
        org_id: str,
        name: str,
        scopes: list[str] | None = None,
        created_by: str | None = None,
    ) -> ApiKeyRecord:
        scopes = scopes or ["ingest:write"]
        key_id, raw_api_key = generate_api_key()
        record = ApiKeyRecord(
            id=key_id,
            org_id=org_id,
            name=name,
            key_prefix=raw_api_key[:16],
            scopes=scopes,
            created_by=created_by,
            created_at=_utcnow(),
            raw_api_key=raw_api_key,
        )
        self._execute(
            "INSERT INTO api_keys (id, org_id, name, key_prefix, hashed_key, scopes, created_by, created_at) "
            "VALUES ({}, {}, {}, {}, {}, {}, {}, {})".format(*([self.dialect.placeholder] * 8)),
            (
                record.id,
                record.org_id,
                record.name,
                record.key_prefix,
                hash_api_key(raw_api_key),
                json.dumps(record.scopes),
                record.created_by,
                record.created_at.isoformat(),
            ),
        )
        return record

    def list_api_keys(self, org_id: str) -> list[ApiKeyRecord]:
        rows = self._fetchall(
            f"SELECT id, org_id, name, key_prefix, scopes, created_by, created_at FROM api_keys "
            f"WHERE org_id = {self.dialect.placeholder} ORDER BY created_at DESC",
            (org_id,),
        )
        records = []
        for row in rows:
            payload = self._row_to_dict(row)
            payload["scopes"] = _parse_json(payload.get("scopes"), [])
            records.append(ApiKeyRecord(**payload))
        return records

    def authenticate_api_key(self, raw_api_key: str) -> ApiKeyRecord | None:
        rows = self._fetchall(
            f"SELECT id, org_id, name, key_prefix, scopes, created_by, created_at FROM api_keys "
            f"WHERE hashed_key = {self.dialect.placeholder}",
            (hash_api_key(raw_api_key),),
        )
        if not rows:
            return None
        payload = self._row_to_dict(rows[0])
        payload["scopes"] = _parse_json(payload.get("scopes"), [])
        return ApiKeyRecord(**payload)

    def create_alert_rule(
        self,
        org_id: str,
        name: str,
        metric_name: str,
        operator: str,
        threshold: float,
        severity: str = "warning",
        enabled: bool = True,
        cool_down_seconds: int = 300,
    ) -> AlertRule:
        rule = AlertRule(
            id=str(uuid4()),
            org_id=org_id,
            name=name,
            metric_name=metric_name,
            operator=operator,
            threshold=threshold,
            severity=severity,
            enabled=enabled,
            cool_down_seconds=cool_down_seconds,
            created_at=_utcnow(),
        )
        self._execute(
            "INSERT INTO alert_rules (id, org_id, name, metric_name, operator, threshold, severity, enabled, cool_down_seconds, created_at) "
            "VALUES ({}, {}, {}, {}, {}, {}, {}, {}, {}, {})".format(*([self.dialect.placeholder] * 10)),
            (
                rule.id,
                rule.org_id,
                rule.name,
                rule.metric_name,
                rule.operator,
                rule.threshold,
                rule.severity,
                int(rule.enabled),
                rule.cool_down_seconds,
                rule.created_at.isoformat(),
            ),
        )
        return rule

    def list_alert_rules(self, org_id: str) -> list[AlertRule]:
        rows = self._fetchall(
            f"SELECT * FROM alert_rules WHERE org_id = {self.dialect.placeholder} ORDER BY created_at DESC",
            (org_id,),
        )
        rules = []
        for row in rows:
            payload = self._row_to_dict(row)
            payload["enabled"] = bool(payload.get("enabled"))
            rules.append(AlertRule(**payload))
        return rules

    def upsert_incident(
        self,
        org_id: str,
        source_key: str,
        title: str,
        severity: str,
        summary: str,
        status: str = "open",
        evidence: dict[str, Any] | None = None,
    ) -> Incident:
        evidence = evidence or {}
        existing = self._fetchall(
            f"SELECT * FROM incidents WHERE org_id = {self.dialect.placeholder} "
            f"AND source_key = {self.dialect.placeholder} AND status != {self.dialect.placeholder}",
            (org_id, source_key, "resolved"),
        )
        now = _utcnow()
        if existing:
            current = self._row_to_dict(existing[0])
            current["title"] = title
            current["severity"] = severity
            current["summary"] = summary
            current["status"] = status
            current["evidence"] = evidence
            current["updated_at"] = now
            self._execute(
                f"UPDATE incidents SET title = {self.dialect.placeholder}, severity = {self.dialect.placeholder}, "
                f"summary = {self.dialect.placeholder}, status = {self.dialect.placeholder}, evidence = {self.dialect.placeholder}, "
                f"updated_at = {self.dialect.placeholder} WHERE id = {self.dialect.placeholder}",
                (
                    current["title"],
                    current["severity"],
                    current["summary"],
                    current["status"],
                    json.dumps(current["evidence"]),
                    current["updated_at"].isoformat() if isinstance(current["updated_at"], datetime) else str(current["updated_at"]),
                    current["id"],
                ),
            )
            if not isinstance(current["created_at"], datetime):
                current["created_at"] = _parse_datetime(current["created_at"])
            return Incident(**current)

        incident = Incident(
            id=str(uuid4()),
            org_id=org_id,
            source_key=source_key,
            title=title,
            severity=severity,
            summary=summary,
            status=status,
            evidence=evidence,
            created_at=now,
            updated_at=now,
        )
        self._execute(
            "INSERT INTO incidents (id, org_id, source_key, title, severity, summary, status, evidence, created_at, updated_at) "
            "VALUES ({}, {}, {}, {}, {}, {}, {}, {}, {}, {})".format(*([self.dialect.placeholder] * 10)),
            (
                incident.id,
                incident.org_id,
                incident.source_key,
                incident.title,
                incident.severity,
                incident.summary,
                incident.status,
                json.dumps(incident.evidence),
                incident.created_at.isoformat(),
                incident.updated_at.isoformat(),
            ),
        )
        return incident

    def list_incidents(self, org_id: str) -> list[Incident]:
        rows = self._fetchall(
            f"SELECT * FROM incidents WHERE org_id = {self.dialect.placeholder} ORDER BY updated_at DESC",
            (org_id,),
        )
        incidents = []
        for row in rows:
            payload = self._row_to_dict(row)
            payload["evidence"] = _parse_json(payload.get("evidence"), {})
            incidents.append(Incident(**payload))
        return incidents

    def get_incident(self, incident_id: str) -> Incident | None:
        rows = self._fetchall(
            f"SELECT * FROM incidents WHERE id = {self.dialect.placeholder}",
            (incident_id,),
        )
        if not rows:
            return None
        payload = self._row_to_dict(rows[0])
        payload["evidence"] = _parse_json(payload.get("evidence"), {})
        return Incident(**payload)

    def append_incident_event(
        self,
        incident_id: str,
        event_type: str,
        message: str,
        payload: dict[str, Any] | None = None,
    ) -> IncidentEvent:
        event = IncidentEvent(
            id=str(uuid4()),
            incident_id=incident_id,
            event_type=event_type,
            message=message,
            payload=payload or {},
            created_at=_utcnow(),
        )
        self._execute(
            "INSERT INTO incident_events (id, incident_id, event_type, message, payload, created_at) "
            "VALUES ({}, {}, {}, {}, {}, {})".format(*([self.dialect.placeholder] * 6)),
            (
                event.id,
                event.incident_id,
                event.event_type,
                event.message,
                json.dumps(event.payload),
                event.created_at.isoformat(),
            ),
        )
        return event

    def get_incident_timeline(self, incident_id: str) -> list[IncidentEvent]:
        rows = self._fetchall(
            f"SELECT * FROM incident_events WHERE incident_id = {self.dialect.placeholder} ORDER BY created_at ASC",
            (incident_id,),
        )
        timeline = []
        for row in rows:
            payload = self._row_to_dict(row)
            payload["payload"] = _parse_json(payload.get("payload"), {})
            timeline.append(IncidentEvent(**payload))
        return timeline

    def create_replay_job(
        self,
        org_id: str,
        endpoint_id: str,
        method: str,
        url: str,
        request_headers: dict[str, Any],
        request_body: Any | None,
    ) -> ReplayJob:
        now = _utcnow()
        job = ReplayJob(
            id=str(uuid4()),
            org_id=org_id,
            endpoint_id=endpoint_id,
            method=method,
            url=url,
            request_headers=request_headers,
            request_body=request_body,
            status="queued",
            created_at=now,
            updated_at=now,
        )
        self._execute(
            "INSERT INTO replay_jobs (id, org_id, endpoint_id, method, url, request_headers, request_body, response_status, response_body, status, created_at, updated_at) "
            "VALUES ({}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {})".format(*([self.dialect.placeholder] * 12)),
            (
                job.id,
                job.org_id,
                job.endpoint_id,
                job.method,
                job.url,
                json.dumps(job.request_headers),
                json.dumps(job.request_body, default=str) if job.request_body is not None else None,
                job.response_status,
                json.dumps(job.response_body, default=str) if job.response_body is not None else None,
                job.status,
                job.created_at.isoformat(),
                job.updated_at.isoformat(),
            ),
        )
        return job

    def update_replay_job_result(
        self,
        replay_job_id: str,
        status: str,
        response_status: int | None,
        response_body: Any | None,
    ) -> None:
        self._execute(
            f"UPDATE replay_jobs SET status = {self.dialect.placeholder}, response_status = {self.dialect.placeholder}, "
            f"response_body = {self.dialect.placeholder}, updated_at = {self.dialect.placeholder} "
            f"WHERE id = {self.dialect.placeholder}",
            (
                status,
                response_status,
                json.dumps(response_body, default=str) if response_body is not None else None,
                _utcnow().isoformat(),
                replay_job_id,
            ),
        )

    def get_replay_job(self, replay_job_id: str) -> ReplayJob | None:
        rows = self._fetchall(
            f"SELECT * FROM replay_jobs WHERE id = {self.dialect.placeholder}",
            (replay_job_id,),
        )
        if not rows:
            return None
        payload = self._row_to_dict(rows[0])
        payload["request_headers"] = _parse_json(payload.get("request_headers"), {})
        payload["request_body"] = _parse_json(payload.get("request_body"))
        payload["response_body"] = _parse_json(payload.get("response_body"))
        return ReplayJob(**payload)

    def _execute(self, query: str, params: tuple[Any, ...] = ()) -> None:
        with self.connection() as conn:
            conn.cursor().execute(query, params)

    def _fetchall(self, query: str, params: tuple[Any, ...] = ()) -> list[Any]:
        with self.connection() as conn:
            if self.is_sqlite:
                cursor = conn.cursor()
            else:
                from psycopg.rows import dict_row

                cursor = conn.cursor(row_factory=dict_row)
            cursor.execute(query, params)
            return cursor.fetchall()

    def _row_to_dict(self, row: Any) -> dict[str, Any]:
        if isinstance(row, sqlite3.Row):
            data = dict(row)
        elif isinstance(row, dict):
            data = dict(row)
        elif hasattr(row, "_mapping"):
            data = dict(row._mapping)
        else:
            if not hasattr(row, "__iter__"):
                raise TypeError("Unsupported database row type.")
            data = dict(row)
        for key, value in list(data.items()):
            if key.endswith("_at") and isinstance(value, str):
                data[key] = _parse_datetime(value)
        return data


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _parse_json(value: Any, default: Any = None) -> Any:
    if value in (None, ""):
        return default
    if isinstance(value, (dict, list)):
        return value
    return json.loads(value)
