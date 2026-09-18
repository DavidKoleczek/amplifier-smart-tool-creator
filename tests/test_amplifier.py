"""Adapter contracts, without credentials or model requests."""

from concurrent.futures import ThreadPoolExecutor
from importlib.metadata import PackageNotFoundError
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any

import pytest
from typer.testing import CliRunner

from smart_tool_creator import lib
from smart_tool_creator.cli import app
from smart_tool_creator.intelligence import amplifier
from smart_tool_creator.intelligence.amplifier import AmplifierIntelligence
from smart_tool_creator.intelligence.schemas import AgentRequest, AgentResult, HostWorkspace
from smart_tool_creator.schemas import SmartToolCreatorError


def request(**kwargs: Any) -> AgentRequest:
    return AgentRequest(prompt="Test", model="explicit-model", timeout_seconds=5, **kwargs)


def test_factory_is_lazy_and_preserves_host_environment() -> None:
    code = """
import os, sys
os.environ['AMPLIFIER_HOME'] = 'host-value'
from smart_tool_creator import lib
agent = lib.create_intelligence('amplifier-agent', provider='ollama')
lib.load_manifest()
lib.skill()
assert os.environ['AMPLIFIER_HOME'] == 'host-value'
assert not any(n.startswith('amplifier_agent_') for n in sys.modules)
"""
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert lib.create_intelligence().implementation.startswith("copilot-sdk")


def test_missing_extra_and_provider_have_remedies(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing(name: str) -> str:
        raise PackageNotFoundError(name)

    monkeypatch.setattr(amplifier, "version", missing)
    with pytest.raises(SmartToolCreatorError, match="extra"):
        AmplifierIntelligence().preflight()
    monkeypatch.setattr(amplifier, "version", lambda _: "0.17.0")
    with pytest.raises(SmartToolCreatorError, match="explicit provider"):
        AmplifierIntelligence().preflight()
    with pytest.raises(SmartToolCreatorError, match="without --provider"):
        lib.create_intelligence("copilot-sdk", provider="ollama")


def test_resume_scope_and_serialization(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    agent = AmplifierIntelligence("ollama")
    running = 0
    maximum = 0
    payloads: list[dict] = []

    def worker(payload: dict, timeout: float, session_id: str | None = None) -> AgentResult:
        nonlocal running, maximum
        running += 1
        maximum = max(maximum, running)
        time.sleep(0.01)
        payloads.append(payload)
        running -= 1
        return AgentResult(text="ok", session_id=session_id)

    monkeypatch.setattr(agent, "_worker", worker)
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(agent.run, [request()] * 3))
    assert maximum == 1
    resumed = agent.run(request(resume=results[0].session_id))
    assert resumed.session_id == results[0].session_id
    assert payloads[-1]["request"]["resume"] == resumed.session_id
    refused = agent.run(request(resume=resumed.session_id, workspace=HostWorkspace(path=tmp_path)))
    assert refused.error
    assert "changed workspace" in refused.error
    assert agent.run(request(resume="unknown")).error


@pytest.mark.parametrize("failure", ["timeout", "bad-json", "crash"])
def test_worker_failures_are_data(monkeypatch: pytest.MonkeyPatch, failure: str) -> None:
    class Process:
        pid = 99999999
        returncode = 1 if failure == "crash" else 0

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def __enter__(self) -> Any:
            return self

        def __exit__(self, *args: Any) -> None:
            pass

        def communicate(self, *args: Any, **kwargs: Any) -> tuple[str, str]:
            if failure == "timeout":
                raise subprocess.TimeoutExpired("worker", 1)
            return "invalid", ""

        def poll(self) -> int:
            return self.returncode

        def wait(self) -> int:
            return self.returncode

    monkeypatch.setattr(subprocess, "Popen", Process)
    result = AmplifierIntelligence("ollama").run(request())
    assert result.error
    assert result.session_id


def test_cli_selection_and_deterministic_help(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, Any] = {}

    def review(**kwargs: Any) -> Any:
        seen.update(kwargs)
        from types import SimpleNamespace

        return SimpleNamespace(output_message="ok", conformance=SimpleNamespace(verdict="PASS"), deviating=[])

    monkeypatch.setattr(lib, "check_spec_adherence", review)
    runner = CliRunner()
    result = runner.invoke(
        app, ["check-spec-adherence", "--backend", "amplifier-agent", "--provider", "ollama", "--model", "my-model"]
    )
    assert result.exit_code == 0, result.output
    assert seen["model"] == "my-model"
    assert seen["intelligence"].provider == "ollama"
    missing = runner.invoke(app, ["check-spec-adherence", "--backend", "amplifier-agent"])
    assert isinstance(missing.exception, SmartToolCreatorError)
    for args in (["manifest"], ["--help"], ["init", "--help"], ["check-spec-adherence", "--help"]):
        assert runner.invoke(app, args).exit_code == 0


def test_preflight_worker_rejects_unknown_provider_without_touching_host() -> None:
    pytest.importorskip("amplifier_agent_cli.provider_sources")
    before = dict(os.environ)
    with pytest.raises(SmartToolCreatorError, match="Unknown provider"):
        AmplifierIntelligence("not-a-provider").preflight()
    assert dict(os.environ) == before


def test_preflight_missing_credentials_names_remedy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("amplifier_agent_cli.provider_sources")
    monkeypatch.setenv("AMPLIFIER_AGENT_HOME", str(tmp_path))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AMPLIFIER_ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(SmartToolCreatorError, match="Configure credentials"):
        AmplifierIntelligence("anthropic").preflight()


@pytest.mark.parametrize(
    ("provider", "remedy"),
    [
        ("openai-chatgpt", "OAuth device-code login"),
        ("chat-completions", "CHAT_COMPLETIONS_BASE_URL"),
        ("vllm", "VLLM_BASE_URL"),
    ],
)
def test_unconfigured_providers_fail_before_running(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, provider: str, remedy: str
) -> None:
    pytest.importorskip("amplifier_agent_cli.provider_sources")
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("AMPLIFIER_AGENT_HOME", str(tmp_path / "agent"))
    for variable in ("CHAT_COMPLETIONS_BASE_URL", "CHAT_COMPLETIONS_API_KEY", "VLLM_BASE_URL", "VLLM_API_KEY"):
        monkeypatch.delenv(variable, raising=False)
    agent = AmplifierIntelligence(provider)
    with pytest.raises(SmartToolCreatorError, match=remedy):
        agent.preflight()
    result = agent.run(request())
    assert result.error
    assert remedy in result.error
    if provider == "openai-chatgpt":
        assert "Interactive login is disabled" in result.error


def test_ollama_default_host_passes_preflight(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("amplifier_agent_cli.provider_sources")
    monkeypatch.setenv("AMPLIFIER_AGENT_HOME", str(tmp_path))
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    AmplifierIntelligence("ollama").preflight()


@pytest.mark.parametrize(
    ("provider", "variable"), [("chat-completions", "CHAT_COMPLETIONS_BASE_URL"), ("vllm", "VLLM_BASE_URL")]
)
def test_keyless_configured_endpoint_passes_preflight(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, provider: str, variable: str
) -> None:
    pytest.importorskip("amplifier_agent_cli.provider_sources")
    monkeypatch.setenv("AMPLIFIER_AGENT_HOME", str(tmp_path))
    monkeypatch.setenv(variable, "http://127.0.0.1:1/v1")
    monkeypatch.delenv("CHAT_COMPLETIONS_API_KEY", raising=False)
    monkeypatch.delenv("VLLM_API_KEY", raising=False)
    AmplifierIntelligence(provider).preflight()


def test_worker_hard_timeout_reaps_process(monkeypatch: pytest.MonkeyPatch) -> None:
    original = subprocess.Popen
    processes: list[Any] = []

    def launch(command: list[str], **kwargs: Any) -> Any:
        process = original([sys.executable, "-c", "import time; time.sleep(30)"], **kwargs)
        processes.append(process)
        return process

    monkeypatch.setattr(subprocess, "Popen", launch)
    result = AmplifierIntelligence("ollama")._worker({}, timeout=0.1, session_id="timed-out")
    assert result.error
    assert "timeout" in result.error
    assert result.session_id == "timed-out"
    assert processes[0].poll() is not None


def test_queue_timeout_does_not_start_worker(monkeypatch: pytest.MonkeyPatch) -> None:
    agent = AmplifierIntelligence("ollama")
    agent._lock.acquire()
    try:
        result = agent.run(AgentRequest(prompt="Test", model="model", timeout_seconds=1))
        assert result.error
        assert "waiting" in result.error
    finally:
        agent._lock.release()
