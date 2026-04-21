import tempfile
import unittest

from shared_libraries.python.platform_lib.auth import create_access_token, decode_access_token
from shared_libraries.python.platform_lib.metadata_store import MetadataStore
from shared_libraries.python.platform_lib.replay import sanitize_headers, sanitize_payload
from shared_libraries.python.platform_lib.telemetry import normalize_legacy_metric


class PlatformLibTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.database_url = f"sqlite:///{self.tempdir.name}/platform.sqlite3"
        self.store = MetadataStore(self.database_url)
        self.store.ensure_schema()

    def tearDown(self):
        self.tempdir.cleanup()

    def test_token_roundtrip(self):
        token = create_access_token({"sub": "user-1", "org_id": "demo-tenant"}, "secret", 60)
        claims = decode_access_token(token, "secret")
        self.assertEqual(claims["sub"], "user-1")
        self.assertEqual(claims["org_id"], "demo-tenant")

    def test_metadata_store_uses_slug_as_org_id(self):
        org = self.store.create_org("Demo Tenant", "demo-tenant")
        self.assertEqual(org.id, "demo-tenant")
        self.assertEqual(self.store.list_orgs()[0].slug, "demo-tenant")

    def test_api_key_can_be_authenticated(self):
        self.store.create_org("Demo Tenant", "demo-tenant")
        record = self.store.create_api_key("demo-tenant", "Console Key")
        authed = self.store.authenticate_api_key(record.raw_api_key)
        self.assertIsNotNone(authed)
        self.assertEqual(authed.org_id, "demo-tenant")

    def test_incident_timeline_roundtrip(self):
        incident = self.store.upsert_incident(
            org_id="demo-tenant",
            source_key="demo:svc:endpoint",
            title="Latency incident",
            severity="critical",
            summary="p95 crossed threshold",
            evidence={"alerts": ["High latency"]},
        )
        self.store.append_incident_event(incident.id, "alert-fired", "High latency", {"severity": "critical"})
        timeline = self.store.get_incident_timeline(incident.id)
        self.assertEqual(len(timeline), 1)
        self.assertEqual(timeline[0].event_type, "alert-fired")

    def test_legacy_metric_normalization(self):
        normalized = normalize_legacy_metric(
            {
                "endpoint_id": "google-test",
                "timestamp": 1710000000,
                "latency": 0.25,
                "status_code": 200,
                "region": "local",
            }
        )
        self.assertEqual(normalized.tenant_id, "demo-tenant")
        self.assertAlmostEqual(normalized.latency_ms or 0.0, 250.0)

    def test_payload_sanitization_redacts_secrets(self):
        headers = sanitize_headers({"Authorization": "secret", "Content-Type": "application/json"})
        payload = sanitize_payload({"token": "secret", "nested": {"password": "pw"}})
        self.assertEqual(headers["Authorization"], "[REDACTED]")
        self.assertEqual(payload["token"], "[REDACTED]")
        self.assertEqual(payload["nested"]["password"], "[REDACTED]")


if __name__ == "__main__":
    unittest.main()
