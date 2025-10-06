from sqlalchemy import select

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.author import get_or_create_authors
from app.models.author import Author


@pytest.fixture
async def author_created(db_session: AsyncSession):
    author = Author(name="Author 1")
    db_session.add(author)
    await db_session.commit()
    await db_session.refresh(author)
    yield author
    await db_session.delete(author)
    await db_session.commit()


async def test_create_authors(db_session):
    author = await get_or_create_authors(db_session, ["Author 1"])
    assert author[0] is not None
    assert str(author[0].name) == "Author 1"

    await db_session.delete(author[0])
    await db_session.commit()


async def test_create_multiple_authors(db_session):
    authors = await get_or_create_authors(db_session, ["Author 1", "Author 2"])
    assert len(authors) == 2
    assert {str(author.name) for author in authors} == {"Author 1", "Author 2"}

    await db_session.delete(authors[0])
    await db_session.delete(authors[1])
    await db_session.commit()


async def test_get_author(db_session, author_created):
    authors = await get_or_create_authors(db_session, ["Author 1"])
    assert len(authors) == 1
    assert str(authors[0].name) == str(author_created.name)

    existing_authors = await db_session.execute(
        select(Author).filter(Author.name == "Author 1")
    )
    existing_authors = list(existing_authors.scalars().all())
    assert len(existing_authors) == 1
    assert str(existing_authors[0].name) == "Author 1"

    await db_session.delete(existing_authors[0])
    await db_session.commit()


async def test_get_or_create_authors(db_session, author_created):
    authors = await get_or_create_authors(db_session, ["Author 1", "Author 2"])
    assert len(authors) == 2
    assert str(authors[0].name) == "Author 1"
    assert str(authors[1].name) == "Author 2"

    existing_authors = await db_session.execute(
        select(Author).filter(Author.name.in_(["Author 1", "Author 2"]))
    )
    existing_authors = list(existing_authors.scalars().all())
    assert len(existing_authors) == 2
    assert str(existing_authors[0].name) == "Author 1"
    assert str(existing_authors[1].name) == "Author 2"

    await db_session.delete(authors[0])
    await db_session.delete(authors[1])
    await db_session.commit()
