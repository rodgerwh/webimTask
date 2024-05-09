from typing import Optional
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter
from starlette.responses import RedirectResponse

from config import settings

router = APIRouter()


@router.get("/login")
async def login():
    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
    }
    github_auth_url = f"{settings.GITHUB_AUTHORIZE_URL}?{urlencode(params)}"
    return RedirectResponse(url=github_auth_url)


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie(key="access_token")
    return response


@router.get("/callback")
async def callback(code: Optional[str] = None, error: Optional[str] = None):
    if error:
        return RedirectResponse(url="/")

    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "client_secret": settings.GITHUB_CLIENT_SECRET,
        "code": code,
    }
    headers = {"Accept": "application/json"}
    async with httpx.AsyncClient() as client:
        response_oauth = await client.post(
            url=settings.GITHUB_TOKEN_URL,
            params=params,
            headers=headers,
        )

    response_json = response_oauth.json()
    if "access_token" not in response_json:
        return RedirectResponse(url="/")
    access_token = response_json["access_token"]

    response = RedirectResponse(url="/")
    response.set_cookie(
        key="access_token", value=access_token, httponly=True, secure=True
    )

    return response
