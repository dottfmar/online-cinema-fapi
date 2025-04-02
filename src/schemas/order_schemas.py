from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, condecimal

from database.models.order import OrderStatusEnum


class OrderItemSchema(BaseModel):
    id: Optional[int]
    movie_id: int
    price_at_order: Decimal

    class Config:
        from_attributes = True


class OrderSchema(BaseModel):
    id: Optional[int]
    user_id: int
    created_at: Optional[datetime]
    status: OrderStatusEnum
    total_amount: Optional[Decimal] = None
    order_items: List[OrderItemSchema]

    class Config:
        from_attributes = True


class OrderItemCreateSchema(BaseModel):
    movie_id: int
    price_at_order: condecimal(max_digits=10, decimal_places=2)

    class Config:
        from_attributes = True


class OrderCreateSchema(BaseModel):
    order_items: List[OrderItemCreateSchema]

    class Config:
        from_attributes = True
