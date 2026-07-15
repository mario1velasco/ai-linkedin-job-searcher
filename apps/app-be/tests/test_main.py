"""Tests for the FastAPI root endpoint."""

import json
from unittest.mock import patch

from fastapi.testclient import TestClient

from app_be.main import app

client = TestClient(app)


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, World!"}


def test_search_linkedin_jobs_writes_file_and_returns_jobs(tmp_path):
    fake_jobs = [{"title": "Frontend Engineer", "company": "Acme"}]
    data_path = tmp_path / "linkedin_data.json"

    with (
        patch(
            "app_be.main.linkedin_service.linkedin_client.search_jobs",
            return_value=fake_jobs,
        ) as mock_search,
        patch("app_be.main.linkedin_service.LINKEDIN_DATA_PATH", data_path),
    ):
        response = client.get("/linkedin/jobs?keywords=Angular")

    assert response.status_code == 200
    assert response.json() == fake_jobs
    mock_search.assert_called_once()
    assert json.loads(data_path.read_text()) == fake_jobs


def test_search_linkedin_jobs_returns_502_on_expired_session():
    with patch(
        "app_be.main.linkedin_service.linkedin_client.search_jobs",
        side_effect=RuntimeError("LinkedIn Voyager API returned 401."),
    ):
        response = client.get("/linkedin/jobs")

    assert response.status_code == 502
