#app/routers/topics.py

"""
Topic (Genre) graph exploration endpoints.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from neo4j import Session

from app.database.neo4j import get_db
from app.models.schemas import (
    Director,
    Film,
    Genre,
    GenreGraphResponse,
    RelatedGenre,
)

router = APIRouter(prefix="/api", tags=["topics"])


def _node_to_genre(node) -> Genre:
    return Genre(name=node.get("name"))


def _node_to_film(node) -> Film:
    return Film(
        wikidata_id=node.get("wikidata_id"),
        title=node.get("title"),
        year=node.get("year"),
    )


def _node_to_director(node) -> Director:
    return Director(
        wikidata_id=node.get("wikidata_id"),
        name=node.get("name"),
    )


def _run_topic_graph_query(
    db: Session,
    topic_name: str,
    depth: int,
    limit: int,
):
    """Run the Cypher query to retrieve the genre subgraph."""
    cypher_depth_1 = """
    MATCH (t:Topic {name: $name})

    OPTIONAL MATCH (f:Article)-[:HAS_TOPIC]->(t)
    WITH t, collect(DISTINCT f)[0..$limit] AS films

    UNWIND films AS f
    OPTIONAL MATCH (d:Author)-[:DIRECTED]->(f)
    WITH t, films, collect(DISTINCT d) AS directors

    OPTIONAL MATCH (f2:Article)-[:HAS_TOPIC]->(t)
    OPTIONAL MATCH (f2)-[:HAS_TOPIC]->(rt:Topic)
    WHERE rt.name <> t.name
    WITH t, films, directors, rt, count(DISTINCT f2) AS shared_films
    ORDER BY shared_films DESC
    WITH t, films, directors,
         collect(
           CASE
             WHEN rt IS NULL THEN NULL
             ELSE { genre: rt, score: shared_films }
           END
         )[0..10] AS related_raw
    RETURN t, films, directors, related_raw
    """

    cypher_depth_2 = """
    MATCH (t:Topic {name: $name})

    OPTIONAL MATCH (f:Article)-[:HAS_TOPIC]->(t)
    OPTIONAL MATCH (f)-[:HAS_TOPIC]->(rt1:Topic)
    WHERE rt1.name <> t.name
    WITH t, rt1, count(DISTINCT f) AS s1
    ORDER BY s1 DESC
    WITH t, collect({rt: rt1, score: s1})[0..10] AS rt1s

    UNWIND rt1s AS x
    WITH t, x.rt AS rt1, x.score AS s1
    OPTIONAL MATCH (f2:Article)-[:HAS_TOPIC]->(rt1)
    OPTIONAL MATCH (f2)-[:HAS_TOPIC]->(rt2:Topic)
    WHERE rt2.name <> rt1.name AND rt2.name <> t.name
    WITH t, rt2, (s1 + count(DISTINCT f2)) AS combined_score
    ORDER BY combined_score DESC
    WITH t, collect({genre: rt2, score: combined_score})[0..10] AS related_raw

    OPTIONAL MATCH (film:Article)-[:HAS_TOPIC]->(t)
    WITH t, related_raw, collect(DISTINCT film)[0..$limit] AS films
    UNWIND films AS f
    OPTIONAL MATCH (d:Author)-[:DIRECTED]->(f)
    WITH t, related_raw, films, collect(DISTINCT d) AS directors
    RETURN t, films, directors, related_raw
    """

    cypher = cypher_depth_2 if depth == 2 else cypher_depth_1
    return db.run(cypher, name=topic_name, limit=limit).single()


@router.get(
    "/topics/{topic_name}/graph",
    response_model=GenreGraphResponse,
)
def get_topic_graph(
    topic_name: str = Path(..., description="Genre name (Topic.name)"),
    depth: int = Query(1, ge=1, le=2),
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Explore a genre-centered subgraph:
    - films
    - directors
    - related genres
    """
    topic_rec = db.run(
        "MATCH (t:Topic {name: $name}) RETURN t LIMIT 1",
        name=topic_name,
    ).single()

    if topic_rec is None:
        raise HTTPException(status_code=404, detail="Topic (genre) not found.")

    record = _run_topic_graph_query(db, topic_name, depth, limit)

    films = [_node_to_film(f) for f in (record["films"] or []) if f]
    directors = [_node_to_director(d) for d in (record["directors"] or []) if d]

    related_topics: List[RelatedGenre] = []
    for item in record["related_raw"] or []:
        if item and item.get("genre"):
            related_topics.append(
                RelatedGenre(
                    genre=_node_to_genre(item["genre"]),
                    score=float(item.get("score", 0)),
                )
            )

    return GenreGraphResponse(
        topic=_node_to_genre(topic_rec["t"]),
        related_topics=related_topics,
        films=films,
        directors=directors,
    )
