from datetime import datetime
from typing import List

from pydantic import BaseModel


class CartItemSchema(BaseModel):
    id: int
    movie_id: int
    added_at: datetime

    class Config:
        from_attributes = True


class CartSchema(BaseModel):
    id: int
    user_id: int
    items: List[CartItemSchema]

    def __init__(self, **data):
        super().__init__(**data)
        # If items is not passed, initialise it with an empty list
        if not hasattr(self, "items"):
            self.items = []

    class Config:
        from_attributes = True


class AddMovieToCartSchema(BaseModel):
    movie_id: int
