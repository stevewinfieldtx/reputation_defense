"""Deterministic review statistics computed in Python, never by the LLM:
response gaps, response times, and 90-day review velocity for the business
and each competitor.

Review dict shape (normalized by collectors / fixtures):
  {author, rating, text, date, owner_response, owner_response_date}
dates are ISO-8601 strings.
"""

from datetime import datetime, timedelta, timezone
from statistics import median


def _parse(dt: str | None) -> datetime | None:
    if not dt:
        return None
    try:
        parsed = datetime.fromisoformat(dt.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _velocity_90d(reviews: list[dict], now: datetime) -> float:
    cutoff = now - timedelta(days=90)
    recent = [r for r in reviews if (_parse(r.get("date")) or cutoff) > cutoff]
    return round(len(recent) / 3.0, 2)


def compute(business_data: dict, competitor_data: list[dict] | None, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    reviews = business_data.get("reviews", [])
    profile = business_data.get("profile", {})

    ratings = [r["rating"] for r in reviews if r.get("rating") is not None]
    negative = [r for r in reviews if (r.get("rating") or 0) <= 2]
    year_ago = now - timedelta(days=365)
    unanswered_neg_12mo = [
        r for r in negative
        if not r.get("owner_response") and (_parse(r.get("date")) or now) > year_ago
    ]

    response_days = []
    for r in reviews:
        posted, replied = _parse(r.get("date")), _parse(r.get("owner_response_date"))
        if posted and replied and replied >= posted:
            response_days.append((replied - posted).days)

    responded = sum(1 for r in reviews if r.get("owner_response"))

    return {
        # profile rating reflects all-time Google average; fall back to sample mean
        "avg_rating": profile.get("rating") or (round(sum(ratings) / len(ratings), 2) if ratings else 0.0),
        "total_reviews_on_profile": profile.get("reviews_count") or len(reviews),
        "reviews_analyzed": len(reviews),
        "negative_count": len(negative),
        "positive_count": sum(1 for r in reviews if (r.get("rating") or 0) >= 4),
        "response_rate_pct": round(100 * responded / len(reviews), 1) if reviews else 0.0,
        "unanswered_negative_12mo": len(unanswered_neg_12mo),
        "median_response_days": median(response_days) if response_days else None,
        "reviews_per_month_90d": _velocity_90d(reviews, now),
        "competitor_velocity": [
            {
                "name": c.get("profile", {}).get("name", "Competitor"),
                "rating": c.get("profile", {}).get("rating"),
                "reviews_count": c.get("profile", {}).get("reviews_count"),
                "reviews_per_month": _velocity_90d(c.get("reviews", []), now),
            }
            for c in (competitor_data or [])
        ],
    }
