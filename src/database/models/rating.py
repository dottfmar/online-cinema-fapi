from __future__ import annotations

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models.base import Base


class RatingModel(Base):
    __tablename__ = "ratings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    user: Mapped["UserModel"] = relationship(  # noqa: F821
        "UserModel", back_populates="ratings"
    )  # noqa: F821

    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"), nullable=False)
    movie: Mapped["MovieModel"] = relationship(  # noqa: F821
        "MovieModel", back_populates="ratings"
    )  # noqa: F821

    def __repr__(self):
        return f"<RatingModel(user_id={self.user_id}, movie_id={self.movie_id}, rating={self.rating})>"
