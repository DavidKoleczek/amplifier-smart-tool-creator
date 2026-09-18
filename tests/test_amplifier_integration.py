"""Opt-in real Agent, real loop and scripted provider. No credentials or model calls."""

import os
from pathlib import Path
from typing import Any

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("CREATOR_TEST_REAL_AGENT") != "1",
    reason="Set CREATOR_TEST_REAL_AGENT=1 to prepare Agent runtime modules and test offline.",
)


async def test_real_agent_submission_and_resume(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from amplifier_agent_cli import provider_sources
    from amplifier_agent_lib import __version__
    from amplifier_agent_lib.bundle.cache import load_and_prepare_cached
    from amplifier_core import ProviderInfo
    from amplifier_core.message_models import ChatResponse, TextBlock, ToolCall, ToolCallBlock
    from amplifier_foundation.bundle import PreparedBundle

    from smart_tool_creator.intelligence.amplifier_worker import run_agent
    from smart_tool_creator.intelligence.schemas import AgentRequest

    class Provider:
        name = "offline-test"

        def __init__(self) -> None:
            self.calls = 0
            self.history: list[Any] = []

        def get_info(self) -> Any:
            return ProviderInfo(id=self.name, display_name="Offline test")

        def get_supported_tools(self) -> list:
            return []

        def parse_tool_calls(self, response: Any) -> list:
            return response.tool_calls or []

        async def list_models(self) -> list:
            return []

        async def complete(self, request: Any, **kwargs: Any) -> Any:
            self.calls += 1
            self.history.append(request)
            assert {tool.name for tool in request.tools or []} == {"submit"}
            if self.calls in (1, 3):
                call = ToolCall(id=f"submit-{self.calls}", name="submit", arguments={"answer": 42})
                return ChatResponse(
                    content=[ToolCallBlock(id=call.id, name=call.name, input=call.arguments)], tool_calls=[call]
                )
            return ChatResponse(content=[TextBlock(text="done")])

    provider = Provider()
    original = PreparedBundle.create_session

    async def create(prepared: Any, **kwargs: Any) -> Any:
        session = await original(prepared, **kwargs)
        await session.coordinator.mount("providers", provider, name=provider.name)
        return session

    monkeypatch.setattr(PreparedBundle, "create_session", create)
    monkeypatch.setattr(provider_sources, "inject_provider", lambda *args, **kwargs: None)
    prepared = await load_and_prepare_cached(aaa_version=__version__)
    request = AgentRequest(
        prompt="Remember the marker apricot. Submit 42.",
        model="offline-model",
        timeout_seconds=90,
        output_schema={"type": "object", "properties": {"answer": {"type": "integer"}}, "required": ["answer"]},
    )
    payload = {
        "provider": "offline-test",
        "request": request.model_dump(mode="json"),
        "session_id": "real-agent",
        "state_directory": str(tmp_path),
    }
    result = await run_agent(payload, prepared)
    assert result.error is None
    assert result.output == {"answer": 42}
    request = request.model_copy(update={"resume": result.session_id, "prompt": "Continue and submit again."})
    payload["request"] = request.model_dump(mode="json")
    resumed = await run_agent(payload, prepared)
    assert resumed.error is None
    assert resumed.output == {"answer": 42}
    assert provider.calls == 4
    assert "apricot" in str(provider.history[2].messages)
