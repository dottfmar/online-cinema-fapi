# isort: skip_file

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models.associations import MoviesGenresModel
from src.database.models.base import Base
from src.database.models.movie import MovieModel


class GenreModel(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    movies: Mapped[list["MovieModel"]] = relationship(
        "MovieModel", secondary=MoviesGenresModel, back_populates="genres"
    )
