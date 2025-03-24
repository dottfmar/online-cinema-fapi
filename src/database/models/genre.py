from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import Base


class GenreModel(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    movies: Mapped[list["MovieModel"]] = relationship(  # noqa: F821
        "MovieModel", secondary="movie_genres", back_populates="genres"
    )
