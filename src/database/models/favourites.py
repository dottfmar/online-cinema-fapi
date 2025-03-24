from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models.accounts import UserModel  # noqa: F401
from src.database.models.base import Base
from src.database.models.movie import MovieModel  # noqa: F401


class FavoritesModel(Base):
    __tablename__ = "favorites"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="favorites")

    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"), nullable=False)
    movie: Mapped["MovieModel"] = relationship("MovieModel", back_populates="favorites")

    def __repr__(self):
        return f"<FavoritesModel(user_id={self.user_id}, movie_id={self.movie_id})>"
