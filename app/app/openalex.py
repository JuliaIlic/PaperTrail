import httpx

from app.config import OPENALEX_TIMEOUT, OPENALEX_URL


async def search_works(query: str, limit: int = 10) -> list[dict]:
    params = {
        "search": query,
        "per-page": limit,
        "select": "display_name,authorships,publication_year,cited_by_count,doi",
    }
    async with httpx.AsyncClient(timeout=OPENALEX_TIMEOUT) as client:
        response = await client.get(OPENALEX_URL, params=params)
        response.raise_for_status()

    results = []
    for work in response.json().get("results", []):
        authors = [
            a["author"]["display_name"]
            for a in work.get("authorships", [])[:5]
            if a.get("author")
        ]
        results.append(
            {
                "title": work.get("display_name"),
                "authors": authors,
                "year": work.get("publication_year"),
                "citations": work.get("cited_by_count"),
                "doi": work.get("doi"),
            }
        )
    return results