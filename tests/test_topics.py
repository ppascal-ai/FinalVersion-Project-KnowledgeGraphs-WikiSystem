# tests/test_topics.py

import os
from neo4j import GraphDatabase
from starlette.testclient import TestClient
from app.main import app

client = TestClient(app)


def _get_any_genre_name() -> str:
    uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")

    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        rec = session.run("MATCH (t:Topic) RETURN t.name AS name LIMIT 1").single()
        assert rec is not None and rec["name"]
        name = rec["name"]
    driver.close()
    return name


def test_topics_graph_returns_data():
    topic = _get_any_genre_name()
    response = client.get(f"/api/topics/{topic}/graph", params={"depth": 1, "limit": 10})
    assert response.status_code == 200

    data = response.json()
    assert "topic" in data and data["topic"]["name"] == topic
    assert "films" in data and isinstance(data["films"], list)
    assert "directors" in data and isinstance(data["directors"], list)
    assert "related_topics" in data and isinstance(data["related_topics"], list)

    # contrat minimal pour films si présents
    if len(data["films"]) > 0:
        f0 = data["films"][0]
        assert "wikidata_id" in f0 and f0["wikidata_id"]
        assert "title" in f0 and f0["title"]
