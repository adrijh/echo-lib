from __future__ import annotations

import builtins
from datetime import UTC, datetime
from typing import Any, cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from echo.db.models.adversary import (
    Adversary,
    AdversaryDetail,
    AdversaryMode,
    AdversaryStatus,
)


class AdversaryTable:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        name: str,
        agent_name: str,
        mode: AdversaryMode,
        max_turns: int = 5,
        system_prompt: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Adversary:
        adversary = Adversary(
            name=name,
            agent_name=agent_name,
            mode=mode,
            max_turns=max_turns,
            system_prompt=system_prompt,
            metadata_=metadata,
        )
        self.session.add(adversary)
        await self.session.flush()
        await self.session.refresh(adversary)
        return adversary

    async def get(self, adversary_id: UUID) -> Adversary | None:
        result = await self.session.execute(select(Adversary).where(Adversary.id == adversary_id))
        return cast(Adversary | None, result.scalar_one_or_none())

    async def list(
        self,
        status: AdversaryStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[builtins.list[Adversary], int]:
        query = select(Adversary)
        count_query = select(func.count()).select_from(Adversary)

        if status is not None:
            query = query.where(Adversary.status == status)
            count_query = count_query.where(Adversary.status == status)

        query = query.order_by(Adversary.created_at.desc()).limit(limit).offset(offset)

        result = await self.session.execute(query)
        count_result = await self.session.execute(count_query)

        adversaries = list(result.scalars().all())
        total = count_result.scalar_one()

        return adversaries, total

    async def update(self, adversary_id: UUID, **fields: Any) -> Adversary | None:
        adversary = await self.get(adversary_id)
        if not adversary:
            return None

        for key, value in fields.items():
            if key == "metadata":
                adversary.metadata_ = value
                flag_modified(adversary, "metadata_")
            elif hasattr(adversary, key):
                setattr(adversary, key, value)

        await self.session.flush()
        await self.session.refresh(adversary)
        return adversary

    async def delete(self, adversary_id: UUID) -> bool:
        adversary = await self.get(adversary_id)
        if not adversary:
            return False

        await self.session.delete(adversary)
        await self.session.flush()
        return True

    async def append_message(
        self,
        adversary_id: UUID,
        sender: str,
        message: str,
        timestamp: datetime | None = None,
    ) -> Adversary | None:
        adversary = await self.get(adversary_id)
        if not adversary:
            return None

        entry = {
            "sender": sender,
            "message": message,
            "timestamp": (timestamp or datetime.now(UTC)).isoformat(),
        }
        adversary.messages.append(entry)
        flag_modified(adversary, "messages")

        await self.session.flush()
        await self.session.refresh(adversary)
        return adversary

    async def create_detail(
        self,
        adversary_id: UUID,
        room_name: str,
    ) -> AdversaryDetail:
        detail = AdversaryDetail(
            adversary_id=adversary_id,
            room_name=room_name,
        )
        self.session.add(detail)
        await self.session.flush()
        await self.session.refresh(detail)
        return detail

    async def get_detail(self, detail_id: UUID) -> AdversaryDetail | None:
        result = await self.session.execute(select(AdversaryDetail).where(AdversaryDetail.id == detail_id))
        return cast(AdversaryDetail | None, result.scalar_one_or_none())

    async def list_details(
        self,
        adversary_id: UUID,
    ) -> builtins.list[AdversaryDetail]:
        result = await self.session.execute(
            select(AdversaryDetail)
            .where(AdversaryDetail.adversary_id == adversary_id)
            .order_by(AdversaryDetail.created_at)
        )
        return list(result.scalars().all())

    async def update_detail(
        self,
        detail_id: UUID,
        **fields: Any,
    ) -> AdversaryDetail | None:
        detail = await self.get_detail(detail_id)
        if not detail:
            return None
        for key, value in fields.items():
            if hasattr(detail, key):
                setattr(detail, key, value)
        await self.session.flush()
        await self.session.refresh(detail)
        return detail
