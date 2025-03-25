from __future__ import annotations

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import CommentModel
from database.models.base import Base


class LikeCommentModel(Base):
    __tablename__ = "comment_likes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    status: Mapped[bool] = mapped_column(default=False)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    user: Mapped["UserModel"] = relationship(  # noqa: F821
        "UserModel", back_populates="comment_likes"
    )  # noqa: F821

    comment_id: Mapped[int] = mapped_column(ForeignKey("comment.id"), nullable=True)
    comment: Mapped["CommentModel"] = relationship(  # noqa: F821
        "CommentModel", back_populates="comment_likes"
    )  # noqa: F821

    def __repr__(self):
        return f"<LikeModel(user_id={self.user_id}, comment_id={self.comment_id})>"
