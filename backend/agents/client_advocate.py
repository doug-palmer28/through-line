"""Client Advocate: speaks for the client organization.

Keeps the work grounded in what this nonprofit actually does, in its own
words, at its real capacity, and with the people it serves in view.
"""

from pydantic_ai import Agent

from agents.common import CONTEXT_TOOLS, TeamDeps, load_prompt
from models import SpecialistAdvice

client_advocate = Agent(
    name="client_advocate",
    deps_type=TeamDeps,
    output_type=SpecialistAdvice,
    instructions=load_prompt("client_advocate"),
    tools=CONTEXT_TOOLS,
    retries=2,
)
