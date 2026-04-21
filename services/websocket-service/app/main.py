import asyncio
import json
import os
import sys

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../shared_libraries/python")))

from platform_lib.realtime import EventBus

from app.config import settings
from app.logger import logger
from app.routes import health


event_bus = EventBus(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    channel=settings.REDIS_CHANNEL_PLATFORM_EVENTS,
)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.SERVICE_NAME.replace("-", " ").title(),
        description="Realtime event bridge for alerts and incident updates.",
        version="0.2.0",
        debug=settings.DEBUG,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)

    @app.websocket("/ws/events/{tenant_id}")
    async def websocket_events(websocket: WebSocket, tenant_id: str):
        await websocket.accept()
        pubsub = event_bus.subscribe()
        try:
            while True:
                message = pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message.get("type") == "message":
                    body = json.loads(message["data"])
                    org_id = body.get("payload", {}).get("org_id")
                    if tenant_id == "*" or tenant_id == org_id:
                        await websocket.send_json(body)
                await asyncio.sleep(0.2)
        except WebSocketDisconnect:
            logger.info(f"WebSocket client for tenant {tenant_id} disconnected.")
        finally:
            pubsub.close()

    return app


app = create_app()
