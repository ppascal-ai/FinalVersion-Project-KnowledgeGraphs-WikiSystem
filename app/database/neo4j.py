import os
from functools import lru_cache
from typing import Generator

from neo4j import GraphDatabase, Driver, Session, basic_auth


@lru_cache
def get_driver() -> Driver:
    """
    Initialise et renvoie un driver Neo4j (singleton grâce à lru_cache).
    Les infos de connexion viennent des variables d'environnement.
    """
    uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")

    driver = GraphDatabase.driver(uri, auth=basic_auth(user, password))
    return driver


def get_db() -> Generator[Session, None, None]:
    """
    Dépendance FastAPI : fournit une session Neo4j par requête.
    Utilisation : Depends(get_db)
    """
    driver = get_driver()
    session: Session = driver.session()
    try:
        yield session
    finally:
        session.close()


def close_driver() -> None:
    """
    Ferme proprement le driver à l'arrêt de l'application.
    """
    driver = get_driver()
    driver.close()
