from typing import Literal

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.genre import get_genre_by_name
from app.models.author import Author
from app.models.book import Book
from app.models.genre import Genre
from app.schemas.book import BookCreate, BookRead, MultipleBooksResponse


async def get_or_create_authors(
    db: AsyncSession,
    author_names: list[str],
) -> list[Author]:
    existing_authors = await db.execute(
        select(Author).filter(Author.name.in_(author_names))
    )
    existing_authors = list(existing_authors.scalars().all())

    existing_names = {str(author.name) for author in existing_authors}
    new_names = set(author_names) - existing_names

    new_authors = [Author(name=name) for name in new_names]
    db.add_all(new_authors)

    if new_authors:
        await db.commit()

        for author in new_authors:
            await db.refresh(author)

    return existing_authors + new_authors


async def save_book(
    payload: BookCreate,
    db: AsyncSession,
) -> BookRead:
    genre_name = payload.genre
    genre = await get_genre_by_name(db, genre_name)

    if not genre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Genre not found"
        )

    payload_author_names = payload.authors
    authors = await get_or_create_authors(db, payload_author_names)

    db_book = Book(
        **payload.model_dump(exclude={"authors", "genre"}),
        genre_id=genre.id,
        authors=authors,
    )
    db.add(db_book)
    await db.commit()
    await db.refresh(db_book)

    book_data = {
        "id": db_book.id,
        "title": db_book.title,
        "description": db_book.description,
        "published_year": db_book.published_year,
        "genre_id": db_book.genre_id,
        "genre": genre.name,
        "authors": [author.name for author in authors],
    }

    return BookRead(**book_data)


async def get_book(db: AsyncSession, book_id: int) -> BookRead:
    result = await db.execute(
        select(Book)
        .where(Book.id == book_id)
        .options(selectinload(Book.authors), selectinload(Book.genre))
    )
    db_book = result.scalars().first()

    if not db_book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Book not found"
        )

    book_data = {
        "id": db_book.id,
        "title": db_book.title,
        "description": db_book.description,
        "published_year": db_book.published_year,
        "genre_id": db_book.genre_id,
        "genre": db_book.genre.name if db_book.genre else None,
        "authors": [author.name for author in db_book.authors],
    }

    return BookRead(**book_data)


async def update_book(db: AsyncSession, book_id: int, payload: BookCreate) -> BookRead:
    result = await db.execute(
        select(Book)
        .where(Book.id == book_id)
        .options(selectinload(Book.authors), selectinload(Book.genre))
    )
    db_book = result.scalars().first()

    if not db_book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Book not found"
        )

    genre_name = payload.genre
    genre = await get_genre_by_name(db, genre_name)

    if not genre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Genre not found"
        )

    payload_author_names = payload.authors
    authors = await get_or_create_authors(db, payload_author_names)

    db_book.title = payload.title
    db_book.description = payload.description
    db_book.published_year = payload.published_year
    db_book.genre_id = genre.id
    db_book.authors = authors

    db.add(db_book)
    await db.commit()
    await db.refresh(db_book)

    book_data = {
        "id": db_book.id,
        "title": db_book.title,
        "description": db_book.description,
        "published_year": db_book.published_year,
        "genre_id": db_book.genre_id,
        "genre": genre.name,
        "authors": [author.name for author in authors],
    }

    return BookRead(**book_data)


async def delete_book(db: AsyncSession, book_id: int) -> None:
    result = await db.execute(select(Book).where(Book.id == book_id))
    db_book = result.scalars().first()

    if not db_book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Book not found"
        )

    await db.delete(db_book)
    await db.commit()


async def get_books(
    db: AsyncSession,
    sort_by: Literal["title", "year", "author"] | None = None,
    title: str | None = None,
    author: str | None = None,
    genre: str | None = None,
    published_year_from: int | None = None,
    published_year_to: int | None = None,
    limit: int = 5,
    offset: int = 0,
) -> MultipleBooksResponse:
    query = (
        select(Book)
        .options(selectinload(Book.authors), selectinload(Book.genre))
        .distinct()
    )

    if title:
        query = query.filter(Book.title.ilike(f"%{title}%"))

    if genre:
        query = query.join(Book.genre).filter(Genre.name == genre.lower())

    if author:
        query = query.join(Book.authors).filter(Author.name.ilike(f"%{author}%"))

    if published_year_from:
        query = query.filter(Book.published_year >= published_year_from)

    if published_year_to:
        query = query.filter(Book.published_year <= published_year_to)

    if sort_by == "title":
        query = query.order_by(Book.title)
    elif sort_by == "year":
        query = query.order_by(Book.published_year)
    elif sort_by == "author":
        query = query.join(Book.authors).order_by(Author.name)

    query = query.limit(limit).offset(offset * limit)

    result = await db.execute(query)
    db_books = result.scalars().unique().all()

    total = await db.scalar(select(func.count()).select_from(query.subquery()))

    books = [
        BookRead(
            id=book.id,
            title=book.title,
            description=book.description,
            published_year=book.published_year,
            genre_id=book.genre_id,
            genre=book.genre.name if book.genre else None,
            authors=[author.name for author in book.authors],
        )
        for book in db_books
    ]

    return MultipleBooksResponse(
        books=books, total=total, page=offset, size=limit
    )
