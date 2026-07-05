"""Runs one audit end-to-end: collect -> metrics -> LLM analysis -> revenue math.

Demo audits run entirely from tests/fixtures (zero API spend); fixture dates are
shifted so the newest review is always yesterday, keeping velocity math alive.
"""

import json
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .analysis import analyzer, metrics as metrics_mod
from .collectors import outscraper
from .config import settings
from .db import get_session
from .models import Audit
from .revenue import benchmarks, calculator

FIXTURES = Path(__file__).resolve().parent.parent / "tests" / "fixtures"


def _shift_dates(business_data: dict) -> dict:
    """Shift all review dates forward so the newest one is yesterday."""
    dates = [r["date"] for r in business_data.get("reviews", []) if r.get("date")]
    if not dates:
        return business_data
    newest = max(datetime.fromisoformat(d.replace("Z", "+00:00")) for d in dates)
    if newest.tzinfo is None:
        newest = newest.replace(tzinfo=timezone.utc)
    delta = (datetime.now(timezone.utc) - timedelta(days=1)) - newest
    for r in business_data.get("reviews", []):
        for field in ("date", "owner_response_date"):
            if r.get(field):
                d = datetime.fromisoformat(r[field].replace("Z", "+00:00"))
                if d.tzinfo is None:
                    d = d.replace(tzinfo=timezone.utc)
                r[field] = (d + delta).isoformat()
    return business_data


def load_demo_data() -> tuple[dict, list[dict], dict]:
    business = json.loads((FIXTURES / "sample_reviews.json").read_text(encoding="utf-8"))
    analysis = json.loads((FIXTURES / "sample_analysis.json").read_text(encoding="utf-8"))
    business_data = _shift_dates(business["business"])
    competitor_data = [_shift_dates(c) for c in business.get("competitors", [])]
    return business_data, competitor_data, analysis


def _set(audit_id: str, **fields) -> None:
    session = get_session()
    try:
        audit = session.get(Audit, audit_id)
        for key, value in fields.items():
            setattr(audit, key, value)
        session.commit()
    finally:
        session.close()


def run_audit(audit_id: str) -> None:
    session = get_session()
    audit = session.get(Audit, audit_id)
    session.close()
    if audit is None:
        return
    try:
        if audit.demo:
            business_data, competitor_data, canned_analysis = load_demo_data()
            _set(audit_id, status="analyzing", business_data=business_data,
                 competitor_data=competitor_data)
        else:
            _set(audit_id, status="collecting")
            business_data = outscraper.collect(
                audit.business_name, audit.city, settings.max_reviews_per_audit)
            competitor_data = []
            for name in audit.competitors or []:
                try:
                    competitor_data.append(outscraper.collect(
                        name, audit.city, settings.competitor_review_sample))
                except Exception:
                    pass  # a missing competitor shouldn't sink the audit
            _set(audit_id, status="analyzing", business_data=business_data,
                 competitor_data=competitor_data)
            canned_analysis = None

        computed = metrics_mod.compute(business_data, competitor_data)
        vertical_label = benchmarks.for_vertical(audit.vertical)["label"]
        analysis = canned_analysis or analyzer.analyze(
            audit.business_name, vertical_label, computed, business_data, competitor_data)
        revenue = calculator.calculate(
            audit.vertical, audit.avg_transaction, audit.monthly_customers, computed)

        _set(audit_id, status="complete", metrics=computed, analysis=analysis,
             revenue=revenue, completed_at=datetime.now(timezone.utc))
    except Exception as err:
        _set(audit_id, status="error", error=f"{err}\n{traceback.format_exc()}")
