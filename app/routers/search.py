# app/routers/search.py

"""
Search endpoint for Wikidata films.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from neo4j import Session

from app.database.neo4j import get_db
from app.models.schemas import (
    Director,
    Film,
    FilmSearchResponse,
    FilmWithContext,
    Genre,
)

router = APIRouter(prefix="/api", tags=["search"])


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


def _node_to_genre(node) -> Genre:
    return Genre(name=node.get("name"))


@router.get("/search", response_model=FilmSearchResponse)
def search_films(
    q: str = Query(..., description="Search query string"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Search films by title, director or genre."""
    if not q.strip():
        raise HTTPException(status_code=400, detail="Query 'q' must not be empty.")

    cypher = """
    CALL {
        MATCH (f:Article)
        WHERE toLower(f.title) CONTAINS toLower($q)
        RETURN DISTINCT f
        UNION
        MATCH (d:Author)-[:DIRECTED]->(f:Article)
        WHERE toLower(d.name) CONTAINS toLower($q)
        RETURN DISTINCT f
        UNION
        MATCH (f:Article)-[:HAS_TOPIC]->(g:Topic)
        WHERE toLower(g.name) CONTAINS toLower($q)
        RETURN DISTINCT f
    }
    WITH f
    OPTIONAL MATCH (f)<-[:DIRECTED]-(d:Author)
    OPTIONAL MATCH (f)-[:HAS_TOPIC]->(g:Topic)
    RETURN f,
           collect(DISTINCT d) AS directors,
           collect(DISTINCT g) AS genres
    LIMIT $limit
    """

    records = db.run(cypher, q=q, limit=limit)

    results: List[FilmWithContext] = []
    for record in records:
        film = _node_to_film(record["f"])
        directors = [
            _node_to_director(d)
            for d in (record["directors"] or [])
            if d is not None
        ]
        genres = [
            _node_to_genre(g)
            for g in (record["genres"] or [])
            if g is not None
        ]

        results.append(
            FilmWithContext(
                **film.model_dump(),
                directors=directors,
                genres=genres,
            )
        )

    return FilmSearchResponse(query=q, results=results)
