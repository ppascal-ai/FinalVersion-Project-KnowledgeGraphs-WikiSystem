# tests/test_graph_queries.py

import os
from neo4j import GraphDatabase


def test_related_films_exist_by_shared_director_or_genre():
    """
    Graph query test (Wikidata Films KG):

    Ensures there exists at least one pair of films that are related by:
    - sharing a director, OR
    - sharing a genre (Topic)

    This replaces the old RELATED_ARTICLE-based test from the previous dataset.
    """
    uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")

    driver = GraphDatabase.driver(uri, auth=(user, password))

    with driver.session() as session:
        rec = session.run(
            """
            CALL {
              // shared director
              MATCH (d:Author)-[:DIRECTED]->(f1:Article)
              MATCH (d)-[:DIRECTED]->(f2:Article)
              WHERE f1 <> f2
              RETURN 1 AS ok
              LIMIT 1
              UNION
              // shared genre
              MATCH (f1:Article)-[:HAS_TOPIC]->(t:Topic)
              MATCH (f2:Article)-[:HAS_TOPIC]->(t)
              WHERE f1 <> f2
              RETURN 1 AS ok
              LIMIT 1
            }
            RETURN count(ok) AS related_pairs_found
            """
        ).single()

        assert rec is not None
        assert rec["related_pairs_found"] > 0

    driver.close()
