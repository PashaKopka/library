from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

CURRENT_YEAR = datetime.now().year


class BookBase(BaseModel):
    title: str = Field(..., examples=["The Great Gatsby"], max_length=512)
    description: Optional[str] = Field(
        None, examples=["A novel set in the Roaring Twenties."]
    )
    published_year: Optional[int] = Field(
        None,
        examples=[1925],
        ge=1800,
        le=CURRENT_YEAR,
        description=f"Year must be between 1800 and {CURRENT_YEAR}",
    )
    authors: list[str] = Field(..., examples=["F. Scott Fitzgerald"], min_length=1)
    genre: str = Field(..., examples=["fiction", "thriller"])


class BookCreate(BookBase):
    pass


class BookUpdate(BookBase):
    pass


class BookRead(BookBase):
    id: int
    genre_id: int

    class Config:
        from_attributes = True
        # This setting has been renamed in newer Pydantic versions
        populate_by_name = True


class MultipleBooksResponse(BaseModel):
    books: list[BookRead]
    total: int
    page: int
    size: int
