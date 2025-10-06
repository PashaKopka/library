import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.genre import get_genre_by_name
from app.models.genre import Genre


@pytest.fixture
async def genre_created(db_session: AsyncSession):
    genre = Genre(name="science fiction")
    db_session.add(genre)
    await db_session.commit()
    await db_session.refresh(genre)
    yield genre
    await db_session.delete(genre)
    await db_session.commit()


async def test_get_genre_by_name(db_session, genre_created):
    genre = await get_genre_by_name(db_session, "science fiction")
    assert genre is not None
    assert str(genre.name) == str(genre_created.name)
