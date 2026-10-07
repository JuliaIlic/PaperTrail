import os

OPENALEX_URL = os.getenv("OPENALEX_URL", "https://api.openalex.org/works")
OPENALEX_TIMEOUT = float(os.getenv("OPENALEX_TIMEOUT", "5"))