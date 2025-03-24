from __future__ import annotations

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import Base


class LikeModel(Base):
    __tablename__ = "likes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    user: Mapped["UserModel"] = relationship(  # noqa: F821
        "UserModel", back_populates="likes"
    )  # noqa: F821

    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"), nullable=True)
    movie: Mapped["MovieModel"] = relationship(  # noqa: F821
        "MovieModel", back_populates="likes"
    )  # noqa: F821

    comment_id: Mapped[int] = mapped_column(ForeignKey("comments.id"), nullable=True)
    comment: Mapped["CommentModel"] = relationship(  # noqa: F821
        "CommentModel", back_populates="likes"
    )

    def __repr__(self):
        return f"<LikeModel(user_id={self.user_id}, movie_id={self.movie_id}, comment_id={self.comment_id})>"
