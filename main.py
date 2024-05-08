import os
from typing import Optional

import httpx
import redis
from celery import Celery
from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
    Request,
    Cookie,
)
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.responses import JSONResponse

from auth import router as auth_router
from config import (
    REDIS_URL,
    GITHUB_USER_URL,
)
from utils import generate_data

app = FastAPI()
app.include_router(auth_router)

websocket_clients = set()

celery = Celery(
    "tasks",
    backend=REDIS_URL,
    broker=REDIS_URL,
)

redis_client = redis.Redis.from_url(REDIS_URL)

templates = Jinja2Templates(directory="templates")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    websocket_clients.add(websocket)
    try:
        while True:
            await websocket.send_text(get_data())
    except WebSocketDisconnect:
        websocket_clients.remove(websocket)


@app.get("/", response_class=HTMLResponse)
async def fetch_data(request: Request, access_token: Optional[str] = Cookie(None)):
    if access_token:
        headers = {"Authorization": f"token {access_token}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(GITHUB_USER_URL, headers=headers)
            if response.status_code != 200:
                return JSONResponse(status_code=401, content={"error": "Invalid token"})
    return templates.TemplateResponse(
        "data.html",
        {
            "request": request,
            "data": get_data(),
            "access_token": access_token,
        },
    )


def get_data():
    return redis_client.get("data").decode("utf-8")


@celery.task
def set_data():
    redis_client.set("data", generate_data(16))


celery.conf.beat_schedule = {
    "generate_data": {
        "task": "main.set_data",
        "schedule": 5.0,
    }
}
