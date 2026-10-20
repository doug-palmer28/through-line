"""Survey Review Bot: checks a survey tool before it goes out.

Reviews wording, scale consistency, whether the questions will produce useful
insight for the logic model's outcomes, burden, and sensitivity. Every
suggestion it can express as a concrete change comes with a one-click `fix`
that staff can choose to apply. It never edits a survey itself.
"""

from pydantic_ai import Agent
from pydantic_ai.usage import UsageLimits

from agents.common import TeamDeps, load_prompt
from models import SurveyReviewResult

REVIEW_LIMITS = UsageLimits(request_limit=3, tool_calls_limit=2, total_tokens_limit=60_000)

survey_reviewer = Agent(
    name="survey_reviewer",
    deps_type=TeamDeps,
    output_type=SurveyReviewResult,
    instructions=load_prompt("survey_reviewer"),
    retries=2,
)
