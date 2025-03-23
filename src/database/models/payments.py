# isort: skip_file

import os
from datetime import datetime

import stripe
from sqlalchemy import DECIMAL, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship

from src.database.models.accounts import UserModel
from src.database.models.order import OrderModel
from src.database.models.order_item import OrderItemModel  # noqa: F401

Base = declarative_base()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


class PaymentModel(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orders.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    status: Mapped[str] = mapped_column(
        Enum("successful", "canceled", "refunded", name="payment_status"),
        default="successful",
    )
    amount: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    external_payment_id: Mapped[str | None] = mapped_column(String, nullable=True)

    user: Mapped["UserModel"] = relationship("UserModel", back_populates="payments")
    order: Mapped["OrderModel"] = relationship("OrderModel", back_populates="payments")


class PaymentItemModel(Base):
    __tablename__ = "payment_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    payment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("payments.id"), nullable=False
    )
    order_item_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("order_items.id"), nullable=False
    )
    price_at_payment: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)

    payment = relationship("PaymentModel", back_populates="items")
    order_item = relationship("OrderItemModel")

    def __repr__(self):
        return f"<PaymentItem(price_at_payment={self.price_at_payment})>"
