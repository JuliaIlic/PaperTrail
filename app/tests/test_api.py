from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from botocore.exceptions import ClientError
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

SAMPLE_RESULTS = [
    {
        "title": "Docker in Practice",
        "authors": ["Jane Doe"],
        "year": 2020,
        "citations": 42,
        "doi": "https://doi.org/10.1234/example",
    }
]


def dynamodb_error(operation: str) -> ClientError:
    return ClientError(
        {"Error": {"Code": "InternalServerError", "Message": "DynamoDB is down"}},
        operation,
    )


@pytest.fixture
def mock_search(monkeypatch):
    mock = AsyncMock(return_value=SAMPLE_RESULTS)
    monkeypatch.setattr("app.main.search_works", mock)
    return mock


@pytest.fixture
def mock_save(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr("app.main.save_search", mock)
    return mock

def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_search_without_query_returns_400():
    response = client.get("/search")
    assert response.status_code == 400


def test_search_with_too_long_query_returns_400():
    response = client.get("/search", params={"q": "a" * 201})
    assert response.status_code == 400


@pytest.mark.parametrize("limit", [0, 51])
def test_search_with_invalid_limit_returns_400(limit):
    response = client.get("/search", params={"q": "docker", "limit": limit})
    assert response.status_code == 400

def test_search_returns_results_and_saves_history(mock_search, mock_save):
    response = client.get("/search", params={"q": "  docker  ", "limit": 5})

    assert response.status_code == 200
    body = response.json()
    assert body["query"] == "docker"
    assert body["count"] == 1
    assert body["results"][0]["title"] == "Docker in Practice"
    mock_search.assert_awaited_once_with("docker", 5)
    mock_save.assert_called_once_with("docker", 1)


def test_search_returns_503_when_openalex_times_out(monkeypatch, mock_save):
    monkeypatch.setattr(
        "app.main.search_works",
        AsyncMock(side_effect=httpx.TimeoutException("timeout")),
    )
    response = client.get("/search", params={"q": "docker"})

    assert response.status_code == 503
    mock_save.assert_not_called()


def test_search_still_works_when_history_save_fails(mock_search, monkeypatch):
    monkeypatch.setattr(
        "app.main.save_search", MagicMock(side_effect=dynamodb_error("PutItem"))
    )
    response = client.get("/search", params={"q": "docker"})

    assert response.status_code == 200
    assert response.json()["count"] == 1

def test_history_returns_items(monkeypatch):
    items = [{"query": "docker", "created_at": "2026-10-07T12:00:00+00:00", "result_count": 10}]
    monkeypatch.setattr("app.main.get_history", MagicMock(return_value=items))

    response = client.get("/history")

    assert response.status_code == 200
    assert response.json() == {"count": 1, "items": items}


def test_history_returns_503_when_dynamodb_fails(monkeypatch):
    monkeypatch.setattr(
        "app.main.get_history", MagicMock(side_effect=dynamodb_error("Query"))
    )
    response = client.get("/history")
    assert response.status_code == 503