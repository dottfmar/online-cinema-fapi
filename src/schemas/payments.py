from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class PaymentStatus(str, Enum):
    successful = "successful"
    canceled = "canceled"
    refunded = "refunded"


class PaymentSchema(BaseModel):
    id: int
    user_id: int
    order_id: int
    amount: float = Field(..., gt=0, description="Total amount in USD")
    external_payment_id: Optional[str] = None
    status: PaymentStatus
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentCreate(BaseModel):
    order_id: int = Field(..., gt=0, description="Order ID")
    total_amount: float = Field(
        ..., gt=0, description="Total amount of the payment in USD"
    )
    token: str = Field(..., min_length=10, description="Token of payment method")


class PaymentResponseSchema(BaseModel):
    message: str
    payment_id: int
