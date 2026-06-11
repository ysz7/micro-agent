"""Phase 4: REPL conversation memory — threading message_history between turns.

Mirrors exactly what ``__main__._repl`` does (extend ``history`` with
``result.new_messages()``, pass ``message_history=history`` on the next turn),
using a FunctionModel that recalls a name only if it can see the earlier turn.
"""

from pydantic_ai import Agent
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.messages import ModelResponse, TextPart


def _memory_model(messages, info: AgentInfo) -> ModelResponse:
    """Reply with the remembered name, scanning the whole message history."""
    name = "unknown"
    for m in messages:
        for part in getattr(m, "parts", []):
            content = getattr(part, "content", "")
            if isinstance(content, str) and "my name is" in content.lower():
                name = content.lower().split("my name is", 1)[1].strip().split()[0]
    return ModelResponse(parts=[TextPart(name)])


def test_repl_remembers_across_turns():
    agent = Agent(FunctionModel(_memory_model))
    history: list = []

    r1 = agent.run_sync("my name is alice", message_history=history)
    history.extend(r1.new_messages())

    # Turn 2 sees turn 1 through message_history → recalls the name.
    r2 = agent.run_sync("what is my name?", message_history=history)
    assert "alice" in r2.output.lower()
    history.extend(r2.new_messages())


def test_clear_forgets_history():
    agent = Agent(FunctionModel(_memory_model))
    history: list = []

    r1 = agent.run_sync("my name is bob", message_history=history)
    history.extend(r1.new_messages())

    history.clear()  # what /clear does

    r2 = agent.run_sync("what is my name?", message_history=history)
    assert r2.output == "unknown"


def test_history_cap_keeps_last_n():
    """The REPL's bound: del history[:-keep] keeps only the last *keep* messages."""
    history = list(range(100))
    keep = 40
    if len(history) > keep:
        del history[:-keep]
    assert history == list(range(60, 100))
