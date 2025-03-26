import uuid
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

from schemas.genre import GenreDetailSchema
from schemas.star import StarListSchema


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    year: int
    certification: str

    model_config = {"from_attributes": True}


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int


class MovieCreateRequestSchema(BaseModel):
    name: str = Field(..., max_length=255)
    year: int = Field(..., ge=1888)
    time: int = Field(..., gt=0)
    imdb: float = Field(..., ge=0, le=10)
    votes: int = Field(..., ge=0)
    meta_score: Optional[float] = Field(None, ge=0, le=100)
    gross: Optional[float] = Field(None, ge=0)
    description: Optional[str] = Field(None)
    price: Decimal = Field(..., ge=0)
    amount: int = Field(..., ge=0)
    certification_id: int = Field(...)
    genres: List[int] = Field(...)
    stars: List[int] = Field(...)
    directors: List[int] = Field(...)

    model_config = {"from_attributes": True}


class MovieUpdateRequestSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    year: Optional[int] = Field(None, ge=1888)
    time: Optional[int] = Field(None, gt=0)
    imdb: Optional[float] = Field(None, ge=0, le=10)
    votes: Optional[int] = Field(None, ge=0)
    meta_score: Optional[float] = Field(None, ge=0, le=100)
    gross: Optional[float] = Field(None, ge=0)
    description: Optional[str] = Field(None, max_length=1000)
    price: Optional[Decimal] = Field(None, ge=0)
    amount: Optional[int] = Field(None, ge=0)
    certification_id: Optional[int] = Field(None, ge=1)
    genres: Optional[List[int]] = Field(None, min_items=1)
    stars: Optional[List[int]] = Field(None, min_items=1)
    directors: Optional[List[int]] = Field(None, min_items=1)

    model_config = {"from_attributes": True}


class DirectorResponseSchema(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class CommentSchema(BaseModel):
    id: int
    content: str
    created_at: str
    user_name: str
    likes_count: int

    model_config = {"from_attributes": True}


class MovieResponseSchema(BaseModel):
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
    amount: int
    certification_id: int
    genres: List[GenreDetailSchema]
    stars: List[StarListSchema]
    directors: List[DirectorResponseSchema]
    likes_count: int
    comments: List[CommentSchema]

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


class MovieCreateUpdateResponseSchema(BaseModel):
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
    amount: int
    certification_id: int
    genres: List[GenreDetailSchema]
    stars: List[StarListSchema]
    directors: List[DirectorResponseSchema]

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
    amount: int
