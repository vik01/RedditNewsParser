# Standard Library Imports
import sys
from typing import Dict, List
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

# Third Party Imports
from dotenv import dotenv_values
from openai import OpenAI

# Local Module Imports
from news_utils import (load_config, require_section,
                        require_str, require_int, resolve_repo_path)

# Load config variables
_cfg = load_config(project_root / "config.yaml")
_environment = require_section(_cfg, "environment")
_openrouter = require_section(_cfg, "openrouter")

ENVIRONMENT_PATH = resolve_repo_path(
    project_root, require_str(_environment, "environment_path"),
    ensure_parent=True)

# All environmental variables
env_config = dotenv_values(ENVIRONMENT_PATH)
OPENROUTER_API_KEY = env_config["OPENROUTER_API"]

# OpenRouter config
MODEL = require_str(_openrouter, "model")
MAX_TOKENS = require_int(_openrouter, "max_tokens")

# Constants
OPENROUTER_URL = "https://openrouter.ai/api/v1"
SYSTEM_PROMPT = (
    "You are a concise news analyst. Given a list of news headlines and "
    "descriptions from a specific country and category, write a brief "
    "summary (3-5 sentences) of the key themes and developments. "
    "Focus on the most important stories and any patterns across them. "
    "Do not list individual articles — synthesize them into a coherent overview."
)


def _group_by_country_category(
        articles: List[Dict]) -> Dict[str, Dict[str, List[Dict]]]:
    """
    Group articles into {country: {category: [articles]}}.

    Handles newsio articles where country/category are lists,
    and newsapiorg articles where they are strings.
    """
    grouped: Dict[str, Dict[str, List[Dict]]] = {}
    for article in articles:
        countries = article.get("country", [])
        categories = article.get("category", [])

        # Normalize to lists
        if isinstance(countries, str):
            countries = [countries]
        if isinstance(categories, str):
            categories = [categories]

        if not countries or not categories:
            continue

        for country in countries:
            for category in categories:
                if country not in grouped:
                    grouped[country] = {}
                if category not in grouped[country]:
                    grouped[country][category] = []
                grouped[country][category].append(article)

    return grouped


def _format_prompt(country: str, category: str,
                   articles: List[Dict]) -> str:
    """
    Build the user prompt from article titles and descriptions.

    Truncates descriptions to 200 characters to manage token usage.
    """
    lines = [f"Country: {country} | Category: {category}\n"]
    for i, article in enumerate(articles, 1):
        title = article.get("title", "No title")
        desc = article.get("description", "")
        if desc and len(desc) > 200:
            desc = desc[:200] + "..."
        lines.append(f"{i}. {title}")
        if desc:
            lines.append(f"   {desc}")
    return "\n".join(lines)


def _call_openrouter(client: OpenAI, prompt: str) -> str:
    """
    Send a prompt to the OpenRouter API and return the summary.
    """
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        max_tokens=MAX_TOKENS,
    )
    return response.choices[0].message.content


def summarize_group(articles: List[Dict], country: str,
                    category: str) -> str:
    """
    Summarize a single country/category group of articles.

    Formats the articles into a prompt and makes one OpenRouter call.

    Args:
        articles: List of article dicts already filtered to one
            country/category.
        country: Country name or code for the prompt.
        category: Category name for the prompt.

    Returns:
        The summary string from the model.
    """
    prompt = _format_prompt(country, category, articles)
    client = OpenAI(base_url=OPENROUTER_URL, api_key=OPENROUTER_API_KEY)
    try:
        return _call_openrouter(client, prompt)
    finally:
        client.close()


def summarize_all(articles: List[Dict]) -> Dict[str, Dict[str, str]]:
    """
    Summarize articles per country and per category.

    Groups all articles by country/category, then calls OpenRouter
    for each group to produce a short synthesis.

    Args:
        articles: Combined list of newsio + newsapiorg article dicts.

    Returns:
        {country: {category: "summary text"}}
    """
    grouped = _group_by_country_category(articles)
    summaries: Dict[str, Dict[str, str]] = {}

    client = OpenAI(base_url=OPENROUTER_URL, api_key=OPENROUTER_API_KEY)
    try:
        for country, categories in grouped.items():
            summaries[country] = {}
            for category, articles_list in categories.items():
                prompt = _format_prompt(country, category, articles_list)
                summary = _call_openrouter(client, prompt)
                summaries[country][category] = summary
    finally:
        client.close()

    return summaries
