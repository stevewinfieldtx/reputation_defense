"""Google Maps profile + reviews via the Outscraper API.

Docs: https://app.outscraper.com/api-docs — maps/reviews-v3 returns the place record
with a reviews_data array. Large requests come back 202 + results_location, which we
poll until done.
"""

import time

import httpx

from ..config import settings

API_ROOT = "https://api.app.outscraper.com"
POLL_INTERVAL_S = 15
POLL_TIMEOUT_S = 600


class OutscraperError(RuntimeError):
    pass


def _headers() -> dict:
    return {"X-API-KEY": settings.outscraper_api_key}


def _await_async_results(results_location: str) -> dict:
    deadline = time.monotonic() + POLL_TIMEOUT_S
    while time.monotonic() < deadline:
        time.sleep(POLL_INTERVAL_S)
        resp = httpx.get(results_location, headers=_headers(), timeout=60)
        resp.raise_for_status()
        payload = resp.json()
        if payload.get("status") == "Success":
            return payload
        if payload.get("status") in ("Failure", "Error"):
            raise OutscraperError(f"Outscraper job failed: {payload}")
    raise OutscraperError("timed out waiting for Outscraper results")


def _normalize(place: dict) -> dict:
    reviews = []
    for r in place.get("reviews_data") or []:
        reviews.append({
            "author": r.get("author_title") or "",
            "rating": r.get("review_rating"),
            "text": r.get("review_text") or "",
            "date": r.get("review_datetime_utc") or "",
            "owner_response": r.get("owner_answer") or None,
            "owner_response_date": r.get("owner_answer_timestamp_datetime_utc") or None,
        })
    return {
        "profile": {
            "name": place.get("name") or "",
            "rating": place.get("rating"),
            "reviews_count": place.get("reviews"),
            "address": place.get("full_address") or "",
            "category": place.get("type") or "",
        },
        "reviews": reviews,
    }


def collect(business_name: str, city: str, max_reviews: int) -> dict:
    if not settings.outscraper_api_key:
        raise OutscraperError("OUTSCRAPER_API_KEY not configured")
    query = f"{business_name}, {city}"
    resp = httpx.get(
        f"{API_ROOT}/maps/reviews-v3",
        params={
            "query": query,
            "reviewsLimit": max_reviews,
            "sort": "newest",
            "async": "false",
            "language": "en",
        },
        headers=_headers(),
        timeout=180,
    )
    if resp.status_code == 202:
        payload = _await_async_results(resp.json()["results_location"])
    else:
        resp.raise_for_status()
        payload = resp.json()

    data = payload.get("data") or []
    # data is a list per query; each query yields a list of matched places
    places = data[0] if data and isinstance(data[0], list) else data
    if not places:
        raise OutscraperError(f"no Google Maps match for '{query}'")
    return _normalize(places[0] if isinstance(places, list) else places)
