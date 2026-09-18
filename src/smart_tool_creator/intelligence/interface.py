"""The contract every model-backed capability runs through, so the implementation is swappable."""

from typing import Protocol

from smart_tool_creator.intelligence.schemas import AgentRequest, AgentResult
from smart_tool_creator.schemas import IntelligenceLayer, SmartToolCreatorError


class Intelligence(Protocol):
    """Runs agents against models; the library depends on this contract, never on an SDK."""

    implementation: str

    def preflight(self) -> None:
        """Raise SmartToolCreatorError naming exactly what to configure when the implementation cannot run."""
        ...

    def run(self, request: AgentRequest) -> AgentResult:
        """Run one agent to completion.

        When the request carries an output schema, the result either holds a conforming
        `output` or an `error`; retry mechanics are the implementation's own business.
        """
        ...


def default_intelligence(backend: IntelligenceLayer = "copilot-sdk", provider: str | None = None) -> Intelligence:
    if backend == "amplifier-agent":
        from smart_tool_creator.intelligence.amplifier import AmplifierIntelligence

        return AmplifierIntelligence(provider=provider)
    if backend != "copilot-sdk" or provider is not None:
        raise SmartToolCreatorError("Choose copilot-sdk without --provider, or amplifier-agent with --provider.")
    from smart_tool_creator.intelligence.copilot import CopilotIntelligence

    return CopilotIntelligence()
