from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.book import book_author_association


class Author(Base):
    __tablename__ = "authors"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)

    books = relationship(
        "Book", secondary=book_author_association, back_populates="authors"
    )
