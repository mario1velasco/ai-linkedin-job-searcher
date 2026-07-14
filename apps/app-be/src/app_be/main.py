"""FastAPI application entrypoint."""

import json
from pathlib import Path

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app_be.api_clients import linkedin_jobs
from app_be.utils.logger import get_logger, setup_logging

CALLBACK_DATA_PATH = Path(__file__).resolve().parent / "callback_data.yaml"
LINKEDIN_DATA_PATH = Path(__file__).resolve().parent / "data" / "linkedin_data.json"

setup_logging()
logger = get_logger(__name__)

app = FastAPI()
app.state.linkedin_access_token = None

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
    logger.info("Received OAuth callback (state=%s)", state)
    try:
        app.state.linkedin_access_token = linkedin_jobs.callback(code, state)
    except ValueError:
        logger.warning("OAuth callback rejected: state mismatch (state=%s)", state)
        raise
    except requests.HTTPError:
        logger.exception("Failed to exchange OAuth code for an access token")
        raise
    logger.info("LinkedIn access token acquired successfully")
    return {"message": "Callback received. You can close this window."}


@app.get("/linkedin/login")
def linkedin_login():
    """Initiate the LinkedIn OAuth flow and retrieve an access token."""
    logger.info("Initiating LinkedIn OAuth login flow")
    linkedin_jobs.linkedln_login()
    return {"message": "LinkedIn login initiated. Please check your browser."}


@app.get("/linkedin/userinfo")
def get_linkedin_userinfo():
    if not app.state.linkedin_access_token:
        logger.warning("Userinfo requested but no LinkedIn access token is set")
        raise HTTPException(status_code=401, detail="Not authenticated with LinkedIn.")
    response = requests.get(
        "https://api.linkedin.com/v2/userinfo",
        headers={"Authorization": f"Bearer {app.state.linkedin_access_token}"},
    )
    if not response.ok:
        logger.error(
            "LinkedIn userinfo request failed with status %s", response.status_code
        )
    else:
        logger.info("Fetched LinkedIn userinfo successfully")
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
        logger.error("LinkedIn job search failed: %s", error)
        raise HTTPException(status_code=502, detail=str(error)) from error

    logger.info("Found %d LinkedIn jobs", len(jobs))

    LINKEDIN_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LINKEDIN_DATA_PATH, "w") as file:
        json.dump(jobs, file, indent=2)
    logger.debug("Wrote LinkedIn job results to %s", LINKEDIN_DATA_PATH)

    return jobs
