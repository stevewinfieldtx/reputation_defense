from datetime import datetime, timezone

from fastapi import BackgroundTasks, FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select

from . import pipeline
from .config import settings
from .db import get_session, init_db
from .models import Audit
from .reports import builder
from .revenue.benchmarks import VERTICALS

app = FastAPI(title="Reputation Defense")


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/", response_class=HTMLResponse)
def intake() -> str:
    return builder.render("intake.html", verticals=VERTICALS)


@app.post("/audits")
def create_audit(
    background: BackgroundTasks,
    business_name: str = Form(...),
    city: str = Form(...),
    vertical: str = Form("default"),
    avg_transaction: float | None = Form(None),
    monthly_customers: float | None = Form(None),
    competitor1: str = Form(""),
    competitor2: str = Form(""),
    competitor3: str = Form(""),
):
    competitors = [c.strip() for c in (competitor1, competitor2, competitor3) if c.strip()]
    audit = Audit(
        business_name=business_name.strip(),
        city=city.strip(),
        vertical=vertical if vertical in VERTICALS else "default",
        avg_transaction=avg_transaction,
        monthly_customers=monthly_customers,
        competitors=competitors,
    )
    session = get_session()
    session.add(audit)
    session.commit()
    audit_id = audit.id
    session.close()
    background.add_task(pipeline.run_audit, audit_id)
    return RedirectResponse(f"/audits/{audit_id}", status_code=303)


@app.get("/audits/{audit_id}", response_class=HTMLResponse)
def audit_status(audit_id: str) -> str:
    audit = _get_audit(audit_id)
    return builder.render("status.html", audit=audit)


@app.get("/reports/{audit_id}", response_class=HTMLResponse)
def report(audit_id: str) -> str:
    audit = _get_audit(audit_id)
    if audit.status != "complete":
        return builder.render("status.html", audit=audit)
    return builder.render(
        "report.html",
        audit=audit,
        profile=(audit.business_data or {}).get("profile", {}),
        metrics=audit.metrics,
        analysis=audit.analysis,
        revenue=audit.revenue,
        prepared_date=(audit.completed_at or datetime.now(timezone.utc)).strftime("%B %d, %Y"),
    )


@app.get("/demo")
def demo() -> RedirectResponse:
    """Run (or reuse) a fixture-driven sample audit — zero API spend."""
    session = get_session()
    existing = session.execute(
        select(Audit).where(Audit.demo.is_(True), Audit.status == "complete")
    ).scalars().first()
    if existing:
        session.close()
        return RedirectResponse(f"/reports/{existing.id}", status_code=303)
    audit = Audit(business_name="Lone Star Smokehouse", city="Plano, TX",
                  vertical="restaurant", demo=True,
                  competitors=["Hutchins BBQ", "Smokey John's Bar-B-Que"])
    session.add(audit)
    session.commit()
    audit_id = audit.id
    session.close()
    pipeline.run_audit(audit_id)  # fixture-driven, fast enough to run inline
    return RedirectResponse(f"/reports/{audit_id}", status_code=303)


@app.get("/admin", response_class=HTMLResponse)
def admin(token: str = "") -> str:
    if token != settings.admin_token:
        raise HTTPException(status_code=403, detail="bad token")
    session = get_session()
    audits = session.execute(select(Audit).order_by(Audit.created_at.desc())).scalars().all()
    session.close()
    return builder.render("admin.html", audits=audits)


@app.get("/health")
def health() -> dict:
    return {
        "ok": True,
        "live_collection": settings.live_collection_enabled,
        "live_analysis": settings.live_analysis_enabled,
    }


def _get_audit(audit_id: str) -> Audit:
    session = get_session()
    audit = session.get(Audit, audit_id)
    session.close()
    if audit is None:
        raise HTTPException(status_code=404, detail="audit not found")
    return audit
