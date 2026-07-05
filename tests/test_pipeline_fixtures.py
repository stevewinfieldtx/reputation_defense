"""End-to-end over the fixtures: metrics -> schema-validated analysis -> revenue -> report HTML."""

from app.analysis import metrics as metrics_mod
from app.analysis.schemas import ReviewAnalysis
from app.pipeline import load_demo_data
from app.reports import builder
from app.revenue import calculator


def test_fixture_analysis_matches_schema():
    _, _, analysis = load_demo_data()
    ReviewAnalysis.model_validate(analysis)


def test_metrics_from_fixture():
    business, competitors, _ = load_demo_data()
    m = metrics_mod.compute(business, competitors)
    assert m["avg_rating"] == 3.9
    assert m["reviews_analyzed"] == 30
    assert m["unanswered_negative_12mo"] >= 5
    assert m["reviews_per_month_90d"] > 0
    assert len(m["competitor_velocity"]) == 2
    hutchins = next(c for c in m["competitor_velocity"] if "Hutchins" in c["name"])
    assert hutchins["reviews_per_month"] > m["reviews_per_month_90d"]


def test_report_renders_from_fixture():
    business, competitors, analysis = load_demo_data()
    m = metrics_mod.compute(business, competitors)
    revenue = calculator.calculate("restaurant", None, None, m)

    class FakeAudit:
        id = "abcd1234deadbeef"
        business_name = "Lone Star Smokehouse"
        demo = True

    html = builder.render(
        "report.html", audit=FakeAudit(), profile=business["profile"],
        metrics=m, analysis=analysis, revenue=revenue, prepared_date="July 06, 2026",
    )
    assert "Lone Star Smokehouse" in html
    assert "Where the money is leaking" in html
    assert "Hutchins BBQ" in html
    assert f"${revenue['total_monthly']:,.0f}" in html
    # every revenue line item's formula must be printed
    for item in revenue["items"]:
        assert item["formula"] in html
