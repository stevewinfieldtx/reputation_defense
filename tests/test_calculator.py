from app.revenue import benchmarks, calculator


def _metrics(rating=3.9, unanswered=7, velocity=2.3, competitors=None):
    return {
        "avg_rating": rating,
        "unanswered_negative_12mo": unanswered,
        "reviews_per_month_90d": velocity,
        "competitor_velocity": competitors or [],
    }


def test_rating_gap_next_half_star():
    item = calculator.rating_gap_item(3.9, monthly_revenue=10000)
    # 3.9 -> 4.0 target; (4.0 - 3.9) / 0.5 = 0.2 half-star steps
    assert item["inputs"]["target_rating"] == 4.0
    assert item["monthly_loss"] == round(10000 * benchmarks.REVENUE_LIFT_PER_HALF_STAR * 0.2, 2)


def test_rating_gap_zero_at_ceiling():
    assert calculator.rating_gap_item(4.8, 10000)["monthly_loss"] == 0.0
    assert calculator.rating_gap_item(4.9, 10000)["monthly_loss"] == 0.0


def test_rating_on_exact_half_star_targets_next_tier():
    item = calculator.rating_gap_item(4.5, 10000)
    assert item["inputs"]["target_rating"] == 5.0


def test_response_gap_spread_over_12_months():
    item = calculator.response_gap_item(6, customer_ltv=200.0)
    expected_annual = 6 * 200.0 * benchmarks.UNANSWERED_NEGATIVE_LOSS_FACTOR
    assert item["monthly_loss"] == round(expected_annual / 12, 2)


def test_velocity_gap_only_counts_shortfall():
    ahead = calculator.velocity_gap_item(10.0, {"name": "X", "reviews_per_month": 4.0})
    assert ahead["monthly_loss"] == 0.0
    behind = calculator.velocity_gap_item(2.0, {"name": "X", "reviews_per_month": 10.0})
    assert behind["monthly_loss"] == 8.0 * benchmarks.PER_REVIEW_VALUE


def test_calculate_uses_client_numbers_when_provided():
    result = calculator.calculate("restaurant", 40.0, 1000, _metrics())
    assert result["assumptions"]["avg_transaction"]["source"] == "client-provided"
    assert result["monthly_revenue_estimate"] == 40000.0


def test_calculate_falls_back_to_benchmarks():
    result = calculator.calculate("restaurant", None, None, _metrics())
    assert "benchmark" in result["assumptions"]["avg_transaction"]["source"]
    assert result["total_monthly"] == round(sum(i["monthly_loss"] for i in result["items"]), 2)
    assert result["total_annual"] == round(result["total_monthly"] * 12, 2)


def test_unknown_vertical_uses_default():
    result = calculator.calculate("spaceport", None, None, _metrics())
    assert result["assumptions"]["vertical_label"] == "General Local Business"
