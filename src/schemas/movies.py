import decimal
import uuid
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

from schemas.genre import GenreCreateUpdateResponseSchema
from schemas.star import StarListSchema


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    year: int
    imdb: float
    price: decimal.Decimal
    certification: Optional[str]

    model_config = {"from_attributes": True}


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int


class DirectorResponseSchema(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class CertificationSchema(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class MovieCreateUpdateResponseSchema(BaseModel):
    id: int
    name: str = Field(..., max_length=255)
    uuid: uuid.UUID
    year: int = Field(..., gt=1888, lt=3000)
    time: int = Field(..., gt=0)
    imdb: float = Field(..., gt=0)
    votes: float = Field(..., gt=0)
    meta_score: float = Optional[float]
    gross: float = Optional[float]
    description: str
    price: float
    amount: Optional[int]
    is_purchased: bool
    certification: CertificationSchema
    genres: List[GenreCreateUpdateResponseSchema]
    stars: List[StarListSchema]
    directors: List[DirectorResponseSchema]

    model_config = {"from_attributes": True}


class MovieCreateRequestSchema(BaseModel):
    name: str = Field(..., max_length=255)
    year: int = Field(..., gt=1888, lt=3000)
    time: int = Field(..., gt=0)
    imdb: float = Field(..., gt=0)
    votes: float = Field(..., gt=0)
    meta_score: float = Field(..., gt=0)
    gross: float = Field(..., gt=0)
    description: str
    price: float = Field(..., gt=0)
    amount: Optional[int] = None
    certification: str
    genres: List[str]
    stars: List[str]
    directors: List[str]

    model_config = {"from_attributes": True}


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = None
    year: Optional[int] = None
    time: Optional[int] = None
    imdb: Optional[float] = None
    votes: Optional[int] = None
    meta_score: Optional[float] = None
    gross: Optional[float] = None
    description: Optional[str] = None
    price: Optional[float] = None
    amount: Optional[int] = None
    is_purchased: Optional[bool] = None
    certification_id: Optional[int] = None
    genre_ids: Optional[List[int]] = None
    star_ids: Optional[List[int]] = None
    director_ids: Optional[List[int]] = None

    model_config = {"from_attributes": True}


class CommentSchema(BaseModel):
    id: int
    content: str
    created_at: str
    user_name: str
    likes_count: int

    model_config = {"from_attributes": True}


class LikeResponseSchema(BaseModel):
    user_id: int
    movie_id: int
    status: bool

    model_config = {"from_attributes": True}


class CommentCreateSchema(BaseModel):
    content: str

    model_config = {"from_attributes": True}


class CommentResponseSchema(BaseModel):
    id: int
    content: str
    created_at: str
    user_id: int
    movie_id: int

    model_config = {"from_attributes": True}


class MovieDetailResponseSchema(BaseModel):
    id: int
    uuid: uuid.UUID
    name: str
    year: int
    time: int
    imdb: float
    votes: int
    meta_score: Optional[float]
    gross: Optional[float]
    description: Optional[str]
    price: Decimal = Field(..., ge=0)
    directors: List[DirectorResponseSchema]
    stars: List[StarListSchema]
    genres: List[GenreCreateUpdateResponseSchema]
    amount: int
