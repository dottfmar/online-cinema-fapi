# isort: skip_file
from __future__ import annotations
import uuid
from typing import Optional

from sqlalchemy import (
    DECIMAL,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import Base


class MovieModel(Base):
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uuid: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, default=uuid.uuid4, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    time: Mapped[int] = mapped_column(Integer, nullable=False)
    imdb: Mapped[float] = mapped_column(Float, nullable=False)
    votes: Mapped[int] = mapped_column(Integer, nullable=False)
    meta_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    gross: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)

    certification_id: Mapped[int] = mapped_column(
        ForeignKey("certifications.id"), nullable=False
    )
    certification: Mapped["CertificationModel"] = relationship(  # noqa: F821
        "CertificationModel", back_populates="movies"
    )

    genres: Mapped[list["GenreModel"]] = relationship(  # noqa: F821
        "GenreModel", secondary="movie_genres", back_populates="movies"
    )
    stars: Mapped[list["StarModel"]] = relationship(  # noqa: F821
        "StarModel", secondary="movie_stars", back_populates="movies"
    )
    directors: Mapped[list["DirectorModel"]] = relationship(  # noqa: F821
        "DirectorModel", secondary="movie_directors", back_populates="movies"
    )

    items: Mapped["CartItemModel"] = relationship(  # noqa: F821
        "CartItemModel", back_populates="movie"
    )

    order_items: Mapped[list["OrderItemModel"]] = relationship(  # noqa: F821
        "OrderItemModel", back_populates="movie"
    )
    likes = relationship(
        "LikeModel", back_populates="movie", cascade="all, delete-orphan"
    )
    ratings = relationship(
        "RatingModel", back_populates="movie", cascade="all, delete-orphan"
    )
    comments = relationship(
        "CommentModel", back_populates="movie", cascade="all, delete-orphan"
    )
    favorites = relationship(
        "FavoritesModel", back_populates="movie", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("name", "year", "time", name="unique_movie_constraint"),
    )

    def __repr__(self):
        return f"<Movie(name='{self.name}', year={self.year}, imdb={self.imdb})>"
