# isort: skip_file
# flake8: noqa: F401, E712
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload, selectinload

from database import (
    CommentModel,
    DirectorModel,
    FavoritesModel,
    GenreModel,
    LikeCommentModel,
    LikeMovieModel,
    MovieModel,
    MoviesDirectorsModel,
    MoviesGenresModel,
    NotificationModel,
    OrderItemModel,
    RatingModel,
    StarModel,
    StarsMoviesModel,
    UserModel,
    CertificationModel,
)
from dependencies import get_current_user, get_db
from schemas.genre import GenreCreateUpdateResponseSchema
from schemas.movies import (
    CommentCreateSchema,
    CommentResponseSchema,
    LikeResponseSchema,
    MovieListItemSchema,
    MovieListResponseSchema,
    MovieDetailResponseSchema,
    MovieCreateUpdateResponseSchema,
    MovieUpdateSchema,
    DirectorResponseSchema,
    MovieCreateRequestSchema,
)
from schemas.star import StarListSchema
from services.movie_service import (
    filter_favorites,
    send_notification,
    sort_favorites,
    get_movies_service,
    get_movie_by_id_service,
    create_movie_service,
)
from services.user_service import check_admin_or_moderator

router = APIRouter(prefix="/movies", tags=["Movies"])


@router.get("/", response_model=MovieListResponseSchema)
async def get_movies(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number (1-based index)"),
    per_page: int = Query(10, ge=1, le=20, description="Number of items per page"),
    min_price: float = Query(None, description="Filter by minimum price"),
    max_price: float = Query(None, description="Filter by maximum price"),
    sort_by: str = Query(
        None, description="Sort by this field (e.g., 'price', 'name')"
    ),
    sort_order: str = Query(
        "asc", regex="^(asc|desc)$", description="Sort order ('asc' or 'desc')"
    ),
    search_term: str = Query(None, description="Search by movie name"),
):
    return await get_movies_service(
        db, page, per_page, min_price, max_price, sort_by, sort_order, search_term
    )


@router.post("/", response_model=MovieCreateUpdateResponseSchema)
async def create_movie(
    movie_data: MovieCreateRequestSchema,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    await check_admin_or_moderator(current_user)
    return await create_movie_service(movie_data, db)


@router.patch("/movies/{movie_id}", response_model=MovieCreateUpdateResponseSchema)
async def update_movie(
    movie_id: int,
    movie: MovieUpdateSchema,
    db: AsyncSession = Depends(get_db),
    get_current_user: UserModel = Depends(get_current_user),
):
    try:
        await check_admin_or_moderator(get_current_user)

        result = await db.execute(select(MovieModel).filter(MovieModel.id == movie_id))
        movie_to_update = result.scalars().first()

        if not movie_to_update:
            raise HTTPException(status_code=404, detail="Movie not found")

        if movie.name is not None:
            movie_to_update.name = movie.name
        if movie.year is not None:
            movie_to_update.year = movie.year
        if movie.time is not None:
            movie_to_update.time = movie.time
        if movie.imdb is not None:
            movie_to_update.imdb = movie.imdb
        if movie.votes is not None:
            movie_to_update.votes = movie.votes
        if movie.meta_score is not None:
            movie_to_update.meta_score = movie.meta_score
        if movie.gross is not None:
            movie_to_update.gross = movie.gross
        if movie.description is not None:
            movie_to_update.description = movie.description
        if movie.price is not None:
            movie_to_update.price = movie.price
        if movie.amount is not None:
            movie_to_update.amount = movie.amount
        if movie.is_purchased is not None:
            movie_to_update.is_purchased = movie.is_purchased

        if movie.certification_id is not None:
            certification = await db.execute(
                select(CertificationModel).filter(
                    CertificationModel.id == movie.certification_id
                )
            )
            certification_obj = certification.scalars().first()
            if not certification_obj:
                raise HTTPException(status_code=404, detail="Certification not found")
            movie_to_update.certification_id = movie.certification_id

        if movie.genre_ids is not None:
            genres = await db.execute(
                select(GenreModel).filter(GenreModel.id.in_(movie.genre_ids))
            )
            genres_list = genres.scalars().all()
            if len(genres_list) != len(movie.genre_ids):
                raise HTTPException(status_code=404, detail="Some genres not found")
            movie_to_update.genres = genres_list

        if movie.star_ids is not None:
            stars = await db.execute(
                select(StarModel).filter(StarModel.id.in_(movie.star_ids))
            )
            stars_list = stars.scalars().all()
            if len(stars_list) != len(movie.star_ids):
                raise HTTPException(status_code=404, detail="Some stars not found")
            movie_to_update.stars = stars_list

        if movie.director_ids is not None:
            directors = await db.execute(
                select(DirectorModel).filter(DirectorModel.id.in_(movie.director_ids))
            )
            directors_list = directors.scalars().all()
            if len(directors_list) != len(movie.director_ids):
                raise HTTPException(status_code=404, detail="Some directors not found")
            movie_to_update.directors = directors_list

        db.add(movie_to_update)
        await db.commit()
        await db.refresh(movie_to_update)

        response_data = MovieCreateUpdateResponseSchema(
            id=movie_to_update.id,
            name=movie_to_update.name,
            year=movie_to_update.year,
            time=movie_to_update.time,
            imdb=movie_to_update.imdb,
            votes=movie_to_update.votes,
            meta_score=movie_to_update.meta_score,
            gross=movie_to_update.gross,
            description=movie_to_update.description,
            price=movie_to_update.price,
            amount=movie_to_update.amount,
            is_purchased=movie_to_update.is_purchased,
            certification_id=movie_to_update.certification_id,
            certification_name=movie_to_update.certification.name,
            genres=[genre.name for genre in movie_to_update.genres],
            stars=[star.name for star in movie_to_update.stars],
            directors=[director.name for director in movie_to_update.directors],
        )

        return response_data

    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error occurred")


@router.delete("/movies/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    get_current_user: UserModel = Depends(get_current_user),
):
    try:
        await check_admin_or_moderator(get_current_user)

        result = await db.execute(select(MovieModel).filter(MovieModel.id == movie_id))
        movie_to_delete = result.scalars().first()

        if not movie_to_delete:
            raise HTTPException(status_code=404, detail="Movie not found")

        await db.delete(movie_to_delete)
        await db.commit()

        return {}

    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error occurred")


@router.get("/{movie_id}", response_model=MovieDetailResponseSchema)
async def get_movie_by_id(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await get_movie_by_id_service(movie_id, db)


@router.post("/{movie_id}/like", response_model=LikeResponseSchema)
async def like_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(get_current_user),
):
    result = await db.execute(select(MovieModel).filter(MovieModel.id == movie_id))
    movie = result.scalars().first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    result = await db.execute(
        select(LikeMovieModel).filter(
            LikeMovieModel.user_id == user.id, LikeMovieModel.movie_id == movie_id
        )
    )
    like = result.scalars().first()

    if like:
        like.status = not like.status
    else:
        like = LikeMovieModel(user_id=user.id, movie_id=movie_id, status=True)
        db.add(like)
    await db.commit()
    await db.refresh(like)

    return like


@router.post("/{movie_id}/comments", response_model=CommentResponseSchema)
async def create_comment(
    movie_id: int,
    comment_data: CommentCreateSchema,
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(get_current_user),
):
    result = await db.execute(select(MovieModel).filter(MovieModel.id == movie_id))
    movie = result.scalars().first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    new_comment = CommentModel(
        content=comment_data.content,
        created_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),  # Поточний час
        user_id=user.id,
        movie_id=movie_id,
    )

    db.add(new_comment)
    await db.commit()
    await db.refresh(new_comment)

    return new_comment


@router.post("/{movie_id}/comments/{comment_id}/like")
async def like_comment(
    movie_id: int,
    comment_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(get_current_user),
):
    result = await db.execute(
        select(CommentModel).filter(CommentModel.id == comment_id)
    )
    comment = result.scalars().first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.movie_id != movie_id:
        raise HTTPException(
            status_code=404, detail="Comment does not belong to the specified movie"
        )

    result = await db.execute(
        select(LikeCommentModel).filter_by(user_id=user.id, comment_id=comment_id)
    )
    like = result.scalars().first()

    if like:
        like.status = not like.status
    else:
        like = LikeCommentModel(user_id=user.id, comment_id=comment_id, status=True)
        db.add(like)

    await db.commit()
    await db.refresh(like)

    if like.status:
        notification_message = (
            f"Your comment on movie {comment.movie_id} has been liked!"
        )
        background_tasks.add_task(
            send_notification, comment.user_id, notification_message, db
        )

    return {"status": "success", "liked": like.status}


@router.post(
    "/{movie_id}/comments/{comment_id}/reply", response_model=CommentResponseSchema
)
async def reply_to_comment(
    movie_id: int,
    comment_id: int,
    content: CommentCreateSchema,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(get_current_user),
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
        user_id=user.id,
        movie_id=movie_id,
    )

    db.add(new_reply)
    await db.commit()
    await db.refresh(new_reply)

    notification_message = f"Your comment on movie {movie_id} has received a reply!"
    background_tasks.add_task(
        send_notification, comment.user_id, notification_message, db
    )

    return CommentResponseSchema(
        id=new_reply.id,
        content=new_reply.content,
        created_at=new_reply.created_at,
        user_id=new_reply.user_id,
        movie_id=new_reply.movie_id,
    )


@router.get("/notifications")
async def get_notifications(
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(get_current_user),
):
    result = await db.execute(
        select(NotificationModel).filter(NotificationModel.user_id == user.id)
    )
    notifications = result.scalars().all()

    return {"status": "success", "notifications": notifications}


@router.put("/notifications/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(get_current_user),
):
    result = await db.execute(
        select(NotificationModel).filter(
            NotificationModel.id == notification_id,
            NotificationModel.user_id == user.id,
        )
    )
    notification = result.scalars().first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True
    await db.commit()

    return {"status": "success", "message": "Notification marked as read"}


@router.post("/{movie_id}/favorite")
async def add_or_remove_from_favorites(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(get_current_user),
):
    result = await db.execute(select(MovieModel).filter(MovieModel.id == movie_id))
    movie = result.scalars().first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    result = await db.execute(
        select(FavoritesModel).filter(
            FavoritesModel.user_id == user.id, FavoritesModel.movie_id == movie_id
        )
    )
    favorite = result.scalars().first()

    if favorite:
        if favorite.status:
            await db.delete(favorite)
            await db.commit()
            return {"message": "Removed from favorites", "status": False}
        else:
            favorite.status = True
    else:
        favorite = FavoritesModel(user_id=user.id, movie_id=movie_id, status=True)
        db.add(favorite)

    await db.commit()
    await db.refresh(favorite)

    return {"message": "Added to favorites", "status": favorite.status}


@router.get("/favorites")
async def get_favorites(
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Page number (1-based index)"),
    per_page: int = Query(10, ge=1, le=20, description="Number of items per page"),
    name: str = Query(None, description="Filter by movie name"),
    min_price: float = Query(None, description="Filter by minimum price"),
    max_price: float = Query(None, description="Filter by maximum price"),
    sort_by: str = Query(
        None, description="Sort by this field (e.g., 'name', 'price')"
    ),
    sort_order: str = Query(
        "asc", regex="^(asc|desc)$", description="Sort order ('asc' or 'desc')"
    ),
):
    total_items_query = (
        select(func.count())
        .select_from(FavoritesModel)
        .filter(FavoritesModel.user_id == user.id, FavoritesModel.status == True)
    )
    total_items = (await db.execute(total_items_query)).scalar()

    if total_items == 0:
        return {
            "favorite_movies": [],
            "total_items": 0,
            "total_pages": 0,
            "current_page": page,
        }

    query = (
        select(MovieModel)
        .join(FavoritesModel)
        .filter(FavoritesModel.user_id == user.id, FavoritesModel.status == True)
    )

    query = filter_favorites(query, name, min_price, max_price)

    if sort_by:
        query = sort_favorites(query, sort_by, sort_order)
    total_pages = (total_items + per_page - 1) // per_page
    query = query.offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(query)
    favorite_movies = result.scalars().all()

    return {
        "favorite_movies": favorite_movies,
        "total_items": total_items,
        "total_pages": total_pages,
        "current_page": page,
    }


@router.post("/{movie_id}/rate/")
async def rate_movie(
    movie_id: int,
    rating: int = Query(
        ..., ge=1, le=10, description="Rating must be between 1 and 10"
    ),
    session: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    query = select(MovieModel).where(MovieModel.id == movie_id)
    movie = (await session.execute(query)).scalar()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    rating_query = select(RatingModel).where(
        RatingModel.user_id == current_user.id, RatingModel.movie_id == movie_id
    )
    existing_rating = (await session.execute(rating_query)).scalar()

    if existing_rating:
        if existing_rating.rating != rating:
            existing_rating.rating = rating
            await session.commit()
    else:
        new_rating = RatingModel(
            user_id=current_user.id, movie_id=movie_id, rating=rating
        )
        session.add(new_rating)
        await session.commit()

    return {"message": "Rating submitted successfully", "rating": rating}
