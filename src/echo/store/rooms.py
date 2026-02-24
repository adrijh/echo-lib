from datetime import datetime
from typing import Any, cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from echo.db.models.room import Room


class RoomsTable:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _upsert(
        self,
        room_id: str,
        thread_id: UUID,
        opportunity_id: str,
        start_timestamp: datetime | None,
        end_timestamp: datetime | None,
        report_url: str | None,
        metadata: dict[str, Any] | None,
    ) -> None:
        update_values = {
            k: v
            for k, v in {
                "start_timestamp": start_timestamp,
                "end_timestamp": end_timestamp,
                "report_url": report_url,
                "metadata": metadata,
            }.items()
            if v is not None
        }

        stmt = (
            insert(Room)
            .values(
                room_id=room_id,
                thread_id=thread_id,
                opportunity_id=opportunity_id,
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
                report_url=report_url,
                metadata_=metadata,
            )
            .on_conflict_do_update(
                index_elements=["room_id"],
                set_=update_values,
            )
        )
        await self.session.execute(stmt)

    async def set_room_start(
        self,
        room_id: str,
        thread_id: UUID,
        opportunity_id: str,
        start_timestamp: datetime,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        await self._upsert(room_id, thread_id, opportunity_id, start_timestamp, None, None, metadata)

    async def set_room_end(
        self,
        room_id: str,
        thread_id: UUID,
        opportunity_id: str,
        end_timestamp: datetime,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        await self._upsert(room_id, thread_id, opportunity_id, None, end_timestamp, None, metadata)

    async def set_room_report(
        self,
        room_id: str,
        thread_id: UUID,
        opportunity_id: str,
        report_url: str,
    ) -> None:
        await self._upsert(room_id, thread_id, opportunity_id, None, None, report_url, None)

    async def get_room(self, room_id: str) -> Room | None:
        result = await self.session.execute(select(Room).where(Room.room_id == room_id))
        return cast(Room | None, result.scalar_one_or_none())

    async def get_rooms(self) -> list[Room]:
        result = await self.session.execute(select(Room).order_by(Room.start_timestamp.desc()))
        return list(result.scalars().all())
