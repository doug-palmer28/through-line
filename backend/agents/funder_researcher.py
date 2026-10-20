"""Funder Researcher: what philanthropic and government funders in the client's field want to see.

Searches the web (OpenAI's built-in web search, through Portkey) for funder
reporting requirements, field-standard outcome measures, and how leading
organizations frame their logic models, then cites what it found.

Two safeguards keep citations honest:
  * `verified` is set here in code, never by the model: a source counts as
    verified only if its URL appeared in this run's actual web search results.
  * If live search isn't available (the model or gateway rejects it), the
    researcher falls back to its own knowledge, says so in the huddle, and every
    source is marked unverified with its URL removed (an unsearched URL may be
    invented).

It only ever searches for public, field-level information. Client documents
and answers never go into a search query (see the prompt).
"""

import json
import re
from typing import Any

from pydantic_ai import Agent
from pydantic_ai.capabilities.web_search import WebSearch
from pydantic_ai.exceptions import ModelHTTPError, UserError
from pydantic_ai.messages import NativeToolCallPart, NativeToolReturnPart

from agents.common import CONTEXT_TOOLS, MAX_WEB_SEARCHES, RESEARCH_LIMITS, TeamDeps, load_prompt, run_agent
from audit import audit_append
from models import Citation, SpecialistAdvice

funder_researcher = Agent(
    name="funder_researcher",
    deps_type=TeamDeps,
    output_type=SpecialistAdvice,  # research runs pass FieldResearch / MetricsResearch
    instructions=load_prompt("funder_researcher"),
    tools=CONTEXT_TOOLS,
    retries=2,
)

URL_RE = re.compile(r"https?://[^\s\"'<>)\]]+")
WEB_NOTE = ("\n\nYou have live web search. Search for public, field-level information only, never the client's "
            "name or anything they told us. Cite only pages that appeared in your search results, with their exact URL.")
KNOWLEDGE_NOTE = ("\n\nLive web search is NOT available. Use what you know. Name only sources you are confident exist, "
                  "set every url to null, and be explicit when something should be checked.")


def _unsupported(exc: Exception) -> bool:
    """True when the failure means 'web search isn't available here', not a general outage."""
    if isinstance(exc, UserError):
        return True
    if isinstance(exc, ModelHTTPError) and exc.status_code in (400, 404, 422):
        return True
    return "web_search" in str(exc).lower() or "not support" in str(exc).lower()


def _norm(url: str) -> str:
    return url.split("#")[0].split("?")[0].rstrip("/.,").lower().removeprefix("https://").removeprefix("http://").removeprefix("www.")


def _same_or_within(url: str, seen: str) -> bool:
    """Same page, or one page inside the other on a path boundary (example.org/a vs example.org/a/b),
    never a look-alike host (example.org vs example.org.evil.com)."""
    return url == seen or url.startswith(seen + "/") or seen.startswith(url + "/")


def _mark_sources(sources: list[Citation], seen_urls: set[str], mode: str) -> None:
    seen = {n for n in (_norm(u) for u in seen_urls) if "." in n.split("/")[0]}  # needs a real host
    for c in sources:
        if mode != "web":
            c.url = None
            c.verified = False
        else:
            url = _norm(c.url or "")
            c.verified = bool(url) and "." in url.split("/")[0] and any(_same_or_within(url, s) for s in seen)


async def research(output_type: Any, prompt: str, deps: TeamDeps, *, input_summary: str, activity: str) -> Any:
    """Run a research step with live web search, falling back to model knowledge if search is unavailable."""
    session = deps.session
    seen_urls: set[str] = set()
    queries: list[str] = []

    def collect(messages) -> None:
        for msg in messages:
            for part in getattr(msg, "parts", []):
                if isinstance(part, NativeToolCallPart):
                    args = part.args_as_dict() if hasattr(part, "args_as_dict") else {}
                    q = args.get("query") or (args.get("action") or {}).get("query") if isinstance(args, dict) else None
                    if q:
                        queries.append(str(q))
                elif isinstance(part, NativeToolReturnPart):
                    seen_urls.update(URL_RE.findall(json.dumps(part.content, default=str)))

    session.post("ask", "boss", activity, to="funder_researcher")
    output = None
    if session.research_mode != "knowledge":
        try:
            output = await run_agent(
                funder_researcher, "funder_researcher", prompt + WEB_NOTE, deps,
                output_type=output_type, limits=RESEARCH_LIMITS, activity=activity,
                capabilities=[WebSearch(max_uses=MAX_WEB_SEARCHES)],
                model_settings={"openai_include_web_search_sources": True},
                on_messages=collect, input_summary=input_summary + " (live web search)",
            )
            session.research_mode = "web"
        except Exception as exc:
            if not _unsupported(exc):
                raise
            session.research_mode = "knowledge"
            audit_append(event="research_fallback", run_id=deps.run_id, session_id=session.id, phase=deps.phase,
                         agent="funder_researcher", error=f"{type(exc).__name__}: {str(exc)[:300]}",
                         input_summary="live web search unavailable; using model knowledge, sources unverified")
            session.post("thinking", "funder_researcher",
                         "Live web search isn't available, so I'm using what I already know. "
                         "I'll mark every source 'unverified' so you can check it.")

    if output is None:
        output = await run_agent(
            funder_researcher, "funder_researcher", prompt + KNOWLEDGE_NOTE, deps,
            output_type=output_type, limits=RESEARCH_LIMITS, activity=activity,
            input_summary=input_summary + " (model knowledge)",
        )

    for q in queries[:MAX_WEB_SEARCHES]:
        session.post("look", "funder_researcher", f"Searched the web: {q}")
    _mark_sources(output.sources, seen_urls, session.research_mode)
    verified = sum(c.verified for c in output.sources)
    session.post("reply", "funder_researcher",
                 f"Found {len(output.sources)} sources ({verified} verified from live search).", to="boss")
    return output
