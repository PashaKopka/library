import itertools
import random

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.book_search import search_books
from app.models.author import Author
from app.models.book import Book
from app.models.genre import Genre
from app.schemas.book import BookCreate


@pytest.fixture
async def genres_created(db_session: AsyncSession):
    genres = [Genre(name=f"genre {i}") for i in range(5)]
    db_session.add_all(genres)
    await db_session.commit()
    for genre in genres:
        await db_session.refresh(genre)
    yield genres
    for genre in genres:
        await db_session.delete(genre)
    await db_session.commit()


@pytest.fixture
async def authors_created(db_session: AsyncSession):
    authors = [Author(name=f"Author {i}") for i in range(5)]
    db_session.add_all(authors)
    await db_session.commit()
    for author in authors:
        await db_session.refresh(author)
    yield authors
    for author in authors:
        await db_session.delete(author)
    await db_session.commit()


@pytest.fixture
async def books_created(db_session: AsyncSession, genres_created, authors_created):
    authors_genres_combination = list(
        itertools.product(authors_created, genres_created)
    )
    random.shuffle(authors_genres_combination)

    books = []
    for i, (author, genre) in enumerate(authors_genres_combination):
        book = Book(
            title=f"{i} Book by {author.name} in {genre.name}",
            description=f"Description of book by {author.name}",
            published_year=1800 + i,
            genre_id=genre.id,
            authors=[author],
        )
        books.append(book)
    db_session.add_all(books)
    await db_session.commit()
    for book in books:
        await db_session.refresh(book)
    yield books
    for book in books:
        await db_session.delete(book)
    await db_session.commit()


async def test_search_books_no_results(db_session: AsyncSession):
    results = await search_books(db_session, "Nonexistent Book Title")
    assert results == []


async def test_search_books_by_title(db_session: AsyncSession, books_created):
    target_book = books_created[0]
    query = target_book.title.split()[0]
    results = await search_books(db_session, query)
    assert any(target_book.title == book.title for book in results)
