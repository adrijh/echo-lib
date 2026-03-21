from datetime import datetime
from typing import Any, cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

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
                "thread_id": thread_id,
                "opportunity_id": opportunity_id,
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

    async def get_room(self, room_id: str | None = None, opportunity_id: str | None = None) -> Room | None:
        if not room_id and not opportunity_id:
            return None

        query = select(Room)
        if room_id:
            query = query.where(Room.room_id == room_id)
        if opportunity_id:
            query = query.where(Room.opportunity_id == opportunity_id)

        result = await self.session.execute(query)
        return cast(Room | None, result.scalar_one_or_none())

    async def get_rooms(self) -> list[Room]:
        result = await self.session.execute(select(Room).order_by(Room.start_timestamp.desc()))
        return list(result.scalars().all())

    async def update_metadata(self, room_id: str, new_metadata: dict[str, Any]) -> bool:
        room = await self.get_room(room_id)
        if not room:
            return False

        current_metadata = dict(room.metadata_) if isinstance(room.metadata_, dict) else {}
        updated = False
        for k, v in new_metadata.items():
            if v:
                current_metadata[k] = v
                updated = True

        if updated:
            room.metadata_ = current_metadata
            flag_modified(room, "metadata_")
            await self.session.commit()
            return True
        return False
