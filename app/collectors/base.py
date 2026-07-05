"""Collector contract. Any source (Outscraper today; Yelp/Facebook later) must return:

{
  "profile": {"name": str, "rating": float, "reviews_count": int,
              "address": str, "category": str},
  "reviews": [
    {"author": str, "rating": int, "text": str, "date": iso8601,
     "owner_response": str|None, "owner_response_date": iso8601|None},
    ...
  ]
}
"""

from typing import Protocol


class Collector(Protocol):
    def collect(self, business_name: str, city: str, max_reviews: int) -> dict: ...
