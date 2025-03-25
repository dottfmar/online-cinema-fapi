from typing import Optional, Sequence, Type

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database import GenreModel
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
) -> Type[GenreModel] | None:
    genre = await db.get(GenreModel, genre_id)
    if not genre:
        return None

    for key, value in genre_data.dict(exclude_unset=True).items():
        setattr(genre, key, value)

    await db.commit()
    await db.refresh(genre)
    return genre


async def delete_genre(db: AsyncSession, genre_id: int) -> bool:
    genre = await db.get(GenreModel, genre_id)
    if not genre:
        return False
    await db.delete(genre)
    await db.commit()
    return True
