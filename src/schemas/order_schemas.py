from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, condecimal

from database.models.order import OrderStatusEnum


class OrderItemSchema(BaseModel):
    id: int
    movie_id: int
    price_at_order: Decimal

    class Config:
        from_attributes = True


class OrderSchema(BaseModel):
    id: int
    user_id: int
    created_at: datetime
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


class OrderStatisticsSchema(BaseModel):
    total_orders: int
    total_amount: Decimal

    class Config:
        orm_mode = True
