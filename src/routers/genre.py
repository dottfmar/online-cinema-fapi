# isort: skip_file
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

import servises.genre as genre_service
from database import GenreModel, MovieModel, UserModel
from dependencies.database_session import get_db
from dependencies.get_user import get_current_user
from schemas.genre import (
    GenreCreateSchema,
    GenreCreateUpdateResponseSchema,
    GenreDetailSchema,
    GenreListSchema,
    GenreUpdateSchema,
    MovieForGenresSchema,
)
from servises.user import check_admin_or_moderator

router = APIRouter(prefix="/genres", tags=["Genres"])


@router.get("/", response_model=List[GenreListSchema])
async def get_genres(db: AsyncSession = Depends(get_db)):
    stmt = (
        select(
            GenreModel.id,
            GenreModel.name,
            func.count(MovieModel.id).label("movie_count"),
        )
        .outerjoin(MovieModel.genres)
        .group_by(GenreModel.id)
    )
    result = await db.execute(stmt)
    genres = result.all()
    return [
        GenreListSchema(id=row.id, name=row.name, movie_count=row.movie_count)
        for row in genres
    ]


@router.get("/{genre_id}/", response_model=GenreDetailSchema)
async def get_genre_by_id(genre_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(GenreModel).where(GenreModel.id == genre_id)
    result = await db.execute(stmt)
    genre = result.scalar_one_or_none()

    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found")

    stmt_movies = select(MovieModel.id, MovieModel.name).where(
        MovieModel.genres.any(id=genre_id)
    )
    result_movies = await db.execute(stmt_movies)
    movies = result_movies.all()

    return GenreDetailSchema(
        id=genre.id,
        name=genre.name,
        related_movies=[
            MovieForGenresSchema(id=movie.id, name=movie.name) for movie in movies
        ],
    )


@router.post("/", response_model=GenreCreateUpdateResponseSchema)
async def create_genre(
    genre: GenreCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    check_admin_or_moderator(current_user)

    new_genre = await genre_service.create_genre(db, genre)
    if not new_genre:
        raise HTTPException(
            status_code=400, detail="Genre with this name already exists"
        )
    return new_genre


@router.put("/{genre_id}/", response_model=GenreCreateUpdateResponseSchema)
async def update_genre(
    genre_id: int,
    genre: GenreUpdateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    check_admin_or_moderator(current_user)

    updated_genre = await genre_service.update_genre(db, genre_id, genre)
    if not updated_genre:
        raise HTTPException(status_code=404, detail="Genre not found")
    return updated_genre


@router.delete("/{genre_id}/", response_model=dict)
async def delete_genre(
    genre_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    check_admin_or_moderator(current_user)

    success = await genre_service.delete_genre(db, genre_id)
    if not success:
        raise HTTPException(status_code=404, detail="Genre not found")
    return {"message": "Genre deleted successfully"}
