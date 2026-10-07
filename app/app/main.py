import httpx
from fastapi import FastAPI, HTTPException

from app.openalex import search_works

app = FastAPI(title="PaperTrail", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/search")
async def search(q: str = "", limit: int = 10):
    q = q.strip()
    if not q or len(q) > 200:
        raise HTTPException(status_code=400, detail="Query must be between 1 and 200 characters.")
    if not 1 <= limit <= 50:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 50.")

    try:
        results = await search_works(q, limit)
    except httpx.TimeoutException:
        raise HTTPException(status_code=503, detail="OpenAlex did not respond in time.")
    except httpx.HTTPError:
        raise HTTPException(status_code=503, detail="Failed to fetch results from OpenAlex.")

    return {"query": q, "count": len(results), "results": results}