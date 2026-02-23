from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from echo.db.models.scheduled_call import ScheduledCall


class ScheduleCallsTable:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert_schedule_call(
        self,
        opportunity_id: str,
        scheduled_at: datetime,
        metadata: dict[str, Any] | None,
        status: str = "pending",
    ) -> None:
        stmt = (
            insert(ScheduledCall)
            .values(
                opportunity_id=opportunity_id,
                scheduled_at=scheduled_at,
                metadata_=metadata,
                status=status,
            )
            .on_conflict_do_update(
                index_elements=["opportunity_id"],
                set_={
                    "scheduled_at": scheduled_at,
                    "metadata_": metadata,
                    "status": status,
                },
            )
        )
        await self.session.execute(stmt)

    async def get_ready_calls(self) -> list[ScheduledCall]:
        stmt = select(ScheduledCall).where(
            ScheduledCall.status == "pending",
            ScheduledCall.scheduled_at <= datetime.now(UTC),
        )
        result = await self.session.execute(stmt)
        return cast(list[ScheduledCall], result.scalars().all())

    async def mark_finished(self, opportunity_id: str) -> None:
        result = await self.session.execute(select(ScheduledCall).where(ScheduledCall.opportunity_id == opportunity_id))
        row = cast(ScheduledCall | None, result.scalar_one_or_none())
        if row is None:
            raise ValueError(f"ScheduleCall {opportunity_id} not found")
        row.status = "finished"
