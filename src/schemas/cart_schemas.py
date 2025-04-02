from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

# from sqlalchemy import DateTime


class CartItemSchema(BaseModel):
    id: Optional[int]
    movie_id: int
    added_at: Optional[datetime]

    class Config:
        from_attributes = True


class CartSchema(BaseModel):
    id: Optional[int]
    user_id: int
    items: Optional[List[CartItemSchema]]

    class Config:
        from_attributes = True

    @classmethod
    async def from_orm(cls, orm_object):
        cart = await super().from_orm(orm_object)
        cart.items = [CartItemSchema.from_orm(item) for item in orm_object.items]
        return cart


class AddMovieToCartSchema(BaseModel):
    movie_id: int

    class Config:
        from_attributes = True
