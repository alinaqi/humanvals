"""Smoke tests: the framework examples ARE documentation, so CI executes them
(ADR-0008 council amendment). Skipped when the examples group isn't installed."""

import subprocess
import sys
from pathlib import Path

import pytest

EXAMPLES = Path(__file__).resolve().parents[1] / 'examples'

CASES = [
    ('pydantic_ai', 'pydantic_ai_agent.py'),
    ('langgraph', 'langgraph_agent.py'),
    ('crewai', 'crewai_agent.py'),
]


@pytest.mark.parametrize(('module', 'script'), CASES)
def test_example_runs_without_keys(module: str, script: str) -> None:
    pytest.importorskip(module)
    result = subprocess.run(
        [sys.executable, str(EXAMPLES / script)],
        capture_output=True, text=True, timeout=300,
        env={'PATH': '/usr/bin:/bin', 'HOME': '/tmp'},  # explicitly no API keys
    )
    assert result.returncode == 0, result.stderr[-2000:]
    assert '3 cases, 1 guideline learned & injected' in result.stdout
