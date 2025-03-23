# isort: skip_file

from datetime import datetime
from enum import Enum

from sqlalchemy import DECIMAL, DateTime
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models.accounts import UserModel
from src.database.models.base import Base
from src.database.models.order_item import OrderItemModel


class OrderStatusEnum(str, Enum):
    PENDING = "Pending"
    PAID = "Paid"
    CANCELED = "Canceled"


class OrderModel(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    user: Mapped["UserModel"] = relationship("UserModel", back_populates="orders")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    status: Mapped[OrderStatusEnum] = mapped_column(
        SQLAlchemyEnum(OrderStatusEnum), nullable=False
    )

    total_amount: Mapped[DECIMAL] = mapped_column(DECIMAL(10, 2), nullable=True)

    order_items: Mapped[list["OrderItemModel"]] = relationship(
        "OrderItemModel", back_populates="order", cascade="all, delete-orphan"
    )

    @classmethod
    def default_order_by(cls):
        return cls.created_at.desc()
