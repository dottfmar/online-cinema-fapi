# isort: skip_file
from __future__ import annotations
import os
from datetime import datetime
from typing import List

import stripe
from sqlalchemy import DECIMAL, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.models.base import Base


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

    user: Mapped["UserModel"] = relationship(  # noqa: F821
        "UserModel", back_populates="payments"
    )  # noqa: F821
    order: Mapped["OrderModel"] = relationship(  # noqa: F821
        "OrderModel", back_populates="payments"
    )  # noqa: F821
    items: Mapped[List["PaymentItemModel"]] = relationship(
        "PaymentItemModel", back_populates="payments"
    )


class PaymentItemModel(Base):
    __tablename__ = "payment_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    payment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("payments.id"), nullable=False
    )
    order_item_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("order_items.id"), nullable=False
    )
    price_at_payment: Mapped[DECIMAL] = mapped_column(DECIMAL(10, 2), nullable=False)

    payments: Mapped["PaymentModel"] = relationship(
        "PaymentModel", back_populates="items"
    )
    order_items: Mapped["OrderItemModel"] = relationship("OrderItemModel")  # noqa: F821

    def __repr__(self):
        return f"<PaymentItem(price_at_payment={self.price_at_payment})>"
