# app/models/schemas.py
from typing import List, Optional
from pydantic import BaseModel, Field


class Film(BaseModel):
    wikidata_id: str = Field(..., description="Wikidata entity id (e.g., Q19303)")
    title: str
    year: Optional[int] = None


class Director(BaseModel):
    wikidata_id: str
    name: str


class Genre(BaseModel):
    name: str


class FilmWithContext(Film):
    directors: List[Director] = []
    genres: List[Genre] = []


class FilmSearchResponse(BaseModel):
    query: str
    results: List[FilmWithContext]


# --- Topics / Graph exploration ---

class RelatedGenre(BaseModel):
    genre: Genre
    score: float = Field(..., description="Co-occurrence score (shared films count / combined score)")


class GenreGraphResponse(BaseModel):
    topic: Genre
    related_topics: List[RelatedGenre] = []
    films: List[Film] = []
    directors: List[Director] = []

class DirectorContributionsResponse(BaseModel):
    director: Director
    films: List[Film] = []
    genres: List[Genre] = []


class RelatedFilm(BaseModel):
    film: Film
    score: float


class RelatedFilmsResponse(BaseModel):
    film_id: str
    related: List[RelatedFilm]
