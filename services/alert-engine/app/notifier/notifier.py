# notifier/notifier.py
# Console-only alert dispatcher.
# No external integrations.

from typing import List


def send_alerts(endpoint_id: str, alerts: List[str]) -> None:
    """
    Print each alert to stdout in the canonical format:

        [ALERT] <endpoint_id> | <message>

    Does nothing if `alerts` is empty.
    """
    for message in alerts:
        print(f"[ALERT] {endpoint_id} | {message}")
