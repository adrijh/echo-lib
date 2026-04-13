import argparse
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from dotenv import load_dotenv

load_dotenv()

from echo.db.models.campaign_detail import CampaignDetail
from echo.db.models.insight import CallRecord
from echo.store.store import PostgresStore
from echo.utils.storage import fetch_report

logger = logging.getLogger(__name__)

STORAGE_ACCOUNT_NAME = "echodevstorage01"
CONTAINER_NAME = "sessions"
BLOB_BASE_URL = f"https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net/{CONTAINER_NAME}"


async def get_opportunity_ids(store: PostgresStore, campaign_id: str) -> list[str]:
    stmt = select(CampaignDetail.opportunity_id).where(
        CampaignDetail.campaign_id == campaign_id
    )
    result = await store.session.execute(stmt)
    return [row[0] for row in result.all()]


async def get_all_call_details(
    store: PostgresStore, campaign_id: str
) -> dict[str, list[dict[str, Any]]]:
    """Fetch all call details for a campaign, grouped by opportunity_id."""
    stmt = select(
        CallRecord.opportunity_id,
        CallRecord.room_id,
        CallRecord.score,
        CallRecord.processed_at,
    ).where(
        CallRecord.campaign_id == campaign_id,
    )
    result = await store.session.execute(stmt)

    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in result.all():
        grouped.setdefault(row[0], []).append(
            {"room_id": row[1], "score": row[2], "processed_at": row[3]}
        )
    return grouped


def report_to_transcription(report: dict[str, Any]) -> str:
    """Convert a LiveKit session report into a clean, readable transcription."""
    lines: list[str] = []
    events = report.get("events", [])

    for event in events:
        event_type = event.get("type")

        if event_type == "user_input_transcribed" and event.get("is_final"):
            text = event.get("transcript", "").strip()
            if text:
                lines.append(f"User:  {text}")

        elif event_type == "conversation_item_added":
            item = event.get("item", {})
            if item.get("type") == "message" and item.get("role") == "assistant":
                parts = item.get("content", [])
                text = " ".join(parts).strip()
                if text:
                    lines.append(f"Agent: {text}")

    return "\n\n".join(lines)


def get_transcription_path(
    output_dir: Path,
    processed_at: datetime | None,
    score: str | int | None,
    opportunity_id: str,
) -> Path:
    date_label = processed_at.strftime("%Y-%m-%d") if processed_at else "unknown-date"
    score_label = str(score) if score is not None else "unscored"
    return output_dir / date_label / score_label / f"{opportunity_id}.txt"


def save_transcription(filepath: Path, text: str) -> Path:
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(text, encoding="utf-8")
    return filepath


async def run(campaign_id: str, output_dir: Path, *, force: bool = False) -> None:
    async with PostgresStore.open() as store:
        opportunity_ids = await get_opportunity_ids(store, campaign_id)
        logger.info("Found %d opportunities for campaign %s", len(opportunity_ids), campaign_id)

        if not opportunity_ids:
            logger.warning("No opportunities found. Exiting.")
            return

        call_details_by_opp = await get_all_call_details(store, campaign_id)
        logger.info("Found call records for %d opportunities", len(call_details_by_opp))

        downloaded = 0
        skipped = 0
        cached = 0

        for opp_id in opportunity_ids:
            call_details = call_details_by_opp.get(opp_id)

            if not call_details:
                logger.debug("No call history for opportunity %s", opp_id)
                skipped += 1
                continue

            detail = call_details[-1]
            room_id = detail["room_id"]
            score = detail["score"]
            processed_at = detail["processed_at"]

            if not room_id:
                logger.debug("No room_id for opportunity %s", opp_id)
                skipped += 1
                continue

            filepath = get_transcription_path(output_dir, processed_at, score, opp_id)

            if filepath.exists() and not force:
                logger.debug("Already exists, skipping: %s", filepath)
                cached += 1
                continue

            blob_url = f"{BLOB_BASE_URL}/recordings/{room_id}/session-report.json"

            try:
                report = await fetch_report(blob_url)
            except Exception:
                logger.warning("Failed to fetch report for room_id=%s", room_id, exc_info=True)
                skipped += 1
                continue

            transcription = report_to_transcription(report)

            save_transcription(filepath, transcription)
            logger.info("Saved: %s", filepath)
            downloaded += 1

        logger.info(
            "Done. downloaded=%d cached=%d skipped=%d total=%d",
            downloaded, cached, skipped, len(opportunity_ids),
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract campaign transcriptions")
    parser.add_argument("campaign_id", help="Campaign UUID")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("transcriptions"),
        help="Output directory (default: ./transcriptions)",
    )
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--force", "-f", action="store_true", help="Re-download even if file already exists")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-8s %(message)s",
    )

    asyncio.run(run(args.campaign_id, args.output_dir, force=args.force))


if __name__ == "__main__":
    main()
