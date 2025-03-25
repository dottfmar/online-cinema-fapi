from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import CommentModel, UserModel
from database.models.base import Base


class LikeCommentModel(Base):
    __tablename__ = "comment_likes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    status: Mapped[bool] = mapped_column(default=False)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    user: Mapped["UserModel"] = relationship(
        "UserModel", back_populates="comment_likes"
    )

    comment_id: Mapped[int] = mapped_column(ForeignKey("comments.id"), nullable=False)
    comment: Mapped["CommentModel"] = relationship(
        "CommentModel", back_populates="comment_likes"
    )

    def __repr__(self):
        return (
            f"<LikeCommentModel(user_id={self.user_id}, comment_id={self.comment_id})>"
        )
