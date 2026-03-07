from datetime import datetime
from typing import Protocol, cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from echo.db.models.insight import CallRecord


class CallInsightProtocol(Protocol):
    answer: bool
    voicemail_answer: bool
    availability: str | None
    recording_consent: bool | None
    program: str | None
    motivation: str | None
    work_status: str
    financial_interest: bool
    financial_topics: list[str]
    financial_details: str | None
    objection: str | None
    score: str
    summary: str
    callback_requested: bool
    callback_reference_day: str | None
    callback_at: datetime | None


class AnalyticsTable:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def insert_call_metric(
        self,
        campaign_id: str,
        room_id: str,
        opportunity_id: str,
        thread_id: UUID | None,
        user_name: str | None,
        user_phone: str | None,
        user_email: str | None,
        plancode: str | None,
        market: str | None,
        duration: int,
        insight: CallInsightProtocol,
        recording_url: str,
    ) -> None:
        stmt = insert(CallRecord).values(
            campaign_id=campaign_id,
            room_id=room_id,
            opportunity_id=opportunity_id,
            thread_id=thread_id,
            user_name=user_name,
            user_phone=user_phone,
            user_email=user_email,
            plancode=plancode,
            market=market,
            answer=insight.answer,
            voicemail_answer=insight.voicemail_answer,
            availability=insight.availability,
            recording_consent=insight.recording_consent,
            motivation=insight.motivation,
            work_status=insight.work_status,
            financial_interest=insight.financial_interest,
            financial_topics=insight.financial_topics,
            financial_details=insight.financial_details,
            objection=insight.objection,
            score=insight.score,
            summary=insight.summary,
            callback_requested=insight.callback_requested,
            callback_reference_day=insight.callback_reference_day,
            callback_at=insight.callback_at,
            duration_seconds=duration,
            recording_url=recording_url,
        )
        await self.session.execute(stmt)

    async def get_call_record(self, room_id: str) -> CallRecord | None:
        result = await self.session.execute(select(CallRecord).where(CallRecord.room_id == room_id))
        return cast(CallRecord | None, result.scalar_one_or_none())

    async def get_call_records(self) -> list[CallRecord]:
        result = await self.session.execute(select(CallRecord))
        return cast(list[CallRecord], result.scalars().all())
