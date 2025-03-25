from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import Base


class CommentModel(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(String(100), nullable=False)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    user: Mapped["UserModel"] = relationship(  # noqa: F821
        "UserModel", back_populates="comments"
    )  # noqa: F821

    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"), nullable=False)
    movie: Mapped["MovieModel"] = relationship(  # noqa: F821
        "MovieModel", back_populates="comments"
    )  # noqa: F821

    parent_comment_id: Mapped[int] = mapped_column(
        ForeignKey("comments.id"), nullable=True
    )
    parent_comment: Mapped["CommentModel"] = relationship(
        "CommentModel", back_populates="replies", remote_side=[id]
    )

    replies: Mapped[list["CommentModel"]] = relationship(
        "CommentModel", back_populates="parent_comment"
    )

    comment_likes: Mapped[list["LikeCommentModel"]] = relationship(  # noqa: F821
        "LikeCommentModel", back_populates="comment"
    )

    def __repr__(self):
        return f"<CommentModel(user_id={self.user_id}, movie_id={self.movie_id}, content='{self.content}')>"
