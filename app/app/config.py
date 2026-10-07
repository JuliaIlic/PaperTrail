import os

OPENALEX_URL = os.getenv("OPENALEX_URL", "https://api.openalex.org/works")
OPENALEX_TIMEOUT = float(os.getenv("OPENALEX_TIMEOUT", "5"))

AWS_REGION = os.getenv("AWS_REGION", "eu-central-1")
DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE", "papertrail-history")

DYNAMODB_ENDPOINT = os.getenv("DYNAMODB_ENDPOINT") or None