"""Shared fixtures for burstrender tests."""

import sys
from pathlib import Path

import pytest

# Make the repo root importable regardless of how pytest is invoked
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture(autouse=True)
def reset_runtime_state():
    """Reset global runtime state between tests.

    The runtime module is a mutable global singleton; PrintLog.error() sets
    exit_code=2 as a side effect.  Without this reset, tests that exercise
    error paths contaminate tests that assert on default runtime values.
    """
    from imageautomation import runtime as config
    config.exit_code = 0
    config.exit_reason = ""
    config.quiet = False
    yield
    config.exit_code = 0
    config.exit_reason = ""
    config.quiet = False


@pytest.fixture()
def captured_commands(monkeypatch):
    """Capture run_subprocess invocations instead of executing them.

    Returns the list that accumulates (application, command) tuples.
    Patch targets are set by each test module via `patch_run` marker calls,
    so this fixture only provides the sink + a helper to patch a module.
    """
    calls = []

    def fake_run_subprocess(application, command, success_message=None, error_message=None, cwd=None):
        calls.append((application, list(command)))
        return True

    class Patcher:
        def __init__(self):
            self.calls = calls

        def patch(self, module):
            monkeypatch.setattr(module, "run_subprocess", fake_run_subprocess)
            return calls

    return Patcher()
