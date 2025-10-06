from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.genre import Genre


async def get_genre_by_name(db: AsyncSession, name: str) -> Genre | None:
    result = await db.execute(select(Genre).filter(Genre.name == name))
    return result.scalars().first()
