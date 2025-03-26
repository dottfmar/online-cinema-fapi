from typing import Optional, Sequence

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database import GenreModel, MovieModel, MoviesGenresModel
from schemas.genre import GenreCreateSchema, GenreUpdateSchema


async def get_genres(db: AsyncSession) -> Sequence[GenreModel]:
    result = await db.execute(select(GenreModel))
    return result.scalars().all()


async def create_genre(
    db: AsyncSession, genre_data: GenreCreateSchema
) -> Optional[GenreModel]:
    new_genre = GenreModel(**genre_data.dict())
    db.add(new_genre)
    try:
        await db.commit()
        await db.refresh(new_genre)
        return new_genre
    except IntegrityError:
        await db.rollback()
        return None


async def update_genre(
    db: AsyncSession, genre_id: int, genre_data: GenreUpdateSchema
) -> Optional[GenreModel]:
    genre = await db.get(GenreModel, genre_id)

    if not genre:
        return None

    for key, value in genre_data.dict(exclude_unset=True).items():
        setattr(genre, key, value)

    try:
        await db.commit()
        await db.refresh(genre)
        return genre
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating genre: {e}")


async def delete_genre(db: AsyncSession, genre_id: int) -> bool:
    genre = await db.get(GenreModel, genre_id)
    if not genre:
        return False

    stmt = (
        select(MovieModel)
        .join(MoviesGenresModel, MovieModel.id == MoviesGenresModel.c.movie_id)
        .where(MoviesGenresModel.c.genre_id == genre_id)
    )
    result = await db.execute(stmt)
    related_movies = result.scalars().all()

    if related_movies:
        return False

    await db.delete(genre)
    await db.commit()
    return True
