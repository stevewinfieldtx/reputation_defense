SYSTEM = """You are a reputation analyst producing input for a paid audit report read by a \
small-business owner. Be concrete, evidence-driven and blunt. Every claim must be \
supported by the reviews provided. Quotes must be verbatim excerpts (trim with ... if \
long), never paraphrased or invented. Do not flatter; the owner is paying to hear \
what is wrong and what to do about it."""


def analysis_prompt(business_name: str, vertical_label: str, metrics: dict,
                    reviews_block: str, competitor_block: str) -> str:
    return f"""Analyze the customer reviews for **{business_name}** ({vertical_label}).

Pre-computed statistics (trust these, do not recompute):
{metrics}

REVIEWS (rating | date | has_owner_response | text):
{reviews_block}

COMPETITOR SNAPSHOT:
{competitor_block or "none provided"}

Return ONLY a JSON object with this exact shape (no markdown fence, no commentary):
{{
  "executive_summary": "3-5 sentences: overall reputation position, the single biggest problem, the single biggest strength, and what it is costing them.",
  "overall_sentiment": "one sentence",
  "clusters": [
    {{"label": "...", "sentiment": "positive|negative", "share_pct": 0-100,
      "summary": "1-2 sentences", "quotes": ["verbatim excerpt", "..."]}}
  ],
  "spam_suspects": [
    {{"excerpt": "...", "author": "...", "reasons": ["generic text", "review burst", "no detail", ...]}}
  ],
  "top_fixes": [
    {{"title": "imperative action", "why": "grounded in the evidence above", "impact": "high|medium|low"}}
  ],
  "competitor_takeaway": "1-2 sentences on what competitors are doing better/worse, or empty string"
}}

Rules:
- 2-8 clusters covering BOTH negative and positive themes; share_pct is the share of same-sentiment reviews touching the theme.
- Only list spam_suspects with genuinely suspicious patterns; an empty list is fine.
- 3-5 top_fixes, ordered by impact; at least one must address the response gap if the stats show one.
"""
