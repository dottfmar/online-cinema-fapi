from datetime import datetime
from enum import Enum
from typing import List

from pydantic import BaseModel


class PaymentStatus(str, Enum):
    SUCCESSFUL = "successful"
    CANCELED = "canceled"
    REFUNDED = "refunded"


class PaymentItemSchema(BaseModel):
    order_item_id: int
    price_at_payment: float

    class Config:
        orm_mode = True


class PaymentSchema(BaseModel):
    id: int
    user_id: int
    order_id: int
    created_at: datetime
    status: PaymentStatus
    amount: float
    external_payment_id: str | None
    payment_items: List[PaymentItemSchema]

    class Config:
        orm_mode = True


class PaymentCreateSchema(BaseModel):
    user_id: int
    order_id: int
    amount: float
    payment_items: List[PaymentItemSchema]
