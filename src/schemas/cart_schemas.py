from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

# from sqlalchemy import DateTime


class CartItemSchema(BaseModel):
    id: int
    movie_id: int
    added_at: datetime


class CartSchema(BaseModel):
    id: int
    user_id: int
    items: Optional[List[CartItemSchema]]


class AddMovieToCartSchema(BaseModel):
    movie_id: int
