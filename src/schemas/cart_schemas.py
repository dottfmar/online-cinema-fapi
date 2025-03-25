from typing import List, Optional

from pydantic import BaseModel
from sqlalchemy import DateTime


class CartItemSchema(BaseModel):
    id: int
    movie_id: int
    added_at: DateTime

    class Config:
        from_attributes = True


class CartSchema(BaseModel):
    id: int
    user_id: int
    items: Optional[List[CartItemSchema]]

    class Config:
        from_attributes = True


class AddMovieToCartSchema(BaseModel):
    movie_id: int
