# tests/test_cypher_queries.py

import os
from neo4j import GraphDatabase


def test_wikidata_graph_has_directed_and_topics():
    """
    Cypher test (graph-native):
    - at least one DIRECTED relationship
    - at least one HAS_TOPIC relationship
    - Articles have wikidata_id
    """
    uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")

    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        rec = session.run(
            """
            CALL { MATCH (:Author)-[r:DIRECTED]->(:Article) RETURN count(r) AS directed_cnt }
            CALL { MATCH (:Article)-[r:HAS_TOPIC]->(:Topic) RETURN count(r) AS topic_cnt }
            CALL { MATCH (f:Article) WHERE f.wikidata_id IS NOT NULL RETURN count(f) AS film_cnt }
            RETURN directed_cnt, topic_cnt, film_cnt
            """
        ).single()

        assert rec is not None
        assert rec["film_cnt"] > 0
        assert rec["directed_cnt"] > 0
        assert rec["topic_cnt"] > 0

    driver.close()