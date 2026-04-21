import json
import smtplib
from email.message import EmailMessage
from typing import List

import httpx

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../shared_libraries/python")))

from platform_lib.realtime import EventBus

from app.alert import Alert
from app.config import settings


event_bus = EventBus(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    channel=settings.REDIS_CHANNEL_PLATFORM_EVENTS,
)


def send_alerts(incident_id: str, alerts: List[Alert]) -> None:
    for alert in alerts:
        payload = {
            "incident_id": incident_id,
            "org_id": alert.org_id,
            "service_name": alert.service_name,
            "endpoint_id": alert.endpoint_id,
            "type": alert.type,
            "severity": alert.severity,
            "message": alert.message,
            "current_value": alert.current_value,
            "threshold": alert.threshold,
        }
        print(f"[ALERT:{alert.severity.upper()}] {alert.service_name}/{alert.endpoint_id} | {alert.message}")
        event_bus.publish("incident.alert", payload)
        _send_webhook(payload)
        _send_email(payload)


def _send_webhook(payload: dict) -> None:
    if not settings.ALERT_WEBHOOK_URL:
        return
    try:
        httpx.post(settings.ALERT_WEBHOOK_URL, json=payload, timeout=10.0)
    except Exception:
        pass


def _send_email(payload: dict) -> None:
    if not settings.SMTP_HOST:
        return
    try:
        message = EmailMessage()
        message["Subject"] = f"[{payload['severity'].upper()}] Incident intelligence alert"
        message["From"] = settings.SMTP_FROM
        message["To"] = settings.SMTP_FROM
        message.set_content(json.dumps(payload, indent=2))
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as client:
            client.send_message(message)
    except Exception:
        pass
