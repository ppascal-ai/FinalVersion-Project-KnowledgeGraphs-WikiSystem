from fastapi import APIRouter, Depends, HTTPException
from neo4j import Session
from app.database.neo4j import get_db
from app.models.schemas import LLMQueryRequest, LLMQueryResponse

router = APIRouter(prefix="/api", tags=["llm"])

BLOCKED = ["create", "merge", "delete", "set", "drop", "load csv", "call db", "apoc."]

def _is_safe_readonly(cypher: str) -> bool:
    s = cypher.lower()
    return not any(b in s for b in BLOCKED)

def _nl_to_cypher(question: str, limit: int) -> str:
    q = question.lower().strip()

    # 3 intents minimalistes (suffit pour “bonus” si bien documenté)
    if "films of director" in q or "films by director" in q:
        # ex: "films by director Q123"
        # on cherche un id "Q..."
        import re
        m = re.search(r"(q\d+)", q)
        if not m:
            raise HTTPException(400, "Provide a director wikidata id like Q12345.")
        did = m.group(1).upper()
        return f"""
        MATCH (d:Author {{wikidata_id: "{did}"}})-[:DIRECTED]->(f:Article)
        RETURN f.wikidata_id AS wikidata_id, f.title AS title, f.year AS year
        ORDER BY f.year DESC
        LIMIT {limit}
        """

    if "related films" in q or "similar films" in q:
        import re
        m = re.search(r"(q\d+)", q)
        if not m:
            raise HTTPException(400, "Provide a film wikidata id like Q19303.")
        fid = m.group(1).upper()
        return f"""
        MATCH (f:Article {{wikidata_id: "{fid}"}})
        OPTIONAL MATCH (f)<-[:DIRECTED]-(d:Author)
        WITH f, collect(DISTINCT d) AS dirs
        OPTIONAL MATCH (f)-[:HAS_TOPIC]->(t:Topic)
        WITH f, dirs, collect(DISTINCT t) AS topics
        MATCH (other:Article) WHERE other <> f
        OPTIONAL MATCH (other)<-[:DIRECTED]-(od:Author)
        OPTIONAL MATCH (other)-[:HAS_TOPIC]->(ot:Topic)
        WITH other,
          size([x IN collect(DISTINCT od) WHERE x IN dirs]) AS sd,
          size([x IN collect(DISTINCT ot) WHERE x IN topics]) AS st
        WITH other, (sd*2.0 + st*1.0) AS score
        WHERE score > 0
        RETURN other.wikidata_id AS wikidata_id, other.title AS title, other.year AS year, score
        ORDER BY score DESC
        LIMIT {limit}
        """

    if "top genres" in q or "most common genres" in q:
        return f"""
        MATCH (:Article)-[:HAS_TOPIC]->(t:Topic)
        RETURN t.name AS genre, count(*) AS n
        ORDER BY n DESC
        LIMIT {limit}
        """

    raise HTTPException(400, "Unsupported question. Try: top genres / related films Q... / films by director Q...")

@router.post("/llm/query", response_model=LLMQueryResponse)
def llm_query(payload: LLMQueryRequest, db: Session = Depends(get_db)):
    cypher = _nl_to_cypher(payload.question, payload.limit)

    if not _is_safe_readonly(cypher):
        raise HTTPException(400, "Generated Cypher rejected (not read-only).")

    rows = db.run(cypher)
    results = [dict(r) for r in rows]
    return LLMQueryResponse(question=payload.question, cypher=cypher.strip(), results=results)
