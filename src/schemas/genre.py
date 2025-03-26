from typing import List, Optional

from pydantic import BaseModel


class GenreCreateSchema(BaseModel):
    name: str

    model_config = {"from_attributes": True}


class GenreListSchema(BaseModel):
    id: int
    name: str
    movie_count: int

    model_config = {"from_attributes": True}


class GenreListResponseSchema(BaseModel):
    genres: List[GenreListSchema]


class GenreUpdateSchema(BaseModel):
    name: Optional[str] = None

    model_config = {"from_attributes": True}


class MovieForGenresSchema(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}


class GenreDetailSchema(BaseModel):
    id: int
    name: str
    related_movies: List[MovieForGenresSchema]
    model_config = {"from_attributes": True}


class GenreCreateUpdateResponseSchema(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}
