# tests/test_authors.py
import os
from neo4j import GraphDatabase
from starlette.testclient import TestClient
from app.main import app

client = TestClient(app)


def _get_any_director_id() -> str:
    uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")

    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        rec = session.run(
            """
            MATCH (d:Author)-[:DIRECTED]->(:Article)
            RETURN d.wikidata_id AS id
            LIMIT 1
            """
        ).single()
        assert rec is not None and rec["id"]
        director_id = rec["id"]
    driver.close()
    return director_id


def test_director_contributions_returns_data():
    director_id = _get_any_director_id()

    response = client.get(f"/api/authors/{director_id}/contributions", params={"limit": 50})
    assert response.status_code == 200

    data = response.json()

    assert "director" in data
    assert data["director"]["wikidata_id"] == director_id
    assert "name" in data["director"] and data["director"]["name"]

    assert "films" in data and isinstance(data["films"], list)
    assert "genres" in data and isinstance(data["genres"], list)

    # Should have at least 1 film (because we picked a director with DIRECTED rel)
    assert len(data["films"]) >= 1

    # Contract for films
    f0 = data["films"][0]
    assert "wikidata_id" in f0 and f0["wikidata_id"]
    assert "title" in f0 and f0["title"]


def test_director_contributions_unknown_director_404():
    response = client.get("/api/authors/Q_DOES_NOT_EXIST/contributions")
    assert response.status_code == 404
