import itertools
import random

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.book import delete_book, get_book, get_books, save_book, update_book
from app.models.author import Author
from app.models.book import Book
from app.models.genre import Genre
from app.schemas.book import BookCreate


@pytest.fixture
async def genre_created(db_session: AsyncSession):
    genre = Genre(name="genre 1")
    db_session.add(genre)
    await db_session.commit()
    await db_session.refresh(genre)
    yield genre
    await db_session.delete(genre)
    await db_session.commit()


@pytest.fixture
async def author_created(db_session: AsyncSession):
    author = Author(name="Author 1")
    db_session.add(author)
    await db_session.commit()
    await db_session.refresh(author)
    yield author
    await db_session.delete(author)
    await db_session.commit()


@pytest.fixture
async def book_created(db_session: AsyncSession, genre_created, author_created):
    book = Book(
        title="Book 1",
        description="Description 1",
        published_year=2021,
        genre_id=genre_created.id,
        authors=[author_created],
    )
    db_session.add(book)
    await db_session.commit()
    await db_session.refresh(book)
    yield book
    await db_session.delete(book)
    await db_session.commit()


@pytest.fixture
async def new_genre(db_session: AsyncSession):
    new_genre = Genre(name="New Genre")
    db_session.add(new_genre)
    await db_session.commit()
    await db_session.refresh(new_genre)
    yield new_genre
    await db_session.delete(new_genre)
    await db_session.commit()


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


async def test_save_book_no_genre(db_session):
    book = BookCreate(
        title="New Book",
        description="New Description",
        published_year=2022,
        genre="Nonexistent Genre",
        authors=["Author 1", "Author 2"],
    )
    with pytest.raises(Exception) as excinfo:
        await save_book(book, db_session)

    assert excinfo.type.__name__ == "HTTPException"
    assert "Genre not found" in str(excinfo.value)


async def test_save_book(db_session, genre_created):
    book = BookCreate(
        title="New Book",
        description="New Description",
        published_year=2022,
        genre=genre_created.name,
        authors=["Author 1", "Author 2"],
    )
    saved_book = await save_book(book, db_session)

    assert saved_book.title == book.title
    assert saved_book.description == book.description
    assert saved_book.published_year == book.published_year
    assert saved_book.genre == genre_created.name
    assert set(saved_book.authors) == set(book.authors)

    # Cleanup
    db_book = await db_session.get(Book, saved_book.id)
    await db_session.delete(db_book)
    await db_session.commit()

    for author_name in book.authors:
        result = await db_session.execute(
            select(Author).where(Author.name == author_name)
        )
        author = result.scalars().first()
        if author:
            await db_session.delete(author)
    await db_session.commit()


async def test_get_book_not_found(db_session):
    with pytest.raises(Exception) as excinfo:
        await get_book(db_session, book_id=9999)

    assert excinfo.type.__name__ == "HTTPException"
    assert "Book not found" in str(excinfo.value)


async def test_get_book(db_session, book_created):
    fetched_book = await get_book(db_session, book_id=book_created.id)

    assert fetched_book.id == book_created.id
    assert fetched_book.title == book_created.title
    assert fetched_book.description == book_created.description
    assert fetched_book.published_year == book_created.published_year
    assert fetched_book.genre == book_created.genre.name
    assert set(fetched_book.authors) == {author.name for author in book_created.authors}


async def test_update_book_not_found(db_session):
    book_update = BookCreate(
        title="Updated Book",
        description="Updated Description",
        published_year=2023,
        genre="Nonexistent Genre",
        authors=["Author 1", "Author 2"],
    )
    with pytest.raises(Exception) as excinfo:
        await update_book(db_session, book_id=9999, payload=book_update)

    assert excinfo.type.__name__ == "HTTPException"
    assert "Book not found" in str(excinfo.value)


async def test_update_book_no_genre(db_session, book_created):
    book_update = BookCreate(
        title="Updated Book",
        description="Updated Description",
        published_year=2023,
        genre="Nonexistent Genre",
        authors=["Author 1", "Author 2"],
    )
    with pytest.raises(Exception) as excinfo:
        await update_book(db_session, book_id=book_created.id, payload=book_update)

    assert excinfo.type.__name__ == "HTTPException"
    assert "Genre not found" in str(excinfo.value)


async def test_update_book(db_session, book_created, new_genre):
    book_update = BookCreate(
        title="Updated Book",
        description="Updated Description",
        published_year=2023,
        genre=new_genre.name,
        authors=["Author 3", "Author 4"],
    )
    updated_book = await update_book(
        db_session, book_id=book_created.id, payload=book_update
    )

    assert updated_book.id == book_created.id
    assert updated_book.title == book_update.title
    assert updated_book.description == book_update.description
    assert updated_book.published_year == book_update.published_year
    assert updated_book.genre == new_genre.name
    assert set(updated_book.authors) == set(book_update.authors)

    # Cleanup
    db_book = await db_session.get(Book, updated_book.id)
    await db_session.delete(db_book)
    await db_session.delete(new_genre)
    await db_session.commit()

    for author_name in book_update.authors:
        result = await db_session.execute(
            select(Author).where(Author.name == author_name)
        )
        author = result.scalars().first()
        if author:
            await db_session.delete(author)
    await db_session.commit()


async def test_delete_book_not_found(db_session):
    with pytest.raises(Exception) as excinfo:
        await delete_book(db_session, book_id=9999)

    assert excinfo.type.__name__ == "HTTPException"
    assert "Book not found" in str(excinfo.value)


async def test_delete_book(db_session, book_created):
    await delete_book(db_session, book_id=book_created.id)

    result = await db_session.execute(select(Book).where(Book.id == book_created.id))
    deleted_book = result.scalars().first()
    assert deleted_book is None

    for author in book_created.authors:
        result = await db_session.execute(select(Author).where(Author.id == author.id))
        author_in_db = result.scalars().first()
        if author_in_db:
            await db_session.delete(author_in_db)
    await db_session.commit()


async def test_get_books(db_session, book_created):
    fetched_books = await get_books(db_session)

    assert fetched_books.total == 1
    assert len(fetched_books.books) == 1
    assert fetched_books.books[0].id == book_created.id
    assert fetched_books.page == 0
    assert fetched_books.size == 5


async def test_get_books_filter_by_title(db_session, books_created):
    title_filter = "Book by Author 0 in genre 0"
    fetched_books = await get_books(db_session, title=title_filter)

    assert fetched_books.total == 1
    assert len(fetched_books.books) == 1
    assert title_filter in fetched_books.books[0].title
    assert fetched_books.page == 0
    assert fetched_books.size == 5

    title_filter = "book by author 0 in genre 0"
    fetched_books = await get_books(db_session, title=title_filter)

    assert fetched_books.total == 1
    assert len(fetched_books.books) == 1
    assert title_filter in fetched_books.books[0].title.lower()
    assert fetched_books.page == 0
    assert fetched_books.size == 5

    title_filter = "by author 0"
    fetched_books = await get_books(db_session, title=title_filter)

    assert fetched_books.total == 5
    assert len(fetched_books.books) == 5
    assert title_filter in fetched_books.books[0].title.lower()
    assert fetched_books.page == 0
    assert fetched_books.size == 5


async def test_get_books_filter_by_genre(db_session, books_created):
    genre_filter = "genre 0"
    fetched_books = await get_books(db_session, genre=genre_filter)

    assert fetched_books.total == 5
    assert len(fetched_books.books) == 5
    assert genre_filter in fetched_books.books[0].genre.lower()
    assert fetched_books.page == 0
    assert fetched_books.size == 5

    genre_filter = "Genre 0"
    fetched_books = await get_books(db_session, genre=genre_filter)

    assert fetched_books.total == 5
    assert len(fetched_books.books) == 5
    assert genre_filter.lower() in fetched_books.books[0].genre.lower()
    assert fetched_books.page == 0
    assert fetched_books.size == 5


async def test_get_books_filter_by_author(db_session, books_created):
    author_filter = "author 0"
    fetched_books = await get_books(db_session, author=author_filter)

    assert fetched_books.total == 5
    assert len(fetched_books.books) == 5
    assert author_filter in fetched_books.books[0].authors[0].lower()
    assert fetched_books.page == 0
    assert fetched_books.size == 5

    author_filter = "0"
    fetched_books = await get_books(db_session, author=author_filter)

    assert fetched_books.total == 5
    assert len(fetched_books.books) == 5
    assert author_filter.lower() in fetched_books.books[0].authors[0].lower()
    assert fetched_books.page == 0
    assert fetched_books.size == 5


async def test_get_books_filter_by_published_year_from(db_session, books_created):
    year_from_filter = 1805
    fetched_books = await get_books(db_session, published_year_from=year_from_filter)

    assert fetched_books.total == 20
    assert len(fetched_books.books) == 5
    assert all(book.published_year >= year_from_filter for book in fetched_books.books)
    assert fetched_books.page == 0
    assert fetched_books.size == 5


async def test_get_books_filter_by_published_year_to(db_session, books_created):
    year_to_filter = 1809
    fetched_books = await get_books(db_session, published_year_to=year_to_filter)

    assert fetched_books.total == 10
    assert len(fetched_books.books) == 5
    assert all(book.published_year <= year_to_filter for book in fetched_books.books)
    assert fetched_books.page == 0
    assert fetched_books.size == 5


async def test_get_books_sort_by_title(db_session, books_created):
    fetched_books = await get_books(db_session, sort_by="title")

    assert fetched_books.total == 25
    assert len(fetched_books.books) == 5
    titles = [book.title for book in fetched_books.books]
    assert titles == sorted(titles)
    assert fetched_books.page == 0
    assert fetched_books.size == 5


async def test_get_books_sort_by_year(db_session, books_created):
    fetched_books = await get_books(db_session, sort_by="year")

    assert fetched_books.total == 25
    assert len(fetched_books.books) == 5
    years = [book.published_year for book in fetched_books.books]
    assert years == sorted(years)
    assert fetched_books.page == 0
    assert fetched_books.size == 5


async def test_get_books_sort_by_author(db_session, books_created):
    fetched_books = await get_books(db_session, sort_by="author")

    assert fetched_books.total == 25
    assert len(fetched_books.books) == 5
    authors = [book.authors[0] for book in fetched_books.books]
    assert authors == sorted(authors)
    assert fetched_books.page == 0
    assert fetched_books.size == 5
