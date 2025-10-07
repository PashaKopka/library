from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from app.core.database import Base

book_author_association = Table(
    "book_authors",
    Base.metadata,
    Column("book_id", ForeignKey("books.id"), primary_key=True),
    Column("author_id", ForeignKey("authors.id"), primary_key=True),
)


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True)
    title = Column(String(512), nullable=False, index=True)
    description = Column(String, nullable=True)
    published_year = Column(Integer, nullable=True)

    genre_id = Column(Integer, ForeignKey("genres.id"), nullable=False)
    genre = relationship("Genre", back_populates="books")

    authors = relationship("Author", secondary=book_author_association, back_populates="books")
