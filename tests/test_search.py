# tests/test_search.py
import os
from neo4j import GraphDatabase
from starlette.testclient import TestClient
from app.main import app

client = TestClient(app)


def _get_any_title_fragment() -> str:
    uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")

    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        rec = session.run("MATCH (f:Article) WHERE f.title IS NOT NULL RETURN f.title AS t LIMIT 1").single()
        assert rec is not None and rec["t"]
        title = rec["t"]
    driver.close()

    # fragment pour éviter soucis d’espaces / titres trop courts
    frag = title.strip().split(" ")[0]
    return frag[:6] if len(frag) >= 3 else title[:6]



def test_search_returns_results():
    q = _get_any_title_fragment()
    response = client.get("/api/search", params={"q": q, "limit": 5})
    assert response.status_code == 200

    data = response.json()
    assert "results" in data
    assert isinstance(data["results"], list)
    assert len(data["results"]) >= 1

    # Vérifie le contrat minimum du dataset Wikidata
    first = data["results"][0]
    assert "wikidata_id" in first and first["wikidata_id"]
    assert "title" in first and first["title"]