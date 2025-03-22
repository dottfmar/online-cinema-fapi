import os

from sqlalchemy import Integer, ForeignKey, DECIMAL, String, Enum, DateTime, func
from sqlalchemy.orm import relationship, Mapped, mapped_column, declarative_base
import stripe
from src.database.models import User, Order, OrderItem
from datetime import datetime


Base = declarative_base()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )
    order_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("orders.id"),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now()
    )
    status: Mapped[str] = mapped_column(
        Enum(
            "successful",
            "canceled",
            "refunded",
            name="payment_status"
        ),
        default="successful"
    )
    amount: Mapped[float] = mapped_column(
        DECIMAL(10, 2),
        nullable=False
    )
    external_payment_id: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    user = relationship("User", back_populates="payments")
    order = relationship("Order", back_populates="payments")


class PaymentItem(Base):
    __tablename__ = "payment_items"
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )
    payment_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("payments.id"),
        nullable=False
    )
    order_item_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("order_items.id"),
        nullable=False
    )
    price_at_payment: Mapped[float] = mapped_column(
        DECIMAL(10, 2),
        nullable=False
    )

    payment = relationship("Payment", back_populates="items")
    order_item = relationship("OrderItem")

    def __repr__(self):
        return f"<PaymentItem(price_at_payment={self.price_at_payment})>"
