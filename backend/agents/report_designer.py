"""Report Designer: turns an organization's results into a funder deck and a one-page flyer (a reusable "shell").

Runs per organization (both gpt-6-luna, both audited), limited by allowances.py:
  1. design -> ReportDraft: a 10-14 slide story with speaker notes, a one-pager, and design settings
               interpreted from the org's design standards. Numbers are {{key}} tokens (figures.py), so the
               shell refreshes with new data without another AI call.
  2. revise -> ReportDraft: one round of staff feedback.
Each is followed by the Privacy Reviewer (agents/privacy_reviewer.py).
"""

from pydantic_ai import Agent
from pydantic_ai.usage import UsageLimits

from agents.common import TeamDeps, load_prompt

DESIGN_LIMITS = UsageLimits(request_limit=4, tool_calls_limit=2, total_tokens_limit=120_000)

report_designer = Agent(
    name="report_designer",
    deps_type=TeamDeps,
    instructions=load_prompt("report_designer"),
    retries=2,
)
