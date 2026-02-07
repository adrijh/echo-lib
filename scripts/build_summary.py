import json
from pathlib import Path
from typing import Any, cast

from dotenv import load_dotenv

from echo.utils.messages import build_summary, livekit_report_to_chat

ENV_FILE = Path(__file__).parent / ".." / ".env"
load_dotenv(ENV_FILE)

if __name__ == "__main__":
    report_path = Path(__file__).parent / ".." / "data" / "session-report.json"
    with open(report_path) as f:
        report = cast(dict[str, Any], json.load(f))

    chat = livekit_report_to_chat(report)
    summary = build_summary(chat)
    print(summary)
