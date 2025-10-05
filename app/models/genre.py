from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Genre(Base):
    __tablename__ = "genres"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)

    books = relationship("Book", back_populates="genre", cascade="all, delete-orphan")
