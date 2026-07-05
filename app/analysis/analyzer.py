import json

import httpx

from ..config import settings
from . import prompts
from .schemas import ReviewAnalysis


def _chat(messages: list[dict]) -> str:
    """OpenAI-compatible chat call (OpenRouter by default)."""
    resp = httpx.post(
        f"{settings.llm_base_url.rstrip('/')}/chat/completions",
        headers={
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "HTTP-Referer": "https://reputationdefense.local",
            "X-Title": "Reputation Defense",
        },
        json={
            "model": settings.llm_model,
            "max_tokens": 4000,
            "messages": [{"role": "system", "content": prompts.SYSTEM}] + messages,
        },
        timeout=300,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


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
    messages = [{"role": "user", "content": prompt}]

    last_err = None
    for _ in range(2):
        raw = _chat(messages)
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
