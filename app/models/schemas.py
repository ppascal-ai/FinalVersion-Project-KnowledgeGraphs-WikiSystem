# app/models/schemas.py

"""Pydantic response schemas for the Wikidata Films API."""

from typing import List, Optional

from pydantic import BaseModel, Field


class Film(BaseModel):
    """Film entity (Wikidata)."""

    wikidata_id: str = Field(..., description="Wikidata entity id (e.g., Q19303)")
    title: str
    year: Optional[int] = None


class Director(BaseModel):
    """Director entity (Wikidata)."""

    wikidata_id: str
    name: str


class Genre(BaseModel):
    """Genre/topic entity."""

    name: str


class FilmWithContext(Film):
    """Film enriched with related directors and genres."""

    directors: List[Director] = []
    genres: List[Genre] = []


class FilmSearchResponse(BaseModel):
    """Search response for films."""

    query: str
    results: List[FilmWithContext]


class RelatedGenre(BaseModel):
    """Related genre with a co-occurrence score."""

    genre: Genre
    score: float = Field(
        ...,
        description="Co-occurrence score (shared films count / combined score)",
    )


class GenreGraphResponse(BaseModel):
    """Subgraph response centered around a genre."""

    topic: Genre
    related_topics: List[RelatedGenre] = []
    films: List[Film] = []
    directors: List[Director] = []


class DirectorContributionsResponse(BaseModel):
    """Director contributions: films and genres."""

    director: Director
    films: List[Film] = []
    genres: List[Genre] = []


class RelatedFilm(BaseModel):
    """Related film with a similarity score."""

    film: Film
    score: float


class RelatedFilmsResponse(BaseModel):
    """Related films response."""

    film_id: str
    related: List[RelatedFilm]
