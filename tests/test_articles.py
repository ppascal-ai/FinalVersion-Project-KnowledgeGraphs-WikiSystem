# tests/test_articles.py
import os
from neo4j import GraphDatabase
from starlette.testclient import TestClient
from app.main import app

client = TestClient(app)


def _get_any_film_id() -> str:
    uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")

    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        rec = session.run(
            "MATCH (f:Article) RETURN f.wikidata_id AS id LIMIT 1"
        ).single()
        assert rec is not None and rec["id"]
        film_id = rec["id"]
    driver.close()
    return film_id


def test_related_films_for_existing_film():
    film_id = _get_any_film_id()
    api_key = os.getenv("API_KEY")
    assert api_key, "API_KEY must be set in the environment to run this test"

    headers = {"X-API-Key": api_key}

    response = client.get(f"/api/articles/{film_id}/related", params={"limit": 10}, headers=headers)
    assert response.status_code == 200

    payload = response.json()
    assert payload["film_id"] == film_id
    assert "related" in payload
    assert isinstance(payload["related"], list)

    if len(payload["related"]) > 0:
        first = payload["related"][0]
        assert "film" in first and "score" in first
        assert "wikidata_id" in first["film"] and first["film"]["wikidata_id"]
        assert "title" in first["film"] and first["film"]["title"]


def test_related_films_for_unknown_film_returns_404():
    api_key = os.getenv("API_KEY")
    assert api_key, "API_KEY must be set in the environment to run this test"
    headers = {"X-API-Key": api_key}

    response = client.get("/api/articles/Q_DOES_NOT_EXIST/related", headers=headers)
    assert response.status_code == 404


def test_related_films_without_key_returns_401():
    film_id = _get_any_film_id()
    response = client.get(f"/api/articles/{film_id}/related")
    assert response.status_code == 401


def test_related_films_with_wrong_key_returns_401():
    film_id = _get_any_film_id()
    response = client.get(f"/api/articles/{film_id}/related", headers={"X-API-Key": "wrong_key"})
    assert response.status_code == 401


def test_related_films_with_valid_key_returns_200():
    api_key = os.getenv("API_KEY")
    assert api_key, "API_KEY must be set in the environment to run this test"
    film_id = _get_any_film_id()
    response = client.get(f"/api/articles/{film_id}/related", headers={"X-API-Key": api_key})
    assert response.status_code == 200
