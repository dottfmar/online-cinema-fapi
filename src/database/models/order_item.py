# isort: skip_file

from sqlalchemy import DECIMAL, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models.base import Base
from src.database.models.movie import MovieModel
from src.database.models.order import OrderModel


class OrderItemModel(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True, auto_increment=True)

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    order: Mapped[OrderModel] = relationship("OrderModel", back_populates="order_items")

    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"), nullable=False
    )
    movie: Mapped[MovieModel] = relationship("MovieModel", back_populates="order_items")

    price_at_order: Mapped[DECIMAL] = mapped_column(DECIMAL(10, 2), nullable=False)
