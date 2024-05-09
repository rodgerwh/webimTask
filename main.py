from asyncio import sleep
from random import randint
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
from starlette.responses import RedirectResponse

from auth import router as auth_router
from config import settings
from utils import generate_data

app = FastAPI()
app.include_router(auth_router)

websocket_clients = set()
templates = Jinja2Templates(directory="templates")
redis_client = redis.Redis.from_url(settings.REDIS_URL)
celery = Celery(
    "tasks",
    backend=settings.REDIS_URL,
    broker=settings.REDIS_URL,
)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    websocket_clients.add(websocket)
    try:
        while True:
            data = get_data()
            if data:
                await websocket.send_text(data)
            await sleep(5)
    except WebSocketDisconnect:
        websocket_clients.remove(websocket)


@app.get("/", response_class=HTMLResponse, name="fetch_data")
async def fetch_data(request: Request, access_token: Optional[str] = Cookie(None)):
    if access_token:
        headers = {"Authorization": f"token {access_token}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(settings.GITHUB_USER_URL, headers=headers)
            if response.status_code != 200:
                response = RedirectResponse(url=app.url_path_for("fetch_data"))
                response.delete_cookie(key="access_token")
                return response

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
    redis_client.set("data", generate_data(randint(1, 500)))


celery.conf.beat_schedule = {
    "generate_data": {
        "task": "main.set_data",
        "schedule": 5.0,
    }
}
