# isort: skip_file
# flake8: noqa: F401, E712
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database import (
    FavoritesModel,
    MovieModel,
    NotificationModel,
    UserModel,
)
from dependencies import get_current_user, get_db
from schemas.movies import (
    CommentCreateSchema,
    CommentResponseSchema,
    LikeResponseSchema,
    MovieListResponseSchema,
    MovieDetailResponseSchema,
    MovieCreateResponseSchema,
    MovieCreateRequestSchema,
    MovieUpdateRequestSchema,
    NotificationsResponseSchema,
)
from services.movie_service import (
    filter_favorites,
    send_notification,
    sort_favorites,
    get_movies_service,
    get_movie_by_id_service,
    create_movie_service,
    update_movie_service,
    delete_movie_service,
    rate_movie_service,
    like_movie_service,
    create_comment_service,
    like_comment_service,
    get_notifications_service,
    reply_to_comment_service,
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


@router.post("/", response_model=MovieCreateResponseSchema)
async def create_movie(
    movie_data: MovieCreateRequestSchema,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    await check_admin_or_moderator(current_user)
    return await create_movie_service(movie_data, db)


@router.patch("/movies/{movie_id}", response_model=dict)
async def update_movie(
    movie_id: int,
    movie: MovieUpdateRequestSchema,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    await check_admin_or_moderator(current_user)
    return await update_movie_service(movie_id, movie, db)


@router.delete("/movies/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    await check_admin_or_moderator(current_user)
    return await delete_movie_service(movie_id, db)


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
    return await like_movie_service(movie_id, user.id, db)


@router.post("/{movie_id}/comments", response_model=CommentResponseSchema)
async def create_comment(
    movie_id: int,
    comment_data: CommentCreateSchema,
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(get_current_user),
):
    return await create_comment_service(movie_id, comment_data.content, user.id, db)


@router.post("/{movie_id}/comments/{comment_id}/like")
async def like_comment(
    movie_id: int,
    comment_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(get_current_user),
) -> dict:
    like, notification_message = await like_comment_service(
        movie_id, comment_id, user.id, db
    )

    if like.status:
        background_tasks.add_task(
            send_notification, like.comment_id, notification_message, db
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
    new_reply, notification_message = await reply_to_comment_service(
        movie_id=movie_id,
        comment_id=comment_id,
        content=content,
        user_id=user.id,
        db=db,
    )

    background_tasks.add_task(
        send_notification, new_reply.user_id, notification_message, db
    )

    return CommentResponseSchema(
        id=new_reply.id,
        content=new_reply.content,
        created_at=new_reply.created_at,
        user_id=new_reply.user_id,
        movie_id=new_reply.movie_id,
    )


@router.get("/notifications/", response_model=NotificationsResponseSchema)
async def get_notifications(
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(get_current_user),
):
    notifications = await get_notifications_service(db, user)

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

    notification.is_read = not notification.is_read
    await db.commit()
    await db.refresh(notification)

    return {
        "status": "success",
        "message": f"Notification marked as {'read' if notification.is_read else 'unread'}",
    }


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
) -> dict:
    return await rate_movie_service(movie_id, rating, current_user.id, session)
