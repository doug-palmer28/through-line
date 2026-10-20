"""Evaluation Specialist: a measurement and evaluation professional.

Checks that the logic model hangs together (every outcome traces to an
activity, outputs are countable, outcomes are measurable) and keeps the
measurement burden realistic for a small organization.
"""

from pydantic_ai import Agent

from agents.common import CONTEXT_TOOLS, TeamDeps, load_prompt
from models import SpecialistAdvice

evaluation_specialist = Agent(
    name="evaluation_specialist",
    deps_type=TeamDeps,
    output_type=SpecialistAdvice,
    instructions=load_prompt("evaluation_specialist"),
    tools=CONTEXT_TOOLS,
    retries=2,
)
