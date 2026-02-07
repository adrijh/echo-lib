import json
from pathlib import Path
from typing import Any, cast

import pytest

from echo.utils.messages import livekit_report_to_chat


@pytest.fixture
def report() -> dict[str, Any]:
    report_path = Path(__file__).parent / ".." / ".." / "data" / "session-report.json"
    with open(report_path) as f:
        return cast(dict[str, Any], json.load(f))


def test_report_to_chat(report: dict[str, Any]) -> None:
    messages = livekit_report_to_chat(report)

    for message in messages:
        assert "content" in message
        assert "role" in message
        assert message["role"] in ["assistant", "user", "system"]
        assert len(message["content"]) > 0
