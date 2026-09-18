"""Amplifier Agent adapter, with each run embedded in an isolated worker process."""

import contextlib
from importlib.metadata import PackageNotFoundError, version
import json
import os
import signal
import subprocess
import sys
from tempfile import TemporaryDirectory
from threading import Lock
import time
from typing import Any
from uuid import uuid4

from smart_tool_creator.intelligence.schemas import AgentRequest, AgentResult
from smart_tool_creator.schemas import SmartToolCreatorError


class AmplifierIntelligence:
    """Keep transcripts for this adapter's lifetime; serialize calls and isolate SDK globals."""

    def __init__(self, provider: str | None = None) -> None:
        self.implementation = "amplifier-agent 0.17.0"
        self.provider = provider
        self._state = TemporaryDirectory(prefix="smart-tool-agent-")
        self._lock = Lock()
        self._sessions: dict[str, tuple[str | None, bool]] = {}

    def preflight(self) -> None:
        try:
            installed = version("amplifier-agent")
        except PackageNotFoundError as error:
            raise SmartToolCreatorError(
                "Amplifier Agent is not installed. Install this tool's amplifier extra: `uv sync --extra amplifier` "
                "(or reinstall with `[amplifier]` in the package requirement)."
            ) from error
        if installed != "0.17.0":
            raise SmartToolCreatorError(
                f"Amplifier Agent {installed} is not supported; sync the pinned v0.17.0 dependency."
            )
        if not self.provider:
            raise SmartToolCreatorError("Amplifier Agent needs an explicit provider. Pass --provider or provider=.")
        result = self._worker({"provider": self.provider, "preflight": True}, 30)
        if result.error:
            raise SmartToolCreatorError(result.error)

    def run(self, request: AgentRequest) -> AgentResult:
        # Agent mutates process-global state. A thread-local event loop is not isolation.
        # Serializing also protects resume transcripts and avoids concurrent cache preparation.
        started = time.monotonic()
        if not self._lock.acquire(timeout=request.timeout_seconds):
            return AgentResult(
                error="Timed out waiting for another Amplifier run to finish.", session_id=request.resume
            )
        try:
            if not self.provider or not request.model.strip():
                return AgentResult(error="Amplifier Agent needs explicit provider and model values.")
            scope = (str(request.workspace.path.resolve()) if request.workspace else None, request.writable)
            session_id = request.resume or str(uuid4())
            if request.resume and self._sessions.get(session_id) != scope:
                return AgentResult(
                    error="Unknown session or changed workspace permissions. Resume on the same adapter with the same scope.",
                    session_id=session_id,
                )
            self._sessions[session_id] = scope
            remaining = request.timeout_seconds - (time.monotonic() - started)
            return self._worker(
                {
                    "provider": self.provider,
                    "request": request.model_dump(mode="json"),
                    "session_id": session_id,
                    "state_directory": self._state.name,
                    "timeout_seconds": remaining,
                },
                remaining + 5,
                session_id,
            )
        finally:
            self._lock.release()

    def _worker(self, payload: dict[str, Any], timeout: float, session_id: str | None = None) -> AgentResult:
        try:
            with subprocess.Popen(
                [sys.executable, "-m", f"{__package__}.amplifier_worker"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                start_new_session=os.name == "posix",
            ) as process:
                try:
                    stdout, stderr = process.communicate(json.dumps(payload), timeout=timeout)
                finally:
                    # Also reap ordinary shell descendants when cancellation kills the worker.
                    if os.name == "posix":
                        with contextlib.suppress(ProcessLookupError):
                            os.killpg(process.pid, signal.SIGKILL)
                    elif process.poll() is None:
                        subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], capture_output=True)
                    if process.poll() is None:
                        process.kill()
                    process.wait()
            if stderr:
                print(stderr, file=sys.stderr, end="")
            if process.returncode:
                return AgentResult(
                    error=f"Amplifier worker exited with status {process.returncode}. See stderr for diagnostics.",
                    session_id=session_id,
                )
            return AgentResult.model_validate_json(stdout)
        except subprocess.TimeoutExpired:
            return AgentResult(error="Amplifier worker exceeded its timeout and was stopped.", session_id=session_id)
        except Exception as error:
            return AgentResult(error=f"{type(error).__name__}: {error}", session_id=session_id)
