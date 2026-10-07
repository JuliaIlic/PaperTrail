import logging

import httpx
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool

from app.openalex import search_works
from app.storage import get_history, save_search

logger = logging.getLogger("papertrail")

app = FastAPI(title="PaperTrail", version="0.2.0")


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

    try:
        await run_in_threadpool(save_search, q, len(results))
    except (BotoCoreError, ClientError):
        logger.exception("Failed to save search history")

    return {"query": q, "count": len(results), "results": results}


@app.get("/history")
def history():
    try:
        items = get_history()
    except (BotoCoreError, ClientError):
        logger.exception("Failed to read search history")
        raise HTTPException(status_code=503, detail="Search history is unavailable.")
    return {"count": len(items), "items": items}