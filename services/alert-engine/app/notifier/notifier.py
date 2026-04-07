# notifier/notifier.py
# Console-only alert dispatcher.
# No external integrations.

from typing import List

from app.alert import Alert


def send_alerts(endpoint_id: str, alerts: List[Alert]) -> None:
    """
    Print each alert to stdout in the canonical format:

        [ALERT:WARNING]  <endpoint_id> | <message>
        [ALERT:CRITICAL] <endpoint_id> | <message>

    Does nothing if `alerts` is empty.
    """
    for alert in alerts:
        print(f"[ALERT:{alert.severity}] {endpoint_id} | {alert.message}")
