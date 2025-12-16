# app/main.py

from fastapi import FastAPI, Depends
from neo4j import Session

from app.database.neo4j import get_db, close_driver

# Imports strong (pas besoin d'export dans app/routers/__init__.py)
from app.routers.search import router as search_router
from app.routers.articles import router as articles_router
from app.routers.topics import router as topics_router
from app.routers.authors import router as authors_router

app = FastAPI(
    title="Knowledge Graph / Wiki API",
    description="API pour le projet de Knowledge Graph (Articles, Topics, Authors, Tags, ...)",
    version="0.1.0",
)


@app.get("/health", tags=["health"])
def health_check(db: Session = Depends(get_db)):
    result = db.run("RETURN 1 AS ok").single()
    db_ok = bool(result and result.get("ok") == 1)
    return {"status": "ok", "neo4j": "up" if db_ok else "down"}


# On enregistre les routes ici
app.include_router(search_router)
app.include_router(articles_router)
app.include_router(topics_router)
app.include_router(authors_router)


@app.on_event("shutdown")
def on_shutdown():
    close_driver()
