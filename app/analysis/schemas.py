"""Pydantic schemas the LLM output must validate against before it reaches a report."""

from pydantic import BaseModel, Field


class SentimentCluster(BaseModel):
    label: str = Field(description="Short theme name, e.g. 'Wait times'")
    sentiment: str = Field(description="'positive' or 'negative'")
    share_pct: float = Field(ge=0, le=100, description="Approx % of same-sentiment reviews mentioning this theme")
    summary: str
    quotes: list[str] = Field(min_length=1, max_length=3, description="Verbatim excerpts from real reviews")


class SpamSuspect(BaseModel):
    excerpt: str
    author: str = ""
    reasons: list[str]


class Fix(BaseModel):
    title: str
    why: str
    impact: str = Field(description="'high', 'medium' or 'low'")


class ReviewAnalysis(BaseModel):
    executive_summary: str
    overall_sentiment: str = Field(description="One-sentence overall read of the review base")
    clusters: list[SentimentCluster] = Field(min_length=2, max_length=8)
    spam_suspects: list[SpamSuspect] = Field(default_factory=list, max_length=10)
    top_fixes: list[Fix] = Field(min_length=3, max_length=5)
    competitor_takeaway: str = ""
