# app/main.py
"""
FastAPI application entrypoint.

Exposes the public API endpoints and provides a health check endpoint
to validate the Neo4j connection.
"""

from fastapi import Depends, FastAPI
from neo4j import Session

from app.database.neo4j import close_driver, get_db

# Router imports (no need for app/routers/__init__.py exports)
from app.routers.articles import router as articles_router
from app.routers.authors import router as authors_router
from app.routers.search import router as search_router
from app.routers.topics import router as topics_router
from app.routers import llm


app = FastAPI(
    title="Knowledge Graph / Wiki API",
    description="API for a Wikidata-based Knowledge Graph (films, directors, genres).",
    version="0.1.0",
)


@app.get("/health", tags=["health"])
def health_check(db: Session = Depends(get_db)):
    """Healthcheck endpoint verifying Neo4j connectivity."""
    result = db.run("RETURN 1 AS ok").single()
    db_ok = bool(result and result.get("ok") == 1)
    return {"status": "ok", "neo4j": "up" if db_ok else "down"}


# Register routes
app.include_router(search_router)
app.include_router(articles_router)
app.include_router(topics_router)
app.include_router(authors_router)
app.include_router(llm.router)


@app.on_event("shutdown")
def on_shutdown():
    """Close Neo4j driver on application shutdown."""
    close_driver()
