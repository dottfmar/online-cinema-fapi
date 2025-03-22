import uuid
from enum import Enum
from typing import Optional

from sqlalchemy import (
    String, Float, Text, DECIMAL, UniqueConstraint, Date, ForeignKey, Table, Column, Integer
)
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import Enum as SQLAlchemyEnum

from src.database.models.base import Base


class MovieStatusEnum(str, Enum):
    RELEASED = "Released"
    POST_PRODUCTION = "Post Production"
    IN_PRODUCTION = "In Production"


MoviesGenresModel = Table(
    "movie_genres",
    Base.metadata,
    Column("movie_id", ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True, nullable=False),
    Column("genre_id", ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True, nullable=False),
)

StarsMoviesModel = Table(
    "movie_stars",
    Base.metadata,
    Column("movie_id", ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True, nullable=False),
    Column("star_id", ForeignKey("stars.id", ondelete="CASCADE"), primary_key=True, nullable=False),
)

MoviesDirectorsModel = Table(
    "movie_directors",
    Base.metadata,
    Column("movie_id", ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True, nullable=False),
    Column("director_id", ForeignKey("directors.id", ondelete="CASCADE"), primary_key=True, nullable=False),
)


class GenreModel(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    movies: Mapped[list["MovieModel"]] = relationship("MovieModel", secondary=MoviesGenresModel, back_populates="genres")


class StarModel(Base):
    __tablename__ = "stars"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    movies: Mapped[list["MovieModel"]] = relationship("MovieModel", secondary=StarsMoviesModel, back_populates="stars")


class DirectorModel(Base):
    __tablename__ = "directors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    movies: Mapped[list["MovieModel"]] = relationship("MovieModel", secondary=MoviesDirectorsModel, back_populates="directors")


class CertificationModel(Base):
    __tablename__ = "certifications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    movies: Mapped[list["MovieModel"]] = relationship("MovieModel", back_populates="certification")


class MovieModel(Base):
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, default=lambda: str(uuid.uuid4()), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    time: Mapped[int] = mapped_column(Integer, nullable=False)  # Тривалість у хвилинах
    imdb: Mapped[float] = mapped_column(Float, nullable=False)
    votes: Mapped[int] = mapped_column(Integer, nullable=False)
    meta_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    gross: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    price: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[MovieStatusEnum] = mapped_column(SQLAlchemyEnum(MovieStatusEnum), nullable=False)

    certification_id: Mapped[int] = mapped_column(ForeignKey("certifications.id"), nullable=False)
    certification: Mapped["CertificationModel"] = relationship("CertificationModel", back_populates="movies")

    genres: Mapped[list["GenreModel"]] = relationship("GenreModel", secondary=MoviesGenresModel, back_populates="movies")
    stars: Mapped[list["StarModel"]] = relationship("StarModel", secondary=StarsMoviesModel, back_populates="movies")
    directors: Mapped[list["DirectorModel"]] = relationship("DirectorModel", secondary=MoviesDirectorsModel, back_populates="movies")

    __table_args__ = (
        UniqueConstraint("name", "year", "time", name="unique_movie_constraint"),
    )

    def __repr__(self):
        return f"<Movie(name='{self.name}', year={self.year}, imdb={self.imdb})>"