from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Author, Book
from app.schemas.book import BookRead


async def search_books(db: AsyncSession, query: str) -> list[BookRead]:
    q = query.lower().strip()

    stmt = (
        select(Book)
        .join(Book.authors, isouter=True)
        .options(selectinload(Book.authors), selectinload(Book.genre))
        .where(
            or_(
                Book.title.ilike(f"%{q}%"),
                Author.name.ilike(f"%{q}%"),
                func.similarity(Book.title, q) > 0.3,
                func.similarity(Author.name, q) > 0.3,
            )
        )
    )

    result = await db.execute(stmt)
    books = result.scalars().unique().all()

    return [
        BookRead(
            id=book.id,
            title=book.title,
            description=book.description,
            published_year=book.published_year,
            genre_id=book.genre_id,
            genre=book.genre.name if book.genre else None,
            authors=[a.name for a in book.authors],
        )
        for book in books
    ]
