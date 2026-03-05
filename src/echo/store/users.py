from typing import cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from echo.db.models.user import User


class UsersTable:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert_user(
        self,
        user_id: UUID,
        contact_id: str | None = None,
        opportunity_id: str | None = None,
        name: str | None = None,
        last_name: str | None = None,
        phone_number: str | None = None,
        mail: str | None = None,
        market: str | None = None,
        faculty: str | None = None,
        plancode: str | None = None,
        track: str | None = None,
    ) -> None:
        stmt = (
            insert(User)
            .values(
                user_id=user_id,
                contact_id=contact_id,
                opportunity_id=opportunity_id,
                name=name,
                last_name=last_name,
                phone_number=phone_number,
                mail=mail,
                market=market,
                faculty=faculty,
                plancode=plancode,
                track=track,
            )
            .on_conflict_do_update(
                index_elements=["opportunity_id"],
                set_={
                    "contact_id": contact_id,
                    "opportunity_id": opportunity_id,
                    "name": name,
                    "last_name": last_name,
                    "phone_number": phone_number,
                    "mail": mail,
                    "market": market,
                    "faculty": faculty,
                    "plancode": plancode,
                    "track": track,
                },
            )
        )
        await self.session.execute(stmt)

    async def soft_delete_user(self, user_id: UUID) -> None:
        result = await self.session.execute(select(User).where(User.user_id == user_id))
        user = cast(User | None, result.scalar_one_or_none())
        if user is None:
            raise ValueError(f"User {user_id} not found")
        user.is_active = False

    async def get_users(self) -> list[User]:
        result = await self.session.execute(select(User))
        return cast(list[User], result.scalars().all())

    async def get_user(
        self,
        *,
        user_id: UUID | None = None,
        contact_id: str | None = None,
        opportunity_id: str | None = None,
    ) -> User | None:
        if user_id is None and contact_id is None and opportunity_id is None:
            raise ValueError("get_user requires user_id, contact_id, or opportunity_id")

        stmt = select(User)
        if user_id is not None:
            stmt = stmt.where(User.user_id == user_id)
        elif contact_id is not None:
            stmt = stmt.where(User.contact_id == contact_id)
        else:
            stmt = stmt.where(User.opportunity_id == opportunity_id)

        result = await self.session.execute(stmt)
        return cast(User | None, result.scalar_one_or_none())

    async def query_users(
        self,
        user_id: UUID | None = None,
        contact_id: str | None = None,
        opportunity_id: str | None = None,
        market: str | None = None,
        faculty: str | None = None,
        is_active: bool | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[User]:
        stmt = select(User)

        if user_id is not None:
            stmt = stmt.where(User.user_id == user_id)
        if contact_id is not None:
            stmt = stmt.where(User.contact_id == contact_id)
        if opportunity_id is not None:
            stmt = stmt.where(User.opportunity_id == opportunity_id)
        if market is not None:
            stmt = stmt.where(User.market == market)
        if faculty is not None:
            stmt = stmt.where(User.faculty == faculty)
        if is_active is not None:
            stmt = stmt.where(User.is_active == is_active)
        if limit is not None:
            stmt = stmt.limit(limit)
        if offset is not None:
            stmt = stmt.offset(offset)

        result = await self.session.execute(stmt)
        return cast(list[User], result.scalars().all())
