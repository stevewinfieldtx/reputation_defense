from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATES = Path(__file__).resolve().parent / "templates"

env = Environment(
    loader=FileSystemLoader(TEMPLATES),
    autoescape=select_autoescape(["html"]),
)


def _money(value) -> str:
    try:
        return f"${value:,.0f}"
    except (TypeError, ValueError):
        return "$0"


env.filters["money"] = _money


def render(template_name: str, **context) -> str:
    return env.get_template(template_name).render(**context)
