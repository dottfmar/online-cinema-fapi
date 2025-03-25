from __future__ import annotations

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import Base


class LikeMovieModel(Base):
    __tablename__ = "movie_likes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    status: Mapped[bool] = mapped_column(default=False)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    user: Mapped["UserModel"] = relationship(  # noqa: F821
        "UserModel", back_populates="movie_likes"
    )  # noqa: F821

    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"), nullable=True)
    movie: Mapped["MovieModel"] = relationship(  # noqa: F821
        "MovieModel", back_populates="movie_likes"
    )  # noqa: F821

    def __repr__(self):
        return f"<LikeModel(user_id={self.user_id}, movie_id={self.movie_id})>"
