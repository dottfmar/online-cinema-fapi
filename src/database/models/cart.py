from __future__ import annotations

from sqlalchemy import Column, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, relationship

from database.models.base import Base


class CartModel(Base):
    __tablename__ = "carts"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = Column(
        Integer, ForeignKey("users.id"), unique=True, nullable=False
    )

    user: Mapped["UserModel"] = relationship(  # noqa: F821
        "UserModel", back_populates="cart"
    )

    items: Mapped["CartItemModel"] = relationship(  # noqa: F821
        "CartItemModel", back_populates="cart", cascade="all, delete-orphan"
    )

    __table_args__ = (UniqueConstraint("user_id", name="uq_user_cart"),)

    def __repr__(self):
        return f"<CartModel(id={self.id}, user_id={self.user_id})>"
