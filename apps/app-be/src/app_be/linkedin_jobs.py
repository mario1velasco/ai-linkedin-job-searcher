"""Client for LinkedIn's internal (undocumented) "Voyager" API.

LinkedIn has no public job-search API for regular OAuth apps - the OAuth flow
in oauth_linkdln.py only grants identity scopes (openid profile email). This
module instead authenticates with the user's own logged-in browser session
(the `li_at` / `JSESSIONID` cookies) and calls the same internal endpoint
LinkedIn's own web app uses. The endpoint path, params, and response shape are
undocumented, reverse-engineered, and may change or need adjustment once
tested against a real response.
"""

from __future__ import annotations

import os
import secrets
import webbrowser
from pathlib import Path
from urllib.parse import urlencode

import browser_cookie3
import requests
import yaml

CALLBACK_DATA_PATH = Path(__file__).resolve().parent / "callback_data.yaml"
VOYAGER_JOB_CARDS_URL = "https://www.linkedin.com/voyager/api/voyagerJobsDashJobCards"
DECORATION_ID = (
    "com.linkedin.voyager.dash.deco.jobs.search.JobSearchCardsCollection-208"
)
STATE = secrets.token_urlsafe()


def linkedln_login():
    """Initiate the LinkedIn OAuth flow and retrieve an access token."""

    params = {
        "response_type": "code",
        "client_id": os.environ["CLIENT_ID"],
        "redirect_uri": os.environ["REDIRECT_URI"],
        "state": STATE,
        "scope": "openid profile email",
    }

    url = f"https://www.linkedin.com/oauth/v2/authorization?{urlencode(params)}"

    webbrowser.open(url)


def callback(code: str, state: str) -> str:
    """Handle the OAuth callback and exchange the code for an access token."""
    if state != STATE:
        raise ValueError("State does not match! Possible CSRF attack.")
    with open(CALLBACK_DATA_PATH, "w") as file:
        yaml.dump({"code": code, "state": state}, file)
    params = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": os.environ["CLIENT_ID"],
        "client_secret": os.environ["CLIENT_SECRET"],
        "redirect_uri": os.environ["REDIRECT_URI"],
    }

    response = requests.post(
        "https://www.linkedin.com/oauth/v2/accessToken", data=params
    )

    response.raise_for_status()

    return response.json()["access_token"]


def search_jobs(
    keywords: str,
    geo_id: str,
    distance: float,
    hours: int,
    remote: bool,
    salary_bucket: str | None = None,
    count: int = 25,
) -> list[dict]:
    session = _build_session()
    query = _build_query(keywords, geo_id, distance, hours, remote, salary_bucket)

    response = session.get(
        VOYAGER_JOB_CARDS_URL,
        params={
            "decorationId": DECORATION_ID,
            "count": count,
            "q": "jobSearch",
            "query": query,
            "start": 0,
        },
        timeout=15,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"LinkedIn Voyager API returned {response.status_code}. "
            "The li_at/JSESSIONID session cookies have likely expired - "
            "log into linkedin.com in a browser and refresh them in .env."
        )

    return _flatten_job_cards(response.json())


# * PRIVATE HELPERS
def _get_linkedin_cookies() -> tuple[str, str]:
    """Get the li_at/JSESSIONID cookies, preferring the local browser session.

    Since this server runs on the same machine as the browser you're logged
    into linkedin.com with, we can read the cookies straight out of the
    browser's cookie store instead of asking you to copy them by hand. Falls
    back to LI_AT_COOKIE/JSESSIONID in .env if that fails (e.g. no local
    browser profile, or running somewhere other than your own machine).
    """
    try:
        cookie_jar = browser_cookie3.load(domain_name="linkedin.com")
        cookies = {cookie.name: cookie.value for cookie in cookie_jar}
        li_at = cookies.get("li_at")
        jsessionid = cookies.get("JSESSIONID")
        if li_at and jsessionid:
            return li_at, jsessionid
    except Exception:  # noqa: BLE001 - browser access is inherently unreliable
        pass

    try:
        return os.environ["LI_AT_COOKIE"], os.environ["JSESSIONID"]
    except KeyError as error:
        raise RuntimeError(
            "Could not find LinkedIn session cookies in your local browser, "
            "and LI_AT_COOKIE/JSESSIONID are not set in .env either. Log "
            "into linkedin.com in a supported browser (Chrome/Firefox/Edge), "
            "or set both env vars manually."
        ) from error


def _build_session() -> requests.Session:
    """Build a requests.Session with the LinkedIn cookies and headers."""
    li_at, jsessionid = _get_linkedin_cookies()

    session = requests.Session()
    session.cookies.set("li_at", li_at, domain=".linkedin.com")
    session.cookies.set("JSESSIONID", jsessionid, domain=".linkedin.com")
    session.headers.update(
        {
            # Voyager's CSRF check requires this header to equal the JSESSIONID
            # cookie value (unquoted) - a long-standing LinkedIn quirk.
            "csrf-token": jsessionid.strip('"'),
            "x-restli-protocol-version": "2.0.0",
            "x-li-lang": "en_US",
            "accept": "application/json",
            "user-agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
        }
    )
    return session


def _build_query(
    keywords: str,
    geo_id: str,
    distance: float,
    hours: int,
    remote: bool,
    salary_bucket: str | None,
) -> str:
    """Build the query string for the LinkedIn Voyager API."""
    filters = [f"distance:List({distance})", f"timePostedRange:List(r{hours * 3600})"]
    if remote:
        filters.append("workplaceType:List(2)")
    if salary_bucket:
        filters.append(f"salaryBucketV2:List({salary_bucket})")

    return (
        "(origin:JOB_SEARCH_PAGE_QUERY_EXPANSION,"
        f"keywords:{keywords},"
        f"locationUnion:(geoId:{geo_id}),"
        f"selectedFilters:({','.join(filters)}),"
        "spellCorrectionEnabled:true)"
    )


def _flatten_job_cards(payload: dict) -> list[dict]:
    """Flatten the LinkedIn Voyager API response into a list of job dicts."""
    included = payload.get("included", [])
    entities_by_urn = {entity.get("entityUrn"): entity for entity in included}

    jobs = []
    for entity in included:
        if entity.get("$type") != "com.linkedin.voyager.dash.jobs.JobPosting":
            continue

        company_urn = (entity.get("companyDetails") or {}).get("company")
        company = entities_by_urn.get(company_urn, {})
        job_posting_id = entity.get("jobPostingId", "")

        jobs.append(
            {
                "title": entity.get("title"),
                "company": company.get("name"),
                "location": entity.get("formattedLocation"),
                "posted_at": entity.get("listedAt"),
                "job_url": f"https://www.linkedin.com/jobs/view/{job_posting_id}",
            }
        )
    return jobs
