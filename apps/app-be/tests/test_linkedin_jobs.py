from unittest.mock import patch

import pytest

from app_be.linkedin_jobs import _build_query, _flatten_job_cards, _get_linkedin_cookies


def test_build_query_basic():
    query = _build_query(
        keywords="Angular",
        geo_id="105646813",
        distance=0.0,
        hours=24,
        remote=True,
        salary_bucket=None,
    )

    assert "keywords:Angular" in query
    assert "locationUnion:(geoId:105646813)" in query
    assert "distance:List(0.0)" in query
    assert "timePostedRange:List(r86400)" in query
    assert "workplaceType:List(2)" in query
    assert "salaryBucketV2" not in query


def test_build_query_not_remote_omits_workplace_type():
    query = _build_query(
        keywords="Angular",
        geo_id="105646813",
        distance=0.0,
        hours=24,
        remote=False,
        salary_bucket=None,
    )

    assert "workplaceType" not in query


def test_build_query_with_salary_bucket():
    query = _build_query(
        keywords="Angular",
        geo_id="105646813",
        distance=0.0,
        hours=24,
        remote=True,
        salary_bucket="f_SA_id_225001%3A272001",
    )

    assert "salaryBucketV2:List(f_SA_id_225001%3A272001)" in query


def test_flatten_job_cards():
    payload = {
        "included": [
            {
                "$type": "com.linkedin.voyager.dash.jobs.JobPosting",
                "entityUrn": "urn:li:fsd_jobPosting:123",
                "jobPostingId": "123",
                "title": "Frontend Engineer (Angular)",
                "formattedLocation": "Remote",
                "listedAt": 1730000000000,
                "companyDetails": {"company": "urn:li:fsd_company:456"},
            },
            {
                "$type": "com.linkedin.voyager.dash.organization.Company",
                "entityUrn": "urn:li:fsd_company:456",
                "name": "Acme Corp",
            },
        ]
    }

    jobs = _flatten_job_cards(payload)

    assert jobs == [
        {
            "title": "Frontend Engineer (Angular)",
            "company": "Acme Corp",
            "location": "Remote",
            "posted_at": 1730000000000,
            "job_url": "https://www.linkedin.com/jobs/view/123",
        }
    ]


def test_flatten_job_cards_ignores_non_job_entities():
    payload = {
        "included": [{"$type": "com.linkedin.voyager.dash.organization.Company"}]
    }

    assert _flatten_job_cards(payload) == []


class _FakeCookie:
    def __init__(self, name, value):
        self.name = name
        self.value = value


def test_get_linkedin_cookies_prefers_local_browser():
    fake_jar = [
        _FakeCookie("li_at", "browser-li-at"),
        _FakeCookie("JSESSIONID", "browser-jsession"),
    ]

    with patch("app_be.linkedin_jobs.browser_cookie3.load", return_value=fake_jar):
        assert _get_linkedin_cookies() == ("browser-li-at", "browser-jsession")


def test_get_linkedin_cookies_falls_back_to_env(monkeypatch):
    monkeypatch.setenv("LI_AT_COOKIE", "env-li-at")
    monkeypatch.setenv("JSESSIONID", "env-jsession")

    with patch(
        "app_be.linkedin_jobs.browser_cookie3.load",
        side_effect=RuntimeError("no browser"),
    ):
        assert _get_linkedin_cookies() == ("env-li-at", "env-jsession")


def test_get_linkedin_cookies_raises_when_nothing_available(monkeypatch):
    monkeypatch.delenv("LI_AT_COOKIE", raising=False)
    monkeypatch.delenv("JSESSIONID", raising=False)

    with patch(
        "app_be.linkedin_jobs.browser_cookie3.load",
        side_effect=RuntimeError("no browser"),
    ), pytest.raises(RuntimeError):
        _get_linkedin_cookies()
