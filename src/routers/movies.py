from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from schemas.movies import (
    MovieListResponseSchema,
    MovieListItemSchema,
    MovieDetailSchema,
    MovieCreateSchema,
    MovieUpdateSchema
)

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema, summary="Get a paginated list of movies")
async def get_movie_list(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
) -> MovieListResponseSchema:
    offset = (page - 1) * per_page
    total_items = await db.scalar(select(func.count()).select_from(MovieModel))
    if not total_items:
        raise HTTPException(status_code=404, detail="No movies found.")
    stmt = select(MovieModel).order_by(MovieModel.id).offset(offset).limit(per_page)
    movies = (await db.execute(stmt)).scalars().all()
    return MovieListResponseSchema(
        movies=[MovieListItemSchema.model_validate(m) for m in movies],
        prev_page=f"/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None,
        next_page=f"/movies/?page={page + 1}&per_page={per_page}" if page * per_page < total_items else None,
        total_pages=(total_items + per_page - 1) // per_page,
        total_items=total_items,
    )


@router.post("/movies/", response_model=MovieDetailSchema, status_code=201, summary="Add a new movie")
async def create_movie(movie_data: MovieCreateSchema, db: AsyncSession = Depends(get_db)) -> MovieDetailSchema:
    existing_movie = await db.scalar(select(MovieModel).where(
        (MovieModel.name == movie_data.name) & (MovieModel.date == movie_data.date)
    ))
    if existing_movie:
        raise HTTPException(status_code=409, detail="Movie already exists.")
    movie = MovieModel(**movie_data.dict())
    db.add(movie)
    await db.commit()
    await db.refresh(movie)
    return MovieDetailSchema.model_validate(movie)


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema, summary="Get movie details by ID")
async def get_movie_by_id(movie_id: int, db: AsyncSession = Depends(get_db)) -> MovieDetailSchema:
    movie = await db.scalar(select(MovieModel).options(joinedload(MovieModel.genres)).where(MovieModel.id == movie_id))
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found.")
    return MovieDetailSchema.model_validate(movie)


@router.delete("/movies/{movie_id}/", status_code=204, summary="Delete a movie by ID")
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await db.scalar(select(MovieModel).where(MovieModel.id == movie_id))
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found.")
    await db.delete(movie)
    await db.commit()
    return {"detail": "Movie deleted successfully."}


@router.patch("/movies/{movie_id}/", summary="Update a movie by ID")
async def update_movie(movie_id: int, movie_data: MovieUpdateSchema, db: AsyncSession = Depends(get_db)):
    movie = await db.scalar(select(MovieModel).where(MovieModel.id == movie_id))
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found.")
    for field, value in movie_data.dict(exclude_unset=True).items():
        setattr(movie, field, value)
    try:
        await db.commit()
        await db.refresh(movie)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")
    return {"detail": "Movie updated successfully."}
