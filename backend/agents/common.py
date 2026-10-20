"""Shared plumbing for every agent: the model, prompts, run context, budgets, and audited runs."""

import hashlib
import os
import uuid
from dataclasses import dataclass, field
from functools import cache
from typing import Any

from openai import AsyncOpenAI
from pydantic_ai import Agent, RunContext, capture_run_messages
from pydantic_ai.messages import ModelResponse, ToolCallPart, ToolReturnPart
from pydantic_ai.models import Model
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.usage import UsageLimits

import ledger
import privacy
from audit import audit_append
from config import BACKEND_DIR, MODEL_NAME
from sessions import Session

PROMPTS_DIR = BACKEND_DIR / "prompts"

# ============================================================ token budgets ("tokenomics")
#
# Every run has hard caps. Hitting one stops the run with an error that is
# logged as `limit_reached` instead of letting a loop run on.

BOSS_LIMITS = UsageLimits(request_limit=10, tool_calls_limit=12, total_tokens_limit=150_000)
SPECIALIST_LIMITS = UsageLimits(request_limit=4, tool_calls_limit=10, total_tokens_limit=40_000)
# The researcher may run several web searches inside one request, so it gets more room.
RESEARCH_LIMITS = UsageLimits(request_limit=6, tool_calls_limit=12, total_tokens_limit=120_000)
MAX_WEB_SEARCHES = 6  # per research run

# Optional consults the boss may make in each phase. Required collaboration
# (question proposals, peer-review rounds, research) is run by the orchestrator
# and doesn't count against this.
CONSULT_BUDGET = {"intake": 0, "interview": 1, "absorb": 0, "draft": 1, "revise": 2, "metrics": 1, "metrics_revise": 2}


# ============================================================ the model


@cache
def team_model() -> OpenAIResponsesModel:
    """gpt-6-luna through the Portkey gateway, on the Responses API.

    gpt-6-luna rejects function tools on /v1/chat/completions, and the boss
    depends on tools, so every agent uses /v1/responses.
    """
    key = os.environ.get("PORTKEY_API_KEY")
    if not key:
        raise RuntimeError("PORTKEY_API_KEY is not set. Add it to .env (see .env.example).")
    client = AsyncOpenAI(
        api_key=key,
        base_url=os.getenv("PORTKEY_BASE_URL", "https://api.portkey.ai/v1"),
        default_headers={"x-portkey-api-key": key, "x-portkey-provider": "openai"},
    )
    return OpenAIResponsesModel(MODEL_NAME, provider=OpenAIProvider(openai_client=client))


# Tests set this to a pydantic-ai TestModel/FunctionModel so no live calls are made.
MODEL_OVERRIDE: Model | None = None


def get_model() -> Model:
    return MODEL_OVERRIDE or team_model()


# ============================================================ prompts


def prompt_file(name: str) -> str:
    return f"backend/prompts/{name}.md"


def load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")


def prompt_hash(name: str) -> str:
    return hashlib.sha256(load_prompt(name).encode()).hexdigest()[:12]


# ============================================================ run context


@dataclass
class TeamDeps:
    """Handed to every agent run. The session is the only data an agent can reach."""

    session: Session
    run_id: str
    phase: str
    step_id: str = ""
    consults_left: int = 0
    consult_log: list[dict] = field(default_factory=list)


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


# ============================================================ audited runs


def _short(value: Any, limit: int = 400) -> str:
    text = value.model_dump_json() if hasattr(value, "model_dump_json") else str(value)
    return text if len(text) <= limit else text[:limit] + "…"


def _tool_calls(messages) -> list[dict]:
    calls: dict[str, dict] = {}
    for msg in messages:
        for part in getattr(msg, "parts", []):
            if isinstance(part, ToolCallPart) and not part.tool_name.startswith("final_result"):
                calls[part.tool_call_id] = {"tool": part.tool_name, "args": part.args_as_dict()}
            elif isinstance(part, ToolReturnPart) and part.tool_call_id in calls:
                calls[part.tool_call_id]["result_summary"] = _short(part.content, 300)
    return list(calls.values())


def _usage_of(messages) -> dict[str, int]:
    """Tokens used by the model responses in a run (for runs that failed before returning a result)."""
    responses = [m for m in messages if isinstance(m, ModelResponse)]
    return {"requests": len(responses),
            "input_tokens": sum(m.usage.input_tokens or 0 for m in responses),
            "output_tokens": sum(m.usage.output_tokens or 0 for m in responses)}


def _dump(output: Any) -> Any:
    """What the audit log keeps of an agent's output. Structured outputs stay auditable, but:
    the exact text a privacy check flagged is never kept, and contact details or codes are scrubbed."""
    data = output.model_dump(mode="json") if hasattr(output, "model_dump") else output
    if isinstance(data, dict) and "findings" in data and "clean" in data:  # a PrivacyReview
        data = {**data, "findings": [{"where": f.get("where"), "issue": f.get("issue"), "text": "[withheld]",
                                      "replacement": "[withheld]"} for f in data.get("findings", [])]}
    return privacy.redact_tree(data)


async def run_agent(
    agent: Agent,
    name: str,
    prompt: str,
    deps: TeamDeps,
    *,
    input_summary: str,
    output_type: Any = None,
    limits: UsageLimits,
    activity: str | None = None,
    capabilities: list | None = None,
    model_settings: dict | None = None,
    on_messages=None,
) -> Any:
    """Run one agent loop and audit it: started, finished (with tool calls, output, tokens) or failed.

    `activity` is a plain-language line for the live team feed ("Reading your materials").
    `capabilities` / `model_settings` are per-run extras (the researcher's web search).
    `on_messages` receives the run's new messages (e.g. to read web search results).
    """
    parent = deps.step_id or None
    step_deps = TeamDeps(
        session=deps.session, run_id=deps.run_id, phase=deps.phase,
        step_id=new_id(name), consults_left=deps.consults_left, consult_log=deps.consult_log,
    )
    base = dict(
        run_id=deps.run_id, session_id=deps.session.id, step_id=step_deps.step_id, parent_step_id=parent,
        phase=deps.phase, agent=name, model=MODEL_NAME, prompt_file=prompt_file(name), prompt_hash=prompt_hash(name),
    )
    audit_append(event="agent_started", input_summary=input_summary, **base)
    if activity:
        deps.session.post("thinking", name, activity)

    kwargs: dict[str, Any] = {"output_type": output_type} if output_type is not None else {}
    if capabilities:
        kwargs["capabilities"] = capabilities
    if model_settings:
        kwargs["model_settings"] = model_settings
    s = deps.session
    ledger_base = dict(org_id=s.org_id, user_id=s.actor_id, feature=s.feature, phase=deps.phase, agent=name,
                       run_id=deps.run_id)
    with capture_run_messages() as messages:
        try:
            result = await agent.run(prompt, deps=step_deps, model=get_model(), usage_limits=limits, **kwargs)
        except Exception as exc:
            deps.session.post("error", name, "Ran into a problem and stopped.")
            event = "limit_reached" if "Limit" in type(exc).__name__ else "agent_failed"
            spent = _usage_of(messages)  # a failed run still used tokens
            deps.session.add_usage(spent)
            ledger.record(**ledger_base, usage=spent, ok=False)
            audit_append(event=event, tool_calls=_tool_calls(messages), error=f"{type(exc).__name__}: {exc}",
                         usage=spent, **base)
            raise

    # The boss's consult budget is spent inside this run; carry it back to the caller.
    deps.consults_left = step_deps.consults_left
    run_usage = result.usage
    usage = {
        "requests": run_usage.requests,
        "input_tokens": run_usage.input_tokens or 0,
        "output_tokens": run_usage.output_tokens or 0,
    }
    deps.session.add_usage(usage)
    ledger.record(**ledger_base, usage=usage)
    new = result.new_messages()
    if on_messages:
        on_messages(new)
    audit_append(
        event="agent_finished", tool_calls=_tool_calls(new), output=_dump(result.output), usage=usage,
        input_summary=f"{sum(isinstance(m, ModelResponse) for m in new)} model responses", **base,
    )
    return result.output


# ============================================================ read-only context tools
#
# Shared by the boss and the specialists. They read only the current session,
# so an agent can never see another client's information.


def _agent_of(ctx: RunContext[TeamDeps]) -> str:
    return ctx.deps.step_id.rsplit("-", 1)[0] or "boss"


def _look(ctx: RunContext[TeamDeps], what: str) -> None:
    ctx.deps.session.post("look", _agent_of(ctx), what)


def get_org_snapshot(ctx: RunContext[TeamDeps]) -> str:
    """What the team knows about the client organization so far."""
    _look(ctx, "Reviewed what we know about your organization")
    snap = ctx.deps.session.snapshot
    return snap.model_dump_json(indent=1) if snap else "No snapshot yet."


def get_interview(ctx: RunContext[TeamDeps]) -> str:
    """The interview questions asked so far, the client's answers, and the team's notes."""
    _look(ctx, "Re-read your interview answers")
    return ctx.deps.session.interview_text()


def get_sector_brief(ctx: RunContext[TeamDeps]) -> str:
    """The Sector Expert's brief on best practices, standards, and common outcomes in the client's field."""
    _look(ctx, "Checked the field's best practices and standards")
    brief = ctx.deps.session.sector_brief
    return brief.model_dump_json(indent=1) if brief else "No sector brief yet."


def get_current_draft(ctx: RunContext[TeamDeps]) -> str:
    """The latest logic model (approved version if there is one, otherwise the latest draft)."""
    _look(ctx, "Looked over the logic model")
    s = ctx.deps.session
    model = s.approved or s.current_draft
    return model.model_dump_json(indent=1) if model else "No draft yet."


def get_measurement_plan(ctx: RunContext[TeamDeps]) -> str:
    """The latest measurement plan draft (metrics, questions, scales, tools), if there is one."""
    _look(ctx, "Looked over the measurement plan")
    plan = ctx.deps.session.current_plan
    return plan.model_dump_json(indent=1) if plan else "No measurement plan yet."


def get_field_research(ctx: RunContext[TeamDeps]) -> str:
    """The Funder Researcher's findings: what funders in this field want measured, how leading organizations
    frame their outcomes, and the sources (cite them by id, e.g. [S2])."""
    _look(ctx, "Checked what funders in this field look for")
    r = ctx.deps.session.field_research
    return r.model_dump_json(indent=1) if r else "No field research yet."


def get_metrics_research(ctx: RunContext[TeamDeps]) -> str:
    """The Funder Researcher's suggested measures and question items for this logic model, with sources."""
    _look(ctx, "Checked the researched measures and questions")
    r = ctx.deps.session.metrics_research
    return r.model_dump_json(indent=1) if r else "No metrics research yet."


def get_question_pool(ctx: RunContext[TeamDeps]) -> str:
    """Interview questions the specialists proposed. Draw from these when choosing the next question."""
    _look(ctx, "Looked at the questions the team proposed")
    pool = ctx.deps.session.question_pool
    if not pool:
        return "No proposed questions."
    return "\n".join(f"- ({q['specialist']}) {q['question']} [why: {q['why']}]" for q in pool)


CONTEXT_TOOLS = [
    get_org_snapshot, get_interview, get_sector_brief, get_field_research, get_question_pool,
    get_current_draft, get_measurement_plan, get_metrics_research,
]
