import asyncio
import json
from urllib.error import HTTPError
from urllib.request import Request, urlopen

__all__ = ["post_json", "wait_for_json"]

async def post_json(url: str, payload: dict) -> None:
    await asyncio.to_thread(_post_json, url, payload)


async def get_json(url: str) -> dict:
    return await asyncio.to_thread(_get_json, url)


async def wait_for_json(url: str, interval_seconds: float = 0.25) -> dict:
    while True:
        try:
            return await get_json(url)
        except HTTPError as error:
            if error.code != 404:
                raise
        await asyncio.sleep(interval_seconds)


def _post_json(url: str, payload: dict) -> None:
    body = json.dumps(payload).encode("utf-8")
    request = Request(url, data=body, method="POST")
    request.add_header("Content-Type", "application/json")
    with urlopen(request, timeout=10) as response:
        response.read()


def _get_json(url: str) -> dict:
    request = Request(url, method="GET")
    with urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))