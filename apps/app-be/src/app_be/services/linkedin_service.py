"""Business logic for the LinkedIn integration.

Orchestrates the LinkedIn OAuth flow and job search on top of
`api_clients.linkedin_client`, and owns LinkedIn-specific rules such as
persisting job search results to disk.
"""

from __future__ import annotations

import json
from pathlib import Path

from app_be.api_clients import linkedin_client
from app_be.utils.logger import get_logger

logger = get_logger(__name__)

LINKEDIN_DATA_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "linkedin_data.json"
)


def login() -> None:
    """Kick off the LinkedIn OAuth flow by opening the authorization URL."""
    linkedin_client.linkedln_login()


def handle_oauth_callback(code: str, state: str) -> str:
    """Exchange the OAuth callback code for an access token."""
    return linkedin_client.callback(code, state)


def get_userinfo(access_token: str) -> dict:
    """Fetch the authenticated user's LinkedIn profile info."""
    return linkedin_client.get_userinfo(access_token)


def search_jobs(
    keywords: str,
    geo_id: str,
    distance: float,
    hours: int,
    remote: bool,
    salary_bucket: str | None = None,
) -> list[dict]:
    """Search LinkedIn jobs and persist the results to disk."""
    jobs = linkedin_client.search_jobs(
        keywords=keywords,
        geo_id=geo_id,
        distance=distance,
        hours=hours,
        remote=remote,
        salary_bucket=salary_bucket,
    )
    logger.info("Found %d LinkedIn jobs", len(jobs))

    LINKEDIN_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LINKEDIN_DATA_PATH, "w") as file:
        json.dump(jobs, file, indent=2)
    logger.debug("Wrote LinkedIn job results to %s", LINKEDIN_DATA_PATH)

    return jobs
