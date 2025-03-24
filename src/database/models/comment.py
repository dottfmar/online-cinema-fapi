from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models.accounts import UserModel  # noqa: F401
from src.database.models.base import Base
from src.database.models.movie import MovieModel  # noqa: F401


class CommentModel(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(String(100), nullable=False)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="comments")

    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"), nullable=False)
    movie: Mapped["MovieModel"] = relationship("MovieModel", back_populates="comments")

    parent_comment_id: Mapped[int] = mapped_column(
        ForeignKey("comments.id"), nullable=True
    )
    parent_comment: Mapped["CommentModel"] = relationship(
        "CommentModel", back_populates="replies", remote_side=[id]
    )

    replies: Mapped[list["CommentModel"]] = relationship(
        "CommentModel", back_populates="parent_comment"
    )

    def __repr__(self):
        return f"<CommentModel(user_id={self.user_id}, movie_id={self.movie_id}, content='{self.content}')>"
