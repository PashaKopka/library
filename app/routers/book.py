from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.crud.book import delete_book, get_book, get_books, save_book, update_book
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.book import BookCreate, BookRead, MultipleBooksResponse

router = APIRouter(prefix="/api/v1/books", tags=["books"])


@router.post("/", response_model=BookRead, status_code=status.HTTP_201_CREATED)
async def create_book(
    payload: BookCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    book = await save_book(payload=payload, db=db)
    return book


@router.get("/", response_model=MultipleBooksResponse, status_code=status.HTTP_200_OK)
async def get_books_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    sort_by: Literal["title", "year", "author"] | None = None,
    title: str | None = None,
    author: str | None = None,
    genre: str | None = None,
    published_year_from: int | None = None,
    published_year_to: int | None = None,
    limit: int = 5,
    page: int = 0,
):
    """
    Get all books with support for pagination,
    sorting (by title, year, author),
    filtering (by title, author, genre, published_year_from, and published_year_to)
    """
    books = await get_books(
        db=db,
        sort_by=sort_by,
        title=title,
        author=author,
        genre=genre,
        published_year_from=published_year_from,
        published_year_to=published_year_to,
        limit=limit,
        offset=page,
    )
    return books


@router.get("/{book_id}", response_model=BookRead, status_code=status.HTTP_200_OK)
async def get_book_by_id(
    book_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    book = await get_book(db=db, book_id=book_id)
    return book


@router.put("/{book_id}", response_model=BookRead, status_code=status.HTTP_200_OK)
async def update_book_endpoint(
    book_id: int,
    payload: BookCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    book = await update_book(db=db, book_id=book_id, payload=payload)
    return book


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book_endpoint(
    book_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await delete_book(db=db, book_id=book_id)
    return {"detail": "Book deleted successfully"}
