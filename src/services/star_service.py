from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import StarModel, StarsMoviesModel


async def get_all_stars(db: AsyncSession) -> list:

    stmt = select(StarModel)
    result = await db.execute(stmt)
    stars = result.scalars().all()
    return stars


async def create_star(db: AsyncSession, name: str) -> StarModel:
    new_star = StarModel(name=name)
    db.add(new_star)
    await db.commit()
    await db.refresh(new_star)
    return new_star


async def update_star(db: AsyncSession, star_id: int, name: str) -> StarModel:
    star = await db.get(StarModel, star_id)
    if not star:
        return None
    star.name = name
    await db.commit()
    await db.refresh(star)
    return star


async def delete_star(db: AsyncSession, star_id: int) -> bool:
    star = await db.get(StarModel, star_id)
    if not star:
        return False

    stmt = select(StarsMoviesModel).filter(StarsMoviesModel.c.star_id == star_id)
    result = await db.execute(stmt)
    related_movies = result.scalars().all()

    if related_movies:
        return False

    await db.delete(star)
    await db.commit()
    return True
