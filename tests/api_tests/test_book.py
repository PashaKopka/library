import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.models.author import Author
from app.models.book import Book
from app.models.genre import Genre
from app.models.user import User


@pytest.fixture
async def user_created(db_session: AsyncSession):
    hashed_password = hash_password("password123")
    user = User(email="user@example.com", password=hashed_password)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    yield user
    await db_session.delete(user)
    await db_session.commit()


@pytest.fixture
async def genre_created(db_session: AsyncSession):
    genre = Genre(name="fiction")
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
def token(user_created):
    return create_access_token(data={"email": user_created.email})


async def test_create_book(client, token, genre_created, db_session: AsyncSession):
    response = client.post(
        "/api/v1/books/",
        json={
            "title": "Test Book",
            "authors": ["Test Author"],
            "genre": "fiction",
            "published_year": 2020,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    assert response.json()["title"] == "Test Book"
    assert response.json()["authors"] == ["Test Author"]
    assert response.json()["genre"] == "fiction"
    assert response.json()["published_year"] == 2020

    # Verify book is in the database
    book = await db_session.execute(select(Book).where(Book.title == "Test Book"))
    book = book.scalars().first()
    assert book is not None

    # Cleanup
    await db_session.delete(book)
    await db_session.commit()


async def test_get_books(client, token, book_created):
    response = client.get(
        "/api/v1/books/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "books" in data
    assert len(data["books"]) == 1
    assert any(book["title"] == "Book 1" for book in data["books"])


async def test_get_book_by_id(client, token, book_created):
    response = client.get(
        f"/api/v1/books/{book_created.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Book 1"
    assert data["authors"] == ["Author 1"]
    assert data["genre"] == "fiction"
    assert data["published_year"] == 2021


async def test_update_book(
    client, token, book_created, genre_created, db_session: AsyncSession
):
    response = client.put(
        f"/api/v1/books/{book_created.id}",
        json={
            "title": "Updated Book",
            "authors": ["Updated Author"],
            "genre": "fiction",
            "published_year": 2022,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Book"
    assert data["authors"] == ["Updated Author"]
    assert data["genre"] == "fiction"
    assert data["published_year"] == 2022


async def test_delete_book(client, token, book_created, db_session: AsyncSession):
    response = client.delete(
        f"/api/v1/books/{book_created.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204

    # Verify book is deleted from the database
    book = await db_session.execute(select(Book).where(Book.id == book_created.id))
    book = book.scalars().first()
    assert book is None


async def test_upload_books_bulk(
    client, token, genre_created, db_session: AsyncSession
):
    books_data = [
        {
            "title": "Bulk Book 1",
            "authors": ["Bulk Author 1"],
            "genre": "fiction",
            "published_year": 2019,
        },
        {
            "title": "Bulk Book 2",
            "authors": ["Bulk Author 2"],
            "genre": "fiction",
            "published_year": 2018,
        },
    ]
    import json
    from io import BytesIO

    file_content = json.dumps(books_data).encode("utf-8")
    file = BytesIO(file_content)
    file.name = "books.json"

    response = client.post(
        "/api/v1/books/bulk-upload",
        files={"json_file": ("books.json", file, "application/json")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert len(data) == 2

    # Verify books are in the database
    for book_data in books_data:
        book = await db_session.execute(
            select(Book).where(Book.title == book_data["title"])
        )
        book = book.scalars().first()
        assert book is not None

        # Cleanup
        await db_session.delete(book)
    await db_session.commit()


async def test_search_books(client, token, book_created):
    response = client.get(
        "/api/v1/books/search/",
        params={"query": "Book"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["books"]) == 1
    assert data["books"][0]["title"] == "Book 1"
