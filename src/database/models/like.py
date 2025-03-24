from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.comment import CommentModel
from src.database.models.accounts import UserModel  # noqa: F401
from src.database.models.base import Base
from src.database.models.movie import MovieModel  # noqa: F401


class LikeModel(Base):
    __tablename__ = "likes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="likes")

    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"), nullable=True)
    movie: Mapped["MovieModel"] = relationship("MovieModel", back_populates="likes")

    comment_id: Mapped[int] = mapped_column(ForeignKey("comments.id"), nullable=True)
    comment: Mapped["CommentModel"] = relationship(
        "CommentModel", back_populates="likes"
    )

    def __repr__(self):
        return f"<LikeModel(user_id={self.user_id}, movie_id={self.movie_id}, comment_id={self.comment_id})>"
