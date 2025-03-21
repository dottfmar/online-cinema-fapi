from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, field_validator

from database.models.movies import MovieStatusEnum


class GenreSchema(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True,
    }


class StarSchema(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True,
    }


class DirectorSchema(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True,
    }


class CertificationSchema(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True,
    }


class MovieBaseSchema(BaseModel):
    name: str = Field(..., max_length=255)
    year: int = Field(..., ge=1900, le=datetime.now().year + 1)  # Валідація року
    time: int = Field(..., ge=1)  # Тривалість у хвилинах
    imdb: float = Field(..., ge=0, le=10)  # Оцінка IMDb
    votes: int = Field(..., ge=0)  # Кількість голосів
    meta_score: Optional[float] = Field(None, ge=0, le=100)
    gross: Optional[float] = Field(None, ge=0)  # Дохід фільму
    price: float = Field(..., ge=0)  # Ціна перегляду
    description: str
    status: MovieStatusEnum

    model_config = {
        "from_attributes": True
    }


class MovieDetailSchema(MovieBaseSchema):
    id: int
    certification: CertificationSchema
    genres: List[GenreSchema]
    stars: List[StarSchema]
    directors: List[DirectorSchema]

    model_config = {
        "from_attributes": True,
    }


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    year: int
    imdb: float
    description: str

    model_config = {
        "from_attributes": True,
    }


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int

    model_config = {
        "from_attributes": True,
    }


class MovieCreateSchema(BaseModel):
    name: str
    year: int = Field(..., ge=1900, le=datetime.now().year + 1)
    time: int = Field(..., ge=1)
    imdb: float = Field(..., ge=0, le=10)
    votes: int = Field(..., ge=0)
    meta_score: Optional[float] = Field(None, ge=0, le=100)
    gross: Optional[float] = Field(None, ge=0)
    price: float = Field(..., ge=0)
    description: str
    status: MovieStatusEnum
    certification_id: int
    genres: List[int]
    stars: List[int]
    directors: List[int]

    model_config = {
        "from_attributes": True,
    }

    @field_validator("year")
    @classmethod
    def validate_year(cls, value):
        current_year = datetime.now().year
        if value > current_year + 1:
            raise ValueError(f"The year cannot be greater than {current_year + 1}.")
        return value


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = None
    year: Optional[int] = Field(None, ge=1900, le=datetime.now().year + 1)
    time: Optional[int] = Field(None, ge=1)
    imdb: Optional[float] = Field(None, ge=0, le=10)
    votes: Optional[int] = Field(None, ge=0)
    meta_score: Optional[float] = Field(None, ge=0, le=100)
    gross: Optional[float] = Field(None, ge=0)
    price: Optional[float] = Field(None, ge=0)
    description: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    certification_id: Optional[int] = None
    genres: Optional[List[int]] = None
    stars: Optional[List[int]] = None
    directors: Optional[List[int]] = None

    model_config = {
        "from_attributes": True,
    }
