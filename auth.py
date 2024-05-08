from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, APIRouter
from starlette.responses import RedirectResponse

from config import (
    GITHUB_CLIENT_ID,
    GITHUB_AUTHORIZE_URL,
    GITHUB_CLIENT_SECRET,
    GITHUB_TOKEN_URL,
)
router = APIRouter()


@router.get("/login")
async def login():
    params = {
        "client_id": GITHUB_CLIENT_ID,
    }
    github_auth_url = f"{GITHUB_AUTHORIZE_URL}?{urlencode(params)}"
    return RedirectResponse(url=github_auth_url)


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie(key="access_token")
    return response


@router.get("/callback")
async def callback(code):
    params = {
        "client_id": GITHUB_CLIENT_ID,
        "client_secret": GITHUB_CLIENT_SECRET,
        "code": code,
    }
    headers = {"Accept": "application/json"}
    async with httpx.AsyncClient() as client:
        response_oauth = await client.post(
            url=GITHUB_TOKEN_URL, params=params, headers=headers
        )
    response_json = response_oauth.json()
    if "access_token" not in response_json:
        raise HTTPException(status_code=400, detail="Failed to authorize.")
    access_token = response_json["access_token"]
    response = RedirectResponse(url="/")
    response.set_cookie(
        key="access_token", value=access_token, httponly=True, secure=True
    )
    return response
