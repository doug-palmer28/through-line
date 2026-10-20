"""Sector Expert: subject-matter expert in the client's field.

At intake it builds a SectorBrief (best practices, standards, common outcomes
and metrics for this field), which becomes the team's knowledge base for the
rest of the session. Afterwards it answers the boss's questions using it.
The brief lives only in the session's memory.
"""

from pydantic_ai import Agent

from agents.common import CONTEXT_TOOLS, TeamDeps, load_prompt
from models import SpecialistAdvice

sector_expert = Agent(
    name="sector_expert",
    deps_type=TeamDeps,
    output_type=SpecialistAdvice,  # run with output_type=SectorBrief to build the brief
    instructions=load_prompt("sector_expert"),
    tools=CONTEXT_TOOLS,
    retries=2,
)
