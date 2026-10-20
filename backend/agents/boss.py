"""Team Lead (the boss): the only agent that talks with the client.

It reads the client's materials, runs the five-question interview, drafts and
revises the logic model, and consults the three specialists through the
`consult` tool. How many consults it gets is set per phase (CONSULT_BUDGET);
when the budget is spent, the tool refuses and the boss must wrap up.
"""

from pydantic_ai import Agent, RunContext

from agents.client_advocate import client_advocate
from agents.common import CONTEXT_TOOLS, SPECIALIST_LIMITS, TeamDeps, load_prompt, run_agent
from agents.evaluation_specialist import evaluation_specialist
from agents.funder_researcher import funder_researcher
from agents.sector_expert import sector_expert
from audit import audit_append
from config import MODEL_NAME
from models import DraftResult, Specialist, SpecialistAdvice

SPECIALISTS: dict[str, Agent] = {
    "evaluation_specialist": evaluation_specialist,
    "client_advocate": client_advocate,
    "sector_expert": sector_expert,
    "funder_researcher": funder_researcher,
}

boss = Agent(
    name="boss",
    deps_type=TeamDeps,
    output_type=DraftResult,  # each phase passes its own output_type at run time
    instructions=load_prompt("boss"),
    tools=CONTEXT_TOOLS,
    retries=2,
)


@boss.tool
async def consult(ctx: RunContext[TeamDeps], specialist: Specialist, question: str) -> SpecialistAdvice | str:
    """Ask one specialist for advice and get a short structured answer back.

    Args:
        specialist: evaluation_specialist (measurement and logic), client_advocate
            (the org's perspective, capacity, and the people it serves),
            sector_expert (best practices and standards in this field), or
            funder_researcher (what funders want; uses its research, no new searches).
        question: Exactly what you need from them, with any facts they should
            weigh. They can also read the snapshot, interview, brief, and draft.
    """
    deps = ctx.deps
    if deps.consults_left <= 0:
        audit_append(
            event="limit_reached", run_id=deps.run_id, session_id=deps.session.id, step_id=deps.step_id,
            phase=deps.phase, agent="boss", model=MODEL_NAME,
            input_summary=f"consult budget spent; refused {specialist}",
        )
        deps.session.post("thinking", "boss", "Consult budget used up for this step. Wrapping up with what we have.")
        return "Refused: no consults left in this phase. Work with what you have and finish."
    deps.consults_left -= 1
    deps.session.post("ask", "boss", question, to=specialist)
    audit_append(
        event="handoff", run_id=deps.run_id, session_id=deps.session.id, step_id=deps.step_id,
        phase=deps.phase, agent="boss", model=MODEL_NAME,
        input_summary=f"boss -> {specialist}: {question[:300]}",
    )
    advice = await run_agent(
        SPECIALISTS[specialist], specialist, question, deps,
        input_summary=f"question from boss: {question[:300]}", limits=SPECIALIST_LIMITS,
    )
    deps.consult_log.append({"specialist": specialist, "question": question, "summary": advice.summary})
    reply = advice.summary + (f" Suggests: {advice.recommendations[0]}" if advice.recommendations else "")
    deps.session.post("reply", specialist, reply, to="boss")
    return advice
