"""FastAPI application entrypoint."""

import json
from pathlib import Path

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app_be import linkedin_jobs

app = FastAPI()
app.state.linkedin_access_token = None

CALLBACK_DATA_PATH = Path(__file__).resolve().parent / "callback_data.yaml"
LINKEDIN_DATA_PATH = Path(__file__).resolve().parent / "data" / "linkedin_data.json"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    # allow_methods=["GET", "POST"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Hello, World!"}


@app.get("/greetings/{name}")
def read_greetings(name: str):
    return {"message": f"Hello, {name}!"}


@app.get("/callback")
def callback(code: str, state: str):
    """Handle the OAuth callback and exchange the code for an access token."""
    app.state.linkedin_access_token = linkedin_jobs.callback(code, state)
    return {"message": "Callback received. You can close this window."}


@app.get("/linkedin/login")
def linkedin_login():
    """Initiate the LinkedIn OAuth flow and retrieve an access token."""
    linkedin_jobs.linkedln_login()
    return {"message": "LinkedIn login initiated. Please check your browser."}


@app.get("/linkedin/userinfo")
def get_linkedin_userinfo():
    if not app.state.linkedin_access_token:
        raise HTTPException(status_code=401, detail="Not authenticated with LinkedIn.")
    response = requests.get(
        "https://api.linkedin.com/v2/userinfo",
        headers={"Authorization": f"Bearer {app.state.linkedin_access_token}"},
    )
    return response.json()


@app.get("/linkedin/jobs")
def search_linkedin_jobs(
    keywords: str = "Angular",
    geo_id: str = "105646813",
    distance: float = 0.0,
    hours: int = 24,
    remote: bool = True,
    salary_bucket: str | None = None,
):
    try:
        jobs = linkedin_jobs.search_jobs(
            keywords=keywords,
            geo_id=geo_id,
            distance=distance,
            hours=hours,
            remote=remote,
            salary_bucket=salary_bucket,
        )
    except RuntimeError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error

    LINKEDIN_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LINKEDIN_DATA_PATH, "w") as file:
        json.dump(jobs, file, indent=2)

    return jobs
