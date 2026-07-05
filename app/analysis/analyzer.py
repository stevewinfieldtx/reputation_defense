import json

import anthropic

from ..config import settings
from . import prompts
from .schemas import ReviewAnalysis


def _client() -> anthropic.Anthropic:
    kwargs = {"api_key": settings.anthropic_api_key}
    if settings.anthropic_base_url:
        kwargs["base_url"] = settings.anthropic_base_url
    return anthropic.Anthropic(**kwargs)


def _format_reviews(reviews: list[dict], limit: int = 150, max_chars: int = 400) -> str:
    lines = []
    for r in reviews[:limit]:
        text = (r.get("text") or "").replace("\n", " ")[:max_chars]
        lines.append(
            f"{r.get('rating', '?')}* | {str(r.get('date', ''))[:10]} | "
            f"{'responded' if r.get('owner_response') else 'NO RESPONSE'} | {text}"
        )
    return "\n".join(lines)


def _format_competitors(competitor_data: list[dict] | None) -> str:
    if not competitor_data:
        return ""
    blocks = []
    for c in competitor_data:
        p = c.get("profile", {})
        sample = _format_reviews(c.get("reviews", []), limit=20, max_chars=200)
        blocks.append(f"--- {p.get('name')} | {p.get('rating')}* | {p.get('reviews_count')} reviews\n{sample}")
    return "\n".join(blocks)


def _extract_json(text: str) -> dict:
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"no JSON object in model output: {text[:200]}")
    return json.loads(text[start : end + 1])


def analyze(business_name: str, vertical_label: str, metrics: dict,
            business_data: dict, competitor_data: list[dict] | None) -> dict:
    """One structured LLM pass over the reviews. Validates against ReviewAnalysis;
    retries once with the validation error before giving up."""
    prompt = prompts.analysis_prompt(
        business_name,
        vertical_label,
        metrics={k: v for k, v in metrics.items() if k != "competitor_velocity"},
        reviews_block=_format_reviews(business_data.get("reviews", [])),
        competitor_block=_format_competitors(competitor_data),
    )
    client = _client()
    messages = [{"role": "user", "content": prompt}]

    last_err = None
    for _ in range(2):
        response = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=4000,
            system=prompts.SYSTEM,
            messages=messages,
        )
        raw = response.content[0].text
        try:
            return ReviewAnalysis.model_validate(_extract_json(raw)).model_dump()
        except Exception as err:  # invalid JSON or schema mismatch -> one corrective retry
            last_err = err
            messages = messages + [
                {"role": "assistant", "content": raw},
                {"role": "user", "content": f"That output failed validation: {err}. "
                                            "Return ONLY the corrected JSON object."},
            ]
    raise RuntimeError(f"analysis failed validation twice: {last_err}")
