# scripts/seed_data.py
import os
import argparse
from dotenv import load_dotenv
from neo4j import GraphDatabase, basic_auth

# -------------------------
# Connection
# -------------------------
def get_driver():
    """Create a Neo4j driver from environment variables."""
    load_dotenv()
    uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")
    return GraphDatabase.driver(uri, auth=basic_auth(user, password))


# -------------------------
# Schema (constraints/indexes)
# -------------------------
def create_constraints_and_indexes(session):
    """
    Create constraints and indexes for the Wikidata Films KG.

    Important Neo4j 5 note:
    - A UNIQUE constraint creates the underlying index automatically.
    - Do NOT also create an index on the same property, otherwise you get:
      Neo.ClientError.Schema.IndexAlreadyExists
    """
    queries = [
        # Uniqueness constraints (these create indexes implicitly)
        """
        CREATE CONSTRAINT article_wid_unique IF NOT EXISTS
        FOR (a:Article)
        REQUIRE a.wikidata_id IS UNIQUE
        """,
        """
        CREATE CONSTRAINT author_wid_unique IF NOT EXISTS
        FOR (au:Author)
        REQUIRE au.wikidata_id IS UNIQUE
        """,

        # For Topic/Tag, choose ONE strategy:
        # - either unique constraint (recommended), OR separate index.
        # We'll use a unique constraint because topics are strings and should be unique.
        """
        CREATE CONSTRAINT topic_name_unique IF NOT EXISTS
        FOR (t:Topic)
        REQUIRE t.name IS UNIQUE
        """,

        # Useful indexes (on properties not already covered by unique constraints)
        """
        CREATE INDEX article_title_index IF NOT EXISTS
        FOR (a:Article)
        ON (a.title)
        """,
        """
        CREATE INDEX article_year_index IF NOT EXISTS
        FOR (a:Article)
        ON (a.year)
        """,
        """
        CREATE INDEX author_name_index IF NOT EXISTS
        FOR (au:Author)
        ON (au.name)
        """,
    ]

    for q in queries:
        q_clean = q.strip()
        if q_clean:
            session.run(q_clean)

def build_genre_cooccurrence(session, top_k: int = 10, min_shared_films: int = 1):
    """
    Build derived relationships between genres (Topic) based on co-occurrence on the same film.

    Creates:
      (:Topic)-[:CO_OCCURS_WITH {score: <#shared_films>}]->(:Topic)

    - For each genre t1, we keep only the top_k most co-occurring genres t2.
    - min_shared_films filters out weak edges.

    Idempotent: MERGE ensures stable results across runs (but we delete existing CO_OCCURS_WITH first).
    """
    # 1) Optional cleanup to prevent stale edges
    session.run("MATCH (:Topic)-[r:CO_OCCURS_WITH]->(:Topic) DELETE r")

    cypher = """
    MATCH (t1:Topic)<-[:HAS_TOPIC]-(f:Article)-[:HAS_TOPIC]->(t2:Topic)
    WHERE t1 <> t2
    WITH t1, t2, count(DISTINCT f) AS score
    WHERE score >= $min_shared

    // sort pairs for each t1 and keep top_k
    ORDER BY t1.name, score DESC, t2.name
    WITH t1, collect({topic: t2, score: score})[0..$top_k] AS top

    UNWIND top AS row
    WITH t1, row.topic AS t2, row.score AS score

    MERGE (t1)-[r:CO_OCCURS_WITH]->(t2)
    SET r.score = score
    RETURN count(r) AS created
    """

    session.run(cypher, top_k=top_k, min_shared=min_shared_films)



# -------------------------
# Optional reset / cleanup
# -------------------------
def clear_database(session):
    """DEV ONLY: delete everything."""
    session.run("MATCH (n) DETACH DELETE n")


# -------------------------
# Sanity checks / small utilities
# -------------------------
def get_counts(session):
    cypher = """
    CALL { MATCH (a:Article) RETURN count(a) AS articles }
    CALL { MATCH (au:Author) RETURN count(au) AS authors }
    CALL { MATCH (t:Topic) RETURN count(t) AS topics }
    CALL { MATCH (:Author)-[r:DIRECTED]->(:Article) RETURN count(r) AS directed_rels }
    CALL { MATCH (:Article)-[r:HAS_TOPIC]->(:Topic) RETURN count(r) AS topic_rels }
    RETURN articles, authors, topics, directed_rels, topic_rels
    """
    return dict(session.run(cypher).single())


def seed_minimal_demo_data(session):
    """
    OPTIONAL: adds 1-2 demo nodes if DB is empty, so /docs works even before import.
    You can remove this if you want strictly Wikidata only.
    """
    cypher = """
    MERGE (a:Author {wikidata_id: "DEMO_AUTHOR"})
      ON CREATE SET a.name = "Demo Director"
    MERGE (f:Article {wikidata_id: "DEMO_FILM"})
      ON CREATE SET f.title = "Demo Film", f.year = 2000
    MERGE (t:Topic {name: "Demo Genre"})
    MERGE (a)-[:DIRECTED]->(f)
    MERGE (f)-[:HAS_TOPIC]->(t)
    """
    session.run(cypher)


# -------------------------
# Main
# -------------------------
def main():
    """
    New workflow:

    1) make docker-run
    2) make import-wikidata   (imports ~200 films)
    3) make seed              (ONLY creates schema + optional demo if empty)

    By default seed does NOT wipe the database, to avoid deleting imported data.
    Use --reset if you explicitly want to clear everything.
    """
    parser = argparse.ArgumentParser(description="Seed Neo4j schema for Wikidata Films dataset.")
    parser.add_argument("--reset", action="store_true", help="Clear database before applying schema (DANGEROUS)")
    parser.add_argument("--demo-if-empty", action="store_true", help="Insert minimal demo nodes if DB is empty")
    args = parser.parse_args()

    driver = get_driver()
    with driver.session() as session:
        if args.reset:
            print("[Neo4j] RESET enabled: clearing database")
            clear_database(session)

        print("[Neo4j] Creating constraints and indexes...")
        create_constraints_and_indexes(session)

        counts = get_counts(session)
        print(f"[Neo4j] Current counts: {counts}")

        print("[Neo4j] Building CO_OCCURS_WITH relationships between genres...")
        build_genre_cooccurrence(session, top_k=10, min_shared_films=2)



        if args.demo_if_empty and counts["articles"] == 0:
            print("[Neo4j] DB empty -> inserting minimal demo data")
            seed_minimal_demo_data(session)
            counts = get_counts(session)
            print(f"[Neo4j] Counts after demo seed: {counts}")

    driver.close()
    print("[Neo4j] Seed finished.")


if __name__ == "__main__":
    main()