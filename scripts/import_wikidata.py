#scripts/import_wikidata.py
import os
import requests
from neo4j import GraphDatabase

WQS_URL = "https://query.wikidata.org/sparql"

SPARQL_QUERY = """
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX bd: <http://www.bigdata.com/rdf#>

SELECT ?film ?filmLabel ?director ?directorLabel ?genreLabel ?pubDate WHERE {
  ?film wdt:P31 wd:Q11424 .
  ?film wdt:P57 ?director .
  OPTIONAL { ?film wdt:P136 ?genre . }
  OPTIONAL { ?film wdt:P577 ?pubDate . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
LIMIT 200
"""

def fetch_wikidata(query: str) -> list[dict]:
    headers = {
        "Accept": "application/sparql-results+json",
        "User-Agent": "KG-WikiSystem/1.0 (student project)"
    }
    r = requests.get(WQS_URL, params={"query": query}, headers=headers, timeout=60)
    r.raise_for_status()
    data = r.json()
    return data["results"]["bindings"]

def qid(uri: str) -> str:
    # ex: http://www.wikidata.org/entity/Q42 -> Q42
    return uri.rsplit("/", 1)[-1]

def year_from_date(date_str: str | None) -> int | None:
    if not date_str:
        return None
    # iso format: "1999-10-15T00:00:00Z"
    try:
        return int(date_str[:4])
    except Exception:
        return None

def main():
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "password")

    rows = fetch_wikidata(SPARQL_QUERY)

    driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    with driver.session() as session:
        # Contraintes / indexes (au moins 2 contraintes)
        session.run("CREATE CONSTRAINT film_wid IF NOT EXISTS FOR (f:Article) REQUIRE f.wikidata_id IS UNIQUE")
        session.run("CREATE CONSTRAINT dir_wid IF NOT EXISTS FOR (a:Author) REQUIRE a.wikidata_id IS UNIQUE")
        session.run("CREATE CONSTRAINT topic_name_unique IF NOT EXISTS FOR (t:Topic) REQUIRE t.name IS UNIQUE")

        cypher = """
        MERGE (f:Article {wikidata_id: $film_id})
          SET f.title = $film_title,
              f.year = $year
        MERGE (a:Author {wikidata_id: $director_id})
          SET a.name = $director_name
        MERGE (a)-[:DIRECTED]->(f)
        WITH f
        CALL {
          WITH f
          WITH f, $genre_name AS gname
          WHERE gname IS NOT NULL
          MERGE (t:Topic {name: gname})
          MERGE (f)-[:HAS_TOPIC]->(t)
          RETURN 1 AS ok
        }
        RETURN 1
        """

        for row in rows:
            film_uri = row["film"]["value"]
            director_uri = row["director"]["value"]

            genre_name = row.get("genreLabel", {}).get("value")
            pub_date = row.get("pubDate", {}).get("value")

            session.run(
                cypher,
                film_id=qid(film_uri),
                film_title=row["filmLabel"]["value"],
                year=year_from_date(pub_date),
                director_id=qid(director_uri),
                director_name=row["directorLabel"]["value"],
                genre_name=genre_name,
            )

    driver.close()
    print(f"Imported {len(rows)} rows from Wikidata")

if __name__ == "__main__":
    main()