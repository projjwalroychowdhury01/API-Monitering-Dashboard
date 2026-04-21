from __future__ import annotations

import json
from typing import Any

import redis


class EventBus:
    def __init__(self, host: str, port: int, db: int = 0, channel: str = "platform.events") -> None:
        self._client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
        self.channel = channel

    def publish(self, event_type: str, payload: dict[str, Any]) -> None:
        message = {"event_type": event_type, "payload": payload}
        self._client.publish(self.channel, json.dumps(message, default=str))

    def subscribe(self):
        pubsub = self._client.pubsub()
        pubsub.subscribe(self.channel)
        return pubsub
