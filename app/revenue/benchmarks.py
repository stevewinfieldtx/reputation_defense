"""Per-vertical benchmark assumptions used when the client doesn't supply real numbers.

Every figure that reaches a report must be traceable to either client input or one of
these benchmarks, and the report labels which was used. Sources are deliberately
conservative round numbers; refine per market as real client data accumulates.
"""

VERTICALS = {
    "restaurant": {
        "label": "Restaurant / Food Service",
        "avg_transaction": 32.0,
        "monthly_customers": 1200,
        "repeat_factor": 4.0,  # avg lifetime visits -> LTV = avg_transaction * repeat_factor
    },
    "home_services": {
        "label": "Home Services (plumbing, HVAC, electrical)",
        "avg_transaction": 450.0,
        "monthly_customers": 45,
        "repeat_factor": 2.2,
    },
    "dental": {
        "label": "Dental / Medical Practice",
        "avg_transaction": 280.0,
        "monthly_customers": 220,
        "repeat_factor": 8.0,
    },
    "salon": {
        "label": "Salon / Personal Care",
        "avg_transaction": 65.0,
        "monthly_customers": 350,
        "repeat_factor": 10.0,
    },
    "auto_repair": {
        "label": "Auto Repair",
        "avg_transaction": 380.0,
        "monthly_customers": 90,
        "repeat_factor": 3.5,
    },
    "retail": {
        "label": "Local Retail",
        "avg_transaction": 48.0,
        "monthly_customers": 600,
        "repeat_factor": 5.0,
    },
    "default": {
        "label": "General Local Business",
        "avg_transaction": 150.0,
        "monthly_customers": 200,
        "repeat_factor": 3.0,
    },
}

# Harvard Business School (Luca, 2011, rev. 2016): a one-star Yelp rating increase
# maps to a 5-9% revenue increase for independent businesses. We use the low end,
# halved per half-star.
REVENUE_LIFT_PER_HALF_STAR = 0.025

# Share of prospects assumed lost when they see a recent negative review with no
# owner response (conservative reading of "responding improves conversion ~15%"
# findings from review-platform studies).
UNANSWERED_NEGATIVE_LOSS_FACTOR = 0.15

# Value assigned to one incremental monthly review vs. the local leader — proxy for
# the prominence/local-pack effect of review velocity.
PER_REVIEW_VALUE = 50.0

# A business is considered "at ceiling" here; no rating-gap loss is claimed above it.
RATING_CEILING = 4.8


def for_vertical(vertical: str) -> dict:
    return VERTICALS.get(vertical, VERTICALS["default"])
