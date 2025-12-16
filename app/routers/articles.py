# app/routers/articles.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from neo4j import Session

from app.database.neo4j import get_db
from app.security import require_api_key
from app.models.schemas import (
    Film,
    RelatedFilm,
    RelatedFilmsResponse,
)

router = APIRouter(prefix="/api", tags=["articles"])


def _node_to_film(node) -> Film:
    return Film(
        wikidata_id=node.get("wikidata_id"),
        title=node.get("title"),
        year=node.get("year"),
    )


@router.get(
    "/articles/{film_id}/related",
    response_model=RelatedFilmsResponse,
)
def get_related_films(
    film_id: str = Path(..., description="Film Wikidata id (e.g., Q19303)"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    _api_key: bool = Depends(require_api_key),
):
    """
    Related films suggestions for Wikidata Films KG.

    We consider a film "related" if it shares:
    - the same director (strong signal)
    - at least one genre (Topic)
    - optionally similar year (weak signal)
    Score is computed from these shared signals.
    """

    # Check film exists
    exists_cypher = "MATCH (f:Article {wikidata_id: $id}) RETURN f LIMIT 1"
    rec = db.run(exists_cypher, id=film_id).single()
    if rec is None:
        raise HTTPException(status_code=404, detail="Film not found.")

    cypher = """
    MATCH (f:Article {wikidata_id: $id})

    OPTIONAL MATCH (fd:Author)-[:DIRECTED]->(f)
    WITH f, collect(DISTINCT fd) AS f_directors
    OPTIONAL MATCH (f)-[:HAS_TOPIC]->(fg:Topic)
    WITH f, f_directors, collect(DISTINCT fg) AS f_genres

    MATCH (other:Article)
    WHERE other <> f

    // directors shared
    OPTIONAL MATCH (od:Author)-[:DIRECTED]->(other)
    WITH f, other, f_directors, f_genres, collect(DISTINCT od) AS o_directors

    // genres shared
    OPTIONAL MATCH (other)-[:HAS_TOPIC]->(og:Topic)
    WITH f, other, f_directors, f_genres, o_directors, collect(DISTINCT og) AS o_genres

    WITH f, other,
        size([d IN o_directors WHERE d IN f_directors]) AS shared_directors,
        size([g IN o_genres WHERE g IN f_genres]) AS shared_genres

    WITH f, other,
        (shared_directors * 2.0 + shared_genres * 1.0) AS base_score,
        CASE
            WHEN other.year IS NULL OR f.year IS NULL THEN 0.0
            WHEN abs(other.year - f.year) <= 1 THEN 0.5
            WHEN abs(other.year - f.year) <= 3 THEN 0.2
            ELSE 0.0
        END AS year_bonus

    WITH other, (base_score + year_bonus) AS score
    WHERE score > 0
    RETURN other, score
    ORDER BY score DESC, other.year DESC
    LIMIT $limit
    """


    records = db.run(cypher, id=film_id, limit=limit)

    related: List[RelatedFilm] = []
    for r in records:
        other_node = r["other"]
        if other_node is None:
            continue
        score = r["score"] if r["score"] is not None else 0.0
        related.append(
            RelatedFilm(
                film=_node_to_film(other_node),
                score=float(score),
            )
        )

    return RelatedFilmsResponse(film_id=film_id, related=related)
