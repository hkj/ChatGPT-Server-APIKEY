import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from starlette.requests import Request
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from oauthlib.oauth2 import OAuth2Error

from dotenv import load_dotenv
from database import generate_and_store_api_key

load_dotenv()

app = FastAPI()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"


@app.get("/login")
def login(request: Request):
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [REDIRECT_URI],
                "userinfo_uri": "https://openidconnect.googleapis.com/v1/userinfo",
            }
        },
        scopes=["openid", "email", "profile"],
    )
    flow.redirect_uri = REDIRECT_URI
    authorization_url, _ = flow.authorization_url(prompt="consent")

    return RedirectResponse(url=authorization_url)


@app.get("/callback")
def callback(request: Request, code: str):
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [REDIRECT_URI],
                "userinfo_uri": "https://openidconnect.googleapis.com/v1/userinfo",
            }
        },
        scopes=["openid", "email", "profile"],
    )
    flow.redirect_uri = REDIRECT_URI

    try:
        flow.fetch_token(code=code)

    except OAuth2Error as e:
        raise HTTPException(status_code=400, detail=f"OAuth2 error:{str(e)}")

    credentials = flow.credentials

    try:
        # Build the Google API client
        service = build("oauth2", "v2", credentials=credentials)

        # Get the user's email
        userinfo = service.userinfo().get().execute()
        email = userinfo["email"]

    except HttpError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # メールアドレスに対してAPI KEYを発行
    api_key = generate_and_store_api_key(email)

    return {"email": email, "api_key": api_key}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
