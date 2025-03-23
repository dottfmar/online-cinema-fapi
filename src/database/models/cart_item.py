# isort: skip_file
from __future__ import annotations

import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, relationship
from src.database.models.base import Base

# from src.database import CartModel, MovieModel


class CartItemModel(Base):
    __tablename__ = "cart_items"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True, autoincrement=True)
    cart_id: Mapped[int] = Column(Integer, ForeignKey("carts.id"), nullable=False)
    movie_id: Mapped[int] = Column(Integer, ForeignKey("movies.id"), nullable=False)
    added_at: Mapped[datetime] = Column(DateTime, default=func.now(), nullable=False)

    cart: Mapped["CartModel"] = relationship(  # noqa: F821
        "CartModel", back_populates="items"
    )  # noqa: F821
    movie: Mapped["MovieModel"] = relationship(  # noqa: F821
        "MovieModel", back_populates="items"
    )  # noqa: F821

    __table_args__ = (UniqueConstraint("cart_id", "movie_id", name="uq_cart_movie"),)
