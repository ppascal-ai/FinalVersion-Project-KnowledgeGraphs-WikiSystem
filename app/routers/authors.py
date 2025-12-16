# app/routers/authors.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from neo4j import Session

from app.database.neo4j import get_db
from app.models.schemas import (
    Director,
    Film,
    Genre,
    DirectorContributionsResponse,
)

router = APIRouter(prefix="/api", tags=["authors"])


def _node_to_director(node) -> Director:
    return Director(
        wikidata_id=node.get("wikidata_id"),
        name=node.get("name"),
    )


def _node_to_film(node) -> Film:
    return Film(
        wikidata_id=node.get("wikidata_id"),
        title=node.get("title"),
        year=node.get("year"),
    )


def _node_to_genre(node) -> Genre:
    return Genre(name=node.get("name"))


@router.get(
    "/authors/{director_id}/contributions",
    response_model=DirectorContributionsResponse,
)
def get_director_contributions(
    director_id: str = Path(..., description="Director Wikidata id (e.g., Q12345)"),
    limit: int = Query(50, ge=1, le=200, description="Max number of films returned"),
    db: Session = Depends(get_db),
):
    """
    Wikidata Films KG:
    Returns a director's contributions:
    - films they directed (Article nodes)
    - genres (Topic) of these films
    """

    # Check director exists
    rec = db.run(
        "MATCH (d:Author {wikidata_id: $id}) RETURN d LIMIT 1",
        id=director_id,
    ).single()
    if rec is None:
        raise HTTPException(status_code=404, detail="Director not found.")

    director = _node_to_director(rec["d"])

    cypher = """
    MATCH (d:Author {wikidata_id: $id})
    OPTIONAL MATCH (d)-[:DIRECTED]->(f:Article)
    WITH d, collect(DISTINCT f)[0..$limit] AS films
    UNWIND films AS f
    OPTIONAL MATCH (f)-[:HAS_TOPIC]->(g:Topic)
    WITH films, collect(DISTINCT g) AS genres
    RETURN films, genres
    """

    record = db.run(cypher, id=director_id, limit=limit).single()

    films_nodes = record["films"] or []
    genre_nodes = record["genres"] or []

    films: List[Film] = [_node_to_film(f) for f in films_nodes if f is not None]
    genres: List[Genre] = [_node_to_genre(g) for g in genre_nodes if g is not None]

    return DirectorContributionsResponse(
        director=director,
        films=films,
        genres=genres,
    )
