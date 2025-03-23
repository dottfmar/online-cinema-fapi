# isort: skip_file

import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, relationship

from database.models.base import Base
from database.models.cart import CartModel
from database.models.movie import MovieModel


class CartItemModel(Base):
    __tablename__ = "cart_items"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True, autoincrement=True)
    cart_id: Mapped[int] = Column(Integer, ForeignKey("carts.id"), nullable=False)
    movie_id: Mapped[int] = Column(Integer, ForeignKey("movies.id"), nullable=False)
    added_at: Mapped[datetime] = Column(DateTime, default=func.now(), nullable=False)

    cart: Mapped["CartModel"] = relationship("CartModel", back_populates="items")
    movie: Mapped["MovieModel"] = relationship("MovieModel", back_populates="items")

    __table_args__ = (UniqueConstraint("cart_id", "movie_id", name="uq_cart_movie"),)
