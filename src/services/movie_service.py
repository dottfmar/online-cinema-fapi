# isort: skip_file
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import (
    CommentModel,
    DirectorModel,
    MovieModel,
    NotificationModel,
    StarModel,
)


def paginate(query, page: int, per_page: int):
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)
    return query


def filter_movies(
    query,
    name: Optional[str] = None,
    actor: Optional[str] = None,
    director: Optional[str] = None,
    description: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    max_rating: Optional[float] = None,
    search: Optional[str] = None,
):
    if name:
        query = query.filter(MovieModel.name.ilike(f"%{name}%"))
    if actor:
        query = query.join(MovieModel.stars).filter(StarModel.name.ilike(f"%{actor}%"))
    if director:
        query = query.join(MovieModel.directors).filter(
            DirectorModel.name.ilike(f"%{director}%")
        )
    if description:
        query = query.filter(MovieModel.description.ilike(f"%{description}%"))
    if min_price is not None:
        query = query.filter(MovieModel.price >= min_price)
    if max_price is not None:
        query = query.filter(MovieModel.price <= max_price)
    if min_rating is not None:
        query = query.filter(MovieModel.imdb >= min_rating)
    if max_rating is not None:
        query = query.filter(MovieModel.imdb <= max_rating)
    if search:
        search_filter = or_(
            MovieModel.name.ilike(f"%{search}%"),
            MovieModel.description.ilike(f"%{search}%"),
            StarModel.name.ilike(f"%{search}%"),
            DirectorModel.name.ilike(f"%{search}%"),
        )
        query = query.filter(search_filter)

    return query


def sort_movies(query, sort_by: str, sort_order: str):
    if sort_by not in ["name", "price", "imdb", "year"]:
        raise HTTPException(status_code=400, detail="Invalid sort field.")
    if sort_order not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="Invalid sort order.")

    if sort_order == "asc":
        query = query.order_by(getattr(MovieModel, sort_by).asc())
    else:
        query = query.order_by(getattr(MovieModel, sort_by).desc())

    return query


async def get_total_count(db, query):
    count_stmt = select(func.count(MovieModel.id))
    result_count = await db.execute(count_stmt)
    return result_count.scalar() or 0


async def get_movie_by_id(movie_id: int, session: AsyncSession) -> MovieModel:
    query = (
        select(MovieModel)
        .options(
            selectinload(MovieModel.comments).selectinload(CommentModel.comment_likes)
        )
        .where(MovieModel.id == movie_id)
    )

    result = await session.execute(query)
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    movie.likes_count = len(movie.movie_likes)

    for comment in movie.comments:
        comment.likes_count = len(comment.comment_likes)

    return movie


def filter_favorites(query, name: str, min_price: float, max_price: float):
    if name:
        query = query.filter(MovieModel.name.ilike(f"%{name}%"))
    if min_price is not None:
        query = query.filter(MovieModel.price >= min_price)
    if max_price is not None:
        query = query.filter(MovieModel.price <= max_price)
    return query


def sort_favorites(query, sort_by: str, sort_order: str):
    if sort_by and sort_order:
        if sort_by == "name":
            query = query.order_by(
                MovieModel.name.asc() if sort_order == "asc" else MovieModel.name.desc()
            )
        elif sort_by == "price":
            query = query.order_by(
                MovieModel.price.asc()
                if sort_order == "asc"
                else MovieModel.price.desc()
            )
    return query


async def send_notification(user_id: int, message: str, db: AsyncSession):
    notification = NotificationModel(user_id=user_id, message=message)
    db.add(notification)
    await db.commit()
