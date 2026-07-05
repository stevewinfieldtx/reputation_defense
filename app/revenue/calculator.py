"""The "revenue left on the table" engine.

Deterministic, pure Python. Every line item returns its formula, inputs and
assumptions so the report can print them verbatim — the number is only worth
something if the client can see exactly how it was computed.
"""

import math

from . import benchmarks


def _resolve_inputs(vertical: str, avg_transaction: float | None, monthly_customers: float | None) -> dict:
    bench = benchmarks.for_vertical(vertical)
    aov_provided = avg_transaction is not None and avg_transaction > 0
    mc_provided = monthly_customers is not None and monthly_customers > 0
    aov = float(avg_transaction) if aov_provided else bench["avg_transaction"]
    mc = float(monthly_customers) if mc_provided else bench["monthly_customers"]
    return {
        "vertical_label": bench["label"],
        "avg_transaction": {"value": aov, "source": "client-provided" if aov_provided else f"benchmark ({bench['label']})"},
        "monthly_customers": {"value": mc, "source": "client-provided" if mc_provided else f"benchmark ({bench['label']})"},
        "customer_ltv": {
            "value": aov * bench["repeat_factor"],
            "source": f"avg transaction x {bench['repeat_factor']} lifetime visits (benchmark)",
        },
    }


def _next_half_star(rating: float) -> float:
    """Smallest half-star tier strictly above the rating (4.3 -> 4.5, 4.5 -> 5.0)."""
    return math.floor(rating * 2) / 2 + 0.5


def rating_gap_item(rating: float, monthly_revenue: float) -> dict:
    ceiling = benchmarks.RATING_CEILING
    lift = benchmarks.REVENUE_LIFT_PER_HALF_STAR
    if rating >= ceiling:
        target, loss = rating, 0.0
    else:
        target = min(5.0, _next_half_star(rating))
        half_steps = (target - rating) / 0.5
        loss = monthly_revenue * lift * half_steps
    return {
        "key": "rating_gap",
        "title": f"Rating gap ({rating:.1f} -> {target:.1f} stars)",
        "monthly_loss": round(loss, 2),
        "formula": "monthly revenue x 2.5% per half-star x half-stars below next tier",
        "explanation": (
            "Harvard Business School research (Luca 2011/2016) links a one-star rating increase "
            "to 5-9% revenue growth for independent businesses; we use the conservative low end. "
            f"No loss is claimed at or above {ceiling} stars."
        ),
        "inputs": {"current_rating": rating, "target_rating": target, "monthly_revenue": round(monthly_revenue, 2)},
    }


def response_gap_item(unanswered_negative_12mo: int, customer_ltv: float) -> dict:
    factor = benchmarks.UNANSWERED_NEGATIVE_LOSS_FACTOR
    annual = unanswered_negative_12mo * customer_ltv * factor
    return {
        "key": "response_gap",
        "title": f"Unanswered negative reviews ({unanswered_negative_12mo} in last 12 months)",
        "monthly_loss": round(annual / 12, 2),
        "formula": "unanswered negatives x customer LTV x 15% deterrence, spread over 12 months",
        "explanation": (
            "An unanswered negative review keeps deterring prospects; platform studies find owner "
            "responses recover roughly 15% of otherwise-lost conversions. Counted only for reviews "
            "rated 1-2 stars in the last 12 months with no owner reply."
        ),
        "inputs": {"unanswered_negative_12mo": unanswered_negative_12mo, "customer_ltv": round(customer_ltv, 2)},
    }


def velocity_gap_item(own_per_month: float, best_competitor: dict | None) -> dict:
    per_review = benchmarks.PER_REVIEW_VALUE
    if best_competitor and best_competitor.get("reviews_per_month", 0) > own_per_month:
        gap = best_competitor["reviews_per_month"] - own_per_month
        loss = gap * per_review
        title = f"Review velocity vs. {best_competitor['name']} ({own_per_month:.1f} vs {best_competitor['reviews_per_month']:.1f}/mo)"
    else:
        gap, loss = 0.0, 0.0
        title = "Review velocity (leading or matching local competitors)"
    return {
        "key": "velocity_gap",
        "title": title,
        "monthly_loss": round(loss, 2),
        "formula": "(competitor reviews/mo - your reviews/mo) x $50 per review",
        "explanation": (
            "Google's local pack weighs review recency and volume; falling behind the local leader "
            "costs prominence. $50/review is a proxy for that visibility value, based on 90-day velocity."
        ),
        "inputs": {
            "own_reviews_per_month": round(own_per_month, 2),
            "best_competitor": best_competitor or {},
            "monthly_gap": round(gap, 2),
        },
    }


def calculate(vertical: str, avg_transaction: float | None, monthly_customers: float | None, metrics: dict) -> dict:
    """metrics comes from app.analysis.metrics.compute()."""
    inputs = _resolve_inputs(vertical, avg_transaction, monthly_customers)
    monthly_revenue = inputs["avg_transaction"]["value"] * inputs["monthly_customers"]["value"]

    competitors = metrics.get("competitor_velocity") or []
    best = max(competitors, key=lambda c: c.get("reviews_per_month", 0)) if competitors else None

    items = [
        rating_gap_item(metrics["avg_rating"], monthly_revenue),
        response_gap_item(metrics["unanswered_negative_12mo"], inputs["customer_ltv"]["value"]),
        velocity_gap_item(metrics["reviews_per_month_90d"], best),
    ]
    total = round(sum(i["monthly_loss"] for i in items), 2)
    return {
        "assumptions": inputs,
        "monthly_revenue_estimate": round(monthly_revenue, 2),
        "items": items,
        "total_monthly": total,
        "total_annual": round(total * 12, 2),
    }
