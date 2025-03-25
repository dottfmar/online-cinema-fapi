from __future__ import annotations

from sqlalchemy import DECIMAL, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import Base

# from src.database import PaymentItemModel, MovieModel, OrderModel


class OrderItemModel(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    order: Mapped[OrderModel] = relationship(  # noqa: F821
        "OrderModel", back_populates="order_items"
    )  # noqa: F821

    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"), nullable=False
    )
    movie: Mapped[MovieModel] = relationship(  # noqa: F821
        "MovieModel", back_populates="order_items"
    )  # noqa: F821

    price_at_order: Mapped[DECIMAL] = mapped_column(DECIMAL(10, 2), nullable=False)

    payment_items: Mapped[list["PaymentItemModel"]] = relationship(  # noqa: F821
        "PaymentItemModel", back_populates="order_items"
    )
