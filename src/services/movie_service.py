# isort: skip_file

from fastapi import HTTPException
from sqlalchemy import func, select, asc, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import (
    CommentModel,
    MovieModel,
    NotificationModel,
)


def apply_pagination(query, page, per_page, total_items):
    total_pages = (total_items + per_page - 1) // per_page
    query = query.offset((page - 1) * per_page).limit(per_page)

    return query, total_pages


def apply_filters(query, min_price, max_price):
    if min_price is not None:
        query = query.filter(MovieModel.price >= min_price)
    if max_price is not None:
        query = query.filter(MovieModel.price <= max_price)

    return query


def apply_sorting(query, sort_by, sort_order):
    if sort_by:
        if sort_by == "price":
            query = query.order_by(
                asc(MovieModel.price) if sort_order == "asc" else desc(MovieModel.price)
            )
        elif sort_by == "name":
            query = query.order_by(
                asc(MovieModel.name) if sort_order == "asc" else desc(MovieModel.name)
            )

    return query


def apply_search(query, search_term):
    if search_term:
        query = query.filter(MovieModel.name.ilike(f"%{search_term}%"))
    return query


async def get_movies_service(
    db: AsyncSession,
    page: int,
    per_page: int,
    min_price: float = None,
    max_price: float = None,
    sort_by: str = None,
    sort_order: str = "asc",
    search_term: str = None,
):
    total_items_query = select(func.count(MovieModel.id))
    total_items_query = apply_filters(total_items_query, min_price, max_price)
    total_items_query = apply_search(total_items_query, search_term)

    total_items = (await db.execute(total_items_query)).scalar()

    if total_items == 0:
        return {
            "movies": [],
            "total_items": 0,
            "total_pages": 0,
            "current_page": page,
        }

    query = select(MovieModel).options(selectinload(MovieModel.certification))

    query = apply_filters(query, min_price, max_price)

    query = apply_search(query, search_term)

    query = apply_sorting(query, sort_by, sort_order)

    query, total_pages = apply_pagination(query, page, per_page, total_items)

    result = await db.execute(query)
    movies = result.scalars().all()

    # Перетворюємо дані про фільм у формат, що включає всі необхідні поля
    movies_data = [
        {
            "id": movie.id,  # Додаємо id фільму
            "name": movie.name,  # Додаємо назву фільму
            "year": movie.year,  # Додаємо рік
            "price": str(
                movie.price
            ),  # Додаємо ціну, якщо потрібно перетворити в строку
            "imdb": movie.imdb,  # Додаємо рейтинг imdb
            "votes": movie.votes,  # Додаємо кількість голосів
            "description": movie.description,  # Додаємо опис
            "certification": (
                movie.certification.name if movie.certification else None
            ),  # Ім'я сертифікації
        }
        for movie in movies
    ]

    return {
        "movies": movies_data,
        "total_items": total_items,
        "total_pages": total_pages,
        "current_page": page,
    }


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
