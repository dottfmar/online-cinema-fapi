# isort: skip_file
from datetime import datetime
from typing import List

from fastapi import HTTPException, status
from sqlalchemy import func, select, asc, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import (
    MovieModel,
    NotificationModel,
    CertificationModel,
    StarModel,
    DirectorModel,
    GenreModel,
    RatingModel,
    LikeMovieModel,
    CommentModel,
    LikeCommentModel,
    UserModel,
)
from schemas.genre import GenreCreateUpdateResponseSchema
from schemas.movies import (
    DirectorResponseSchema,
    MovieDetailResponseSchema,
    MovieCreateRequestSchema,
    MovieCreateResponseSchema,
    MovieUpdateRequestSchema,
    NotificationResponseSchema,
    CommentCreateSchema,
)
from schemas.star import StarListSchema


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

    movies_data = [
        {
            "id": movie.id,
            "name": movie.name,
            "year": movie.year,
            "price": str(movie.price),
            "imdb": movie.imdb,
            "votes": movie.votes,
            "description": movie.description,
            "certification": (
                movie.certification.name if movie.certification else None
            ),
        }
        for movie in movies
    ]

    return {
        "movies": movies_data,
        "total_items": total_items,
        "total_pages": total_pages,
        "current_page": page,
    }


async def get_movie_by_id_service(
    movie_id: int, db: AsyncSession
) -> MovieDetailResponseSchema:
    result = await db.execute(
        select(MovieModel)
        .options(
            selectinload(MovieModel.genres),
            selectinload(MovieModel.stars),
            selectinload(MovieModel.directors),
        )
        .filter(MovieModel.id == movie_id)
    )
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    return MovieDetailResponseSchema(
        id=movie.id,
        uuid=movie.uuid,
        name=movie.name,
        year=movie.year,
        time=movie.time,
        imdb=movie.imdb,
        votes=movie.votes,
        meta_score=movie.meta_score,
        gross=movie.gross,
        description=movie.description,
        price=movie.price,
        amount=movie.amount,
        directors=[
            DirectorResponseSchema(id=director.id, name=director.name)
            for director in movie.directors
        ],
        stars=[StarListSchema(id=star.id, name=star.name) for star in movie.stars],
        genres=[
            GenreCreateUpdateResponseSchema(id=genre.id, name=genre.name)
            for genre in movie.genres
        ],
    )


async def create_movie_service(
    movie_data: MovieCreateRequestSchema, db: AsyncSession
) -> MovieCreateResponseSchema:
    existing_stmt = select(MovieModel).where(
        (MovieModel.name == movie_data.name),
        (MovieModel.year == movie_data.year),
    )
    existing_result = await db.execute(existing_stmt)
    existing_movie = existing_result.scalars().first()

    if existing_movie:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Movie already exists"
        )
    try:
        certification_stmt = select(CertificationModel).where(
            CertificationModel.name == movie_data.certification
        )
        certification_result = await db.execute(certification_stmt)
        certification = certification_result.scalars().first()
        if not certification:
            certification = CertificationModel(name=movie_data.certification)
            db.add(certification)
            await db.flush()
        genres = []
        for genre_name in movie_data.genres:
            genre_stmt = select(GenreModel).where(GenreModel.name == genre_name)
            genre_result = await db.execute(genre_stmt)
            genre = genre_result.scalars().first()

            if not genre:
                genre = GenreModel(name=genre_name)
                db.add(genre)
                await db.flush()
            genres.append(genre)
        directors = []
        for director_name in movie_data.directors:
            director_stmt = select(DirectorModel).where(
                DirectorModel.name == director_name
            )
            director_result = await db.execute(director_stmt)
            director = director_result.scalars().first()

            if not director:
                director = DirectorModel(name=director_name)
                db.add(director)
                await db.flush()
            directors.append(director)
        stars = []
        for star_name in movie_data.stars:
            star_stmt = select(StarModel).where(StarModel.name == star_name)
            star_result = await db.execute(star_stmt)
            star = star_result.scalars().first()

            if not star:
                star = StarModel(name=star_name)
                db.add(star)
                await db.flush()
            stars.append(star)
        new_movie = MovieModel(
            name=movie_data.name,
            year=movie_data.year,
            time=movie_data.time,
            imdb=movie_data.imdb,
            votes=movie_data.votes,
            meta_score=movie_data.meta_score,
            gross=movie_data.gross,
            description=movie_data.description,
            price=movie_data.price,
            amount=movie_data.amount,
            is_purchased=False,
            certification=certification,
            genres=genres,
            directors=directors,
            stars=stars,
        )
        db.add(new_movie)
        await db.commit()
        await db.refresh(new_movie, ["genres", "directors", "stars"])

        return MovieCreateResponseSchema.model_validate(new_movie)

    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")


async def update_movie_service(
    movie_id: int, movie_data: MovieUpdateRequestSchema, db: AsyncSession
):
    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    for field, value in movie_data.model_dump(exclude_unset=True).items():
        setattr(movie, field, value)

    try:
        await db.commit()
        await db.refresh(movie)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")

    return {"detail": "Movie updated successfully."}


async def delete_movie_service(movie_id: int, db: AsyncSession):
    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    await db.delete(movie)
    await db.commit()

    return {"detail": "Movie deleted successfully."}


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


async def send_notification(comment_id: int, message: str, db: AsyncSession):
    result = await db.execute(
        select(CommentModel).filter(CommentModel.id == comment_id)
    )
    comment = result.scalars().first()

    if not comment:
        return

    notification = NotificationModel(user_id=comment.user_id, message=message)
    db.add(notification)
    await db.commit()


async def rate_movie_service(
    movie_id: int, rating: int, current_user_id: int, session: AsyncSession
):
    query = select(MovieModel).where(MovieModel.id == movie_id)
    movie = (await session.execute(query)).scalar()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    rating_query = select(RatingModel).where(
        RatingModel.user_id == current_user_id, RatingModel.movie_id == movie_id
    )
    existing_rating = (await session.execute(rating_query)).scalar()

    if existing_rating:
        if existing_rating.rating != rating:
            existing_rating.rating = rating
            await session.commit()
    else:
        new_rating = RatingModel(
            user_id=current_user_id, movie_id=movie_id, rating=rating
        )
        session.add(new_rating)
        await session.commit()

    return {"message": "Rating submitted successfully", "rating": rating}


async def like_movie_service(movie_id: int, user_id: int, session: AsyncSession):
    movie_query = select(MovieModel).where(MovieModel.id == movie_id)
    movie = (await session.execute(movie_query)).scalar()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    like_query = select(LikeMovieModel).where(
        LikeMovieModel.user_id == user_id, LikeMovieModel.movie_id == movie_id
    )
    like = (await session.execute(like_query)).scalar()

    if like:
        like.status = not like.status
    else:
        like = LikeMovieModel(user_id=user_id, movie_id=movie_id, status=True)
        session.add(like)

    await session.commit()
    await session.refresh(like)

    return like


async def create_comment_service(
    movie_id: int, comment_content: str, user_id: int, session: AsyncSession
):
    movie_query = select(MovieModel).where(MovieModel.id == movie_id)
    movie = (await session.execute(movie_query)).scalar()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    new_comment = CommentModel(
        content=comment_content,
        created_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        user_id=user_id,
        movie_id=movie_id,
    )

    session.add(new_comment)
    await session.commit()
    await session.refresh(new_comment)

    return new_comment


async def like_comment_service(
    movie_id: int,
    comment_id: int,
    user_id: int,
    session: AsyncSession,
):
    result = await session.execute(
        select(CommentModel).filter(CommentModel.id == comment_id)
    )
    comment = result.scalars().first()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.movie_id != movie_id:
        raise HTTPException(
            status_code=404, detail="Comment does not belong to the specified movie"
        )

    result = await session.execute(
        select(LikeCommentModel).filter_by(user_id=user_id, comment_id=comment_id)
    )
    like = result.scalars().first()

    if like:
        like.status = not like.status
    else:
        like = LikeCommentModel(user_id=user_id, comment_id=comment_id, status=True)
        session.add(like)

    await session.commit()
    await session.refresh(like)

    truncated_comment_content = (
        comment.content[:50] + "..." if len(comment.content) > 50 else comment.content
    )
    notification_message = f"Your comment '{truncated_comment_content}' has been liked!"

    return like, notification_message


async def get_notifications_service(
    db: AsyncSession, user: UserModel
) -> List[NotificationResponseSchema]:
    result = await db.execute(
        select(NotificationModel).filter(NotificationModel.user_id == user.id)
    )
    notifications = result.scalars().all()

    if not notifications:
        raise HTTPException(status_code=404, detail="No notifications found")
    to_return = [
        NotificationResponseSchema(
            id=notification.id,
            message=notification.message,
            is_read=notification.is_read,
        )
        for notification in notifications
    ]
    return to_return


async def reply_to_comment_service(
    movie_id: int,
    comment_id: int,
    content: CommentCreateSchema,
    user_id: int,
    db: AsyncSession,
):
    result = await db.execute(select(MovieModel).filter(MovieModel.id == movie_id))
    movie = result.scalars().first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    result = await db.execute(
        select(CommentModel).filter(CommentModel.id == comment_id)
    )
    comment = result.scalars().first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    reply_content = f"Reply to comment {comment_id}: {content.content}"

    new_reply = CommentModel(
        content=reply_content,
        created_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        user_id=user_id,
        movie_id=movie_id,
    )

    db.add(new_reply)
    await db.commit()
    await db.refresh(new_reply)

    truncated_comment_content = (
        comment.content[:50] + "..." if len(comment.content) > 50 else comment.content
    )
    notification_message = (
        f"Your comment '{truncated_comment_content}' has received a reply!"
    )

    return new_reply, notification_message
