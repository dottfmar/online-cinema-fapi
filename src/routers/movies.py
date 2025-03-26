# isort: skip_file
# flake8: noqa: F401, E712
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

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
)
from dependencies import get_current_user, get_db
from schemas.movies import (
    CommentCreateSchema,
    CommentResponseSchema,
    LikeResponseSchema,
    MovieCreateRequestSchema,
    MovieListItemSchema,
    MovieListResponseSchema,
    MovieResponseSchema,
    MovieUpdateRequestSchema,
    MovieDetailResponseSchema,
)
from services.movie_service import (
    filter_favorites,
    filter_movies,
    get_movie_by_id,
    get_total_count,
    paginate,
    send_notification,
    sort_favorites,
    sort_movies,
)
from services.user_service import check_admin_or_moderator

router = APIRouter(prefix="/movies", tags=["Movies"])


@router.get("/movies")
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
):
    total_items_query = select(func.count()).select_from(MovieModel)

    if min_price is not None:
        total_items_query = total_items_query.filter(MovieModel.price >= min_price)
    if max_price is not None:
        total_items_query = total_items_query.filter(MovieModel.price <= max_price)

    total_items = (await db.execute(total_items_query)).scalar()

    if total_items == 0:
        return {
            "movies": [],
            "total_items": 0,
            "total_pages": 0,
            "current_page": page,
        }

    query = select(MovieModel)

    if min_price is not None:
        query = query.filter(MovieModel.price >= min_price)
    if max_price is not None:
        query = query.filter(MovieModel.price <= max_price)

    if sort_by:
        if sort_by == "price":
            query = query.order_by(
                MovieModel.price.asc()
                if sort_order == "asc"
                else MovieModel.price.desc()
            )
        elif sort_by == "name":
            query = query.order_by(
                MovieModel.name.asc() if sort_order == "asc" else MovieModel.name.desc()
            )
    total_pages = (total_items + per_page - 1) // per_page
    query = query.offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(query)
    movies = result.scalars().all()

    return {
        "movies": movies,
        "total_items": total_items,
        "total_pages": total_pages,
        "current_page": page,
    }


@router.get("/{movie_id}", response_model=MovieDetailResponseSchema)
async def get_movie_by_id(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(MovieModel).filter(MovieModel.id == movie_id))
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    return movie


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


@router.post(
    "/", response_model=MovieResponseSchema, status_code=status.HTTP_201_CREATED
)
async def create_movie(
    movie_data: MovieCreateRequestSchema,
    session: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    check_admin_or_moderator(current_user)

    existing_movie = await session.execute(
        select(MovieModel).where(
            MovieModel.name == movie_data.name, MovieModel.year == movie_data.year
        )
    )
    if existing_movie.scalar():
        raise HTTPException(
            status_code=400, detail="Movie with this name and year already exists"
        )

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
        certification_id=movie_data.certification_id,
    )
    session.add(new_movie)
    await session.commit()
    await session.refresh(new_movie)

    if movie_data.genres:
        for genre_id in movie_data.genres:
            session.add(MoviesGenresModel(movie_id=new_movie.id, genre_id=genre_id))

    if movie_data.stars:
        for star_id in movie_data.stars:
            session.add(StarsMoviesModel(movie_id=new_movie.id, star_id=star_id))

    if movie_data.directors:
        for director_id in movie_data.directors:
            session.add(
                MoviesDirectorsModel(movie_id=new_movie.id, director_id=director_id)
            )

    await session.commit()
    await session.refresh(new_movie)

    return new_movie


@router.patch(
    "/{movie_id}/", response_model=MovieResponseSchema, status_code=status.HTTP_200_OK
)
async def update_movie(
    movie_id: int,
    movie_data: MovieUpdateRequestSchema,
    session: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    check_admin_or_moderator(current_user)

    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    result = await session.execute(stmt)
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    if movie_data.name is not None:
        movie.name = movie_data.name
    if movie_data.year is not None:
        movie.year = movie_data.year
    if movie_data.time is not None:
        movie.time = movie_data.time
    if movie_data.imdb is not None:
        movie.imdb = movie_data.imdb
    if movie_data.votes is not None:
        movie.votes = movie_data.votes
    if movie_data.meta_score is not None:
        movie.meta_score = movie_data.meta_score
    if movie_data.gross is not None:
        movie.gross = movie_data.gross
    if movie_data.description is not None:
        movie.description = movie_data.description
    if movie_data.price is not None:
        movie.price = movie_data.price
    if movie_data.amount is not None:
        movie.amount = movie_data.amount
    if movie_data.certification_id is not None:
        movie.certification_id = movie_data.certification_id

    if movie_data.genres is not None:
        genres = await session.execute(
            select(GenreModel).filter(GenreModel.id.in_(movie_data.genres))
        )
        movie.genres = genres.scalars().all()

    if movie_data.stars is not None:
        stars = await session.execute(
            select(StarModel).filter(StarModel.id.in_(movie_data.stars))
        )
        movie.stars = stars.scalars().all()

    if movie_data.directors is not None:
        directors = await session.execute(
            select(DirectorModel).filter(DirectorModel.id.in_(movie_data.directors))
        )
        movie.directors = directors.scalars().all()

    await session.commit()
    await session.refresh(movie)

    return movie


@router.delete("/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(
    movie_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    check_admin_or_moderator(current_user)

    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    result = await session.execute(stmt)
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    order_item_stmt = (
        select(OrderItemModel).join(MovieModel).where(MovieModel.id == movie_id)
    )
    order_item_result = await session.execute(order_item_stmt)
    order_items = order_item_result.scalars().all()

    if order_items:
        raise HTTPException(
            status_code=400, detail="Cannot delete movie, it has been purchased"
        )

    await session.delete(movie)
    await session.commit()

    return None
