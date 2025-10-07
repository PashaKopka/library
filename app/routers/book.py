import json
from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.crud.book import (
    delete_book,
    get_book,
    get_books,
    save_book,
    sort_by_literal,
    update_book,
)
from app.crud.book_search import search_books
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
    sort_by: sort_by_literal | None = None,
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


@router.post("/bulk-upload", status_code=status.HTTP_201_CREATED)
async def bulk_upload_books(
    json_file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[BookRead]:
    """
    Upload a JSON file with a list of books.

    Example JSON file:

    ```json
    [
      {
        "title": "The Great Gatsby",
        "description": "A novel set in the Roaring Twenties.",
        "published_year": 1925,
        "authors": ["F. Scott Fitzgerald"],
        "genre": "fiction"
      },
      {
        "title": "Dune",
        "description": "Epic sci-fi saga.",
        "published_year": 1965,
        "authors": ["Frank Herbert"],
        "genre": "science"
      }
    ]
    ```
    """

    allowed_content_types = ["application/json", "text/json"]

    if (
        not json_file.filename.lower().endswith(".json")
        or json_file.content_type not in allowed_content_types
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. File must be a JSON (.json) file.",
        )

    try:
        contents = await json_file.read()
        data = json.loads(contents)
        if not isinstance(data, list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="JSON file must contain a list of book objects.",
            )

        created_books = []
        for item in data:
            if not isinstance(item, dict):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Each book entry must be a JSON object.",
                )
            book = await save_book(payload=BookCreate(**item), db=db)
            created_books.append(book)

        return created_books

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to decode JSON. Please ensure the file contains valid JSON.",
        )


@router.get(
    "/search/", response_model=MultipleBooksResponse, status_code=status.HTTP_200_OK
)
async def books_search(
    query: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    results = await search_books(db, query)
    return MultipleBooksResponse(
        books=results, total=len(results), page=0, size=len(results)
    )
