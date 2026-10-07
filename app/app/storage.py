from datetime import datetime, timezone

import boto3
from boto3.dynamodb.conditions import Key

from app.config import AWS_REGION, DYNAMODB_ENDPOINT, DYNAMODB_TABLE

PARTITION_KEY = "search"


def _table():
    kwargs = {"region_name": AWS_REGION}
    if DYNAMODB_ENDPOINT:
        kwargs["endpoint_url"] = DYNAMODB_ENDPOINT
    return boto3.resource("dynamodb", **kwargs).Table(DYNAMODB_TABLE)


def save_search(query: str, result_count: int) -> None:
    _table().put_item(
        Item={
            "pk": PARTITION_KEY,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "query": query,
            "result_count": result_count,
        }
    )


def get_history(limit: int = 20) -> list[dict]:
    response = _table().query(
        KeyConditionExpression=Key("pk").eq(PARTITION_KEY),
        ScanIndexForward=False,  # newest first
        Limit=limit,
    )
    return [
        {
            "query": item["query"],
            "created_at": item["created_at"],
            "result_count": int(item["result_count"]),
        }
        for item in response["Items"]
    ]