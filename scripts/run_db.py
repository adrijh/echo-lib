import asyncio
from pathlib import Path

from dotenv import load_dotenv

ENV_FILE = Path(__file__).parent / ".." / ".env"
load_dotenv(ENV_FILE)


async def reset_db() -> None:
    from echo.db.base import Base, create_engine

    engine = create_engine()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(reset_db())
