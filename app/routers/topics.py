#app/routers/topics.py

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from neo4j import Session

from app.database.neo4j import get_db
from app.models.schemas import (
    Genre,
    Film,
    Director,
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


@router.get(
    "/topics/{topic_name}/graph",
    response_model=GenreGraphResponse,
)
def get_topic_graph(
    topic_name: str = Path(..., description="Genre name (Topic.name)"),
    depth: int = Query(1, ge=1, le=2, description="1 = direct co-occurrence, 2 = expands one hop"),
    limit: int = Query(25, ge=1, le=100, description="Max number of films returned"),
    db: Session = Depends(get_db),
):
    """
    Explore a Genre (Topic) subgraph for Wikidata Films:

    - topic: the requested genre
    - related_topics: genres co-occurring on the same films (with a score)
    - films: films tagged with this genre
    - directors: directors connected to those films

    depth=2 expands related genres one extra hop (still summarized).
    """

    # 1) Check topic exists
    topic_rec = db.run(
        "MATCH (t:Topic {name: $name}) RETURN t LIMIT 1",
        name=topic_name,
    ).single()

    if topic_rec is None:
        raise HTTPException(status_code=404, detail="Topic (genre) not found.")

    topic = _node_to_genre(topic_rec["t"])

    # 2) Main query: films + directors + related topics
    # Related topics = co-occurrence: (f)-[:HAS_TOPIC]->(t) and (f)-[:HAS_TOPIC]->(rt)
    # Score = number of shared films
    cypher_depth_1 = """
    MATCH (t:Topic {name: $name})

    // Films in this genre
    OPTIONAL MATCH (f:Article)-[:HAS_TOPIC]->(t)
    WITH t, collect(DISTINCT f)[0..$limit] AS films

    // Directors of those films
    UNWIND films AS f
    OPTIONAL MATCH (d:Author)-[:DIRECTED]->(f)
    WITH t, films, collect(DISTINCT d) AS directors

    // Related genres via co-occurrence (on any film)
    OPTIONAL MATCH (f2:Article)-[:HAS_TOPIC]->(t)
    OPTIONAL MATCH (f2)-[:HAS_TOPIC]->(rt:Topic)
    WHERE rt.name <> t.name
    WITH t, films, directors, rt, count(DISTINCT f2) AS shared_films
    ORDER BY shared_films DESC
    WITH t, films, directors,
         collect(
           CASE WHEN rt IS NULL THEN NULL
                ELSE { genre: rt, score: shared_films }
           END
         )[0..10] AS related_raw
    RETURN t, films, directors, related_raw
    """

    cypher_depth_2 = """
    MATCH (t:Topic {name: $name})

    // Direct related topics (rt1) by co-occurrence
    OPTIONAL MATCH (f:Article)-[:HAS_TOPIC]->(t)
    OPTIONAL MATCH (f)-[:HAS_TOPIC]->(rt1:Topic)
    WHERE rt1.name <> t.name
    WITH t, rt1, count(DISTINCT f) AS s1
    ORDER BY s1 DESC
    WITH t, collect({rt: rt1, score: s1})[0..10] AS rt1s

    // Expand: related topics of related topics (rt2), score aggregated
    UNWIND rt1s AS x
    WITH t, x.rt AS rt1, x.score AS s1
    OPTIONAL MATCH (f2:Article)-[:HAS_TOPIC]->(rt1)
    OPTIONAL MATCH (f2)-[:HAS_TOPIC]->(rt2:Topic)
    WHERE rt2.name <> rt1.name AND rt2.name <> t.name
    WITH t, rt1, s1, rt2, count(DISTINCT f2) AS s2
    WITH t, rt2, (s1 + s2) AS combined_score
    ORDER BY combined_score DESC
    WITH t, collect({genre: rt2, score: combined_score})[0..10] AS related_raw

    // Films + directors (same as depth=1)
    OPTIONAL MATCH (film:Article)-[:HAS_TOPIC]->(t)
    WITH t, related_raw, collect(DISTINCT film)[0..$limit] AS films
    UNWIND films AS f
    OPTIONAL MATCH (d:Author)-[:DIRECTED]->(f)
    WITH t, related_raw, films, collect(DISTINCT d) AS directors
    RETURN t, films, directors, related_raw
    """

    cypher = cypher_depth_2 if depth == 2 else cypher_depth_1
    rec = db.run(cypher, name=topic_name, limit=limit).single()

    films_nodes = rec["films"] or []
    director_nodes = rec["directors"] or []
    related_raw = rec["related_raw"] or []

    films: List[Film] = [_node_to_film(n) for n in films_nodes if n is not None]
    directors: List[Director] = [_node_to_director(n) for n in director_nodes if n is not None]

    related_topics: List[RelatedGenre] = []
    for item in related_raw:
        if not item:
            continue
        gnode = item.get("genre")
        score = item.get("score", 0)
        if gnode is None:
            continue
        related_topics.append(
            RelatedGenre(
                genre=_node_to_genre(gnode),
                score=float(score),
            )
        )

    return GenreGraphResponse(
        topic=topic,
        related_topics=related_topics,
        films=films,
        directors=directors,
    )
