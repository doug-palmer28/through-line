"""Grant Writer: drafts a grant application tailored to one foundation, using the organization's live data.

One application = (allowances.py: 3 new applications per month per organization)
  1. Funder Researcher -> FoundationProfile (live web search + the foundation's site; citations verified in code)
  2. Grant Writer      -> GrantDraft (answers per question, numbers as {{key}} tokens, checklist, needs-input list)
  3. Privacy Reviewer  -> fixes applied, then the code scan
plus one feedback round (Grant Writer + Privacy Reviewer again).
"""

from pydantic_ai import Agent
from pydantic_ai.usage import UsageLimits

from agents.common import TeamDeps, load_prompt

WRITER_LIMITS = UsageLimits(request_limit=4, tool_calls_limit=2, total_tokens_limit=150_000)

grant_writer = Agent(
    name="grant_writer",
    deps_type=TeamDeps,
    instructions=load_prompt("grant_writer"),
    retries=2,
)
