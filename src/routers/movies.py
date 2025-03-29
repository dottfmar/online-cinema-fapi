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


@router.get(
    "/",
    response_model=MovieListResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Get a list of movies",
    description=(
        "<h3>This endpoint retrieves a list of movies, with options to filter and sort the results.</h3>"
        "The response includes paginated results based on the provided query parameters."
    ),
    responses={
        200: {
            "description": "A list of movies matching the provided filters and pagination.",
            "content": {
                "application/json": {
                    "example": {
                        "movies": [
                            {
                                "id": 1,
                                "name": "Movie 1",
                                "year": 2012,
                                "imdb": 5,
                                "price": "12.99",
                                "certification": "G",
                            },
                        ],
                        "prev_page": "null",
                        "next_page": 2,
                        "current_page": 1,
                        "total_pages": 50,
                        "total_items": 100,
                    }
                }
            },
        },
        400: {
            "description": "Invalid query parameters.",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid query parameter 'sort_by'."}
                }
            },
        },
    },
)
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
    """
    Fetch a paginated list of movies, with optional filtering, sorting, and searching.

    This endpoint retrieves movies with options to filter by price range, sort by fields like
    price or name, and search by movie name. Pagination is applied based on the 'page' and
    'per_page' parameters.

    :param db: The async SQLAlchemy database session (provided via dependency injection).
    :type db: AsyncSession
    :param page: The page number for pagination (1-based index). Defaults to 1.
    :type page: int
    :param per_page: The number of items per page (between 1 and 20). Defaults to 10.
    :type per_page: int
    :param min_price: The minimum price filter for the movies. Optional.
    :type min_price: float
    :param max_price: The maximum price filter for the movies. Optional.
    :type max_price: float
    :param sort_by: The field to sort the results by (e.g., 'price', 'name'). Optional.
    :type sort_by: str
    :param sort_order: The sorting order, either 'asc' for ascending or 'desc' for descending. Defaults to 'asc'.
    :type sort_order: str
    :param search_term: A search term to filter movies by their name. Optional.
    :type search_term: str

    :return: A paginated list of movies matching the specified filters.
    :rtype: MovieListResponseSchema

    :raises HTTPException: Raises a 400 error if query parameters are invalid.
    """
    return await get_movies_service(
        db, page, per_page, min_price, max_price, sort_by, sort_order, search_term
    )


@router.post(
    "/",
    response_model=MovieCreateResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new movie",
    description=(
        "<h3>This endpoint allows you to create a new movie in the system.</h3>"
        "The movie data provided will be validated, and the movie will be added to the database."
    ),
    responses={
        201: {
            "description": "The movie was created successfully.",
        },
        400: {
            "description": "Invalid movie data.",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid or missing movie data."}
                }
            },
        },
        403: {
            "description": "Permission denied. Only admins or moderators can create a movie.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "You do not have permission to create a movie."
                    }
                }
            },
        },
    },
)
async def create_movie(
    movie_data: MovieCreateRequestSchema,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Create a new movie in the system.

    This endpoint allows an authenticated user with appropriate permissions (admin or moderator)
    to create a new movie in the system by providing the required movie data.

    :param movie_data: The movie data used to create the new movie.
    :type movie_data: MovieCreateRequestSchema
    :param db: The async SQLAlchemy database session (provided via dependency injection).
    :type db: AsyncSession
    :param current_user: The authenticated user making the request, validated via dependency injection.
    :type current_user: UserModel

    :return: A response containing the details of the created movie.
    :rtype: MovieCreateResponseSchema

    :raises HTTPException: Raises a 403 error if the current user does not have permission to create a movie.
    :raises HTTPException: Raises a 400 error if the provided movie data is invalid.
    """
    await check_admin_or_moderator(current_user)
    return await create_movie_service(movie_data, db)


@router.patch(
    "/movies/{movie_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Update an existing movie",
    description=(
        "<h3>This endpoint allows you to update an existing movie in the system.</h3>"
        "The movie data will be validated and the movie will be updated based on the provided information."
    ),
    responses={
        200: {
            "description": "The movie was successfully updated.",
        },
        400: {
            "description": "Invalid movie data provided.",
            "content": {
                "application/json": {"example": {"detail": "Invalid movie data."}}
            },
        },
        403: {
            "description": "Permission denied. Only admins or moderators can update a movie.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "You do not have permission to update this movie."
                    }
                }
            },
        },
        404: {
            "description": "Movie not found.",
            "content": {
                "application/json": {"example": {"detail": "Movie not found."}}
            },
        },
    },
)
async def update_movie(
    movie_id: int,
    movie: MovieUpdateRequestSchema,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Update an existing movie in the system.

    This endpoint allows an authenticated user with appropriate permissions (admin or moderator)
    to update the information of an existing movie. If the movie is not found or if the data is invalid,
    the appropriate error response will be returned.

    :param movie_id: The ID of the movie to update.
    :type movie_id: int
    :param movie: The updated movie data.
    :type movie: MovieUpdateRequestSchema
    :param db: The async SQLAlchemy database session (provided via dependency injection).
    :type db: AsyncSession
    :param current_user: The authenticated user making the request, validated via dependency injection.
    :type current_user: UserModel

    :return: A dictionary indicating the success of the update operation.
    :rtype: dict

    :raises HTTPException: Raises a 403 error if the current user does not have permission to update the movie.
    :raises HTTPException: Raises a 404 error if the movie is not found.
    :raises HTTPException: Raises a 400 error if the provided movie data is invalid.
    """
    await check_admin_or_moderator(current_user)
    return await update_movie_service(movie_id, movie, db)


@router.delete(
    "/movies/{movie_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a movie",
    description=(
        "<h3>This endpoint allows you to delete a movie from the system.</h3>"
        "If the movie exists and the user has proper permissions, the movie will be removed."
    ),
    responses={
        204: {
            "description": "The movie was successfully deleted.",
        },
        403: {
            "description": "Permission denied. Only admins or moderators can delete a movie.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "You do not have permission to delete this movie."
                    }
                }
            },
        },
        404: {
            "description": "Movie not found.",
            "content": {
                "application/json": {"example": {"detail": "Movie not found."}}
            },
        },
    },
)
async def delete_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Delete a movie from the system.

    This endpoint allows an authenticated user with appropriate permissions (admin or moderator)
    to delete an existing movie from the system. If the movie is not found or the user does not
    have the necessary permissions, an appropriate error response will be returned.

    :param movie_id: The ID of the movie to delete.
    :type movie_id: int
    :param db: The async SQLAlchemy database session (provided via dependency injection).
    :type db: AsyncSession
    :param current_user: The authenticated user making the request, validated via dependency injection.
    :type current_user: UserModel

    :return: No content if the movie was successfully deleted.
    :rtype: None

    :raises HTTPException: Raises a 403 error if the current user does not have permission to delete the movie.
    :raises HTTPException: Raises a 404 error if the movie is not found.
    """
    await check_admin_or_moderator(current_user)
    return await delete_movie_service(movie_id, db)


@router.get(
    "/{movie_id}",
    response_model=MovieDetailResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Get details of a movie",
    description=(
        "<h3>This endpoint retrieves detailed information about a specific movie.</h3>"
        "The response includes the movie's details based on the provided movie ID."
    ),
    responses={
        200: {
            "description": "Detailed information about the movie.",
        },
        404: {
            "description": "Movie not found.",
            "content": {
                "application/json": {"example": {"detail": "Movie not found."}}
            },
        },
    },
)
async def get_movie_by_id(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Fetch detailed information about a specific movie using its ID.

    This endpoint retrieves the details of a movie, such as its title, description, and other
    relevant information, by using the provided movie ID. If the movie is not found, a 404 error
    will be returned.

    :param movie_id: The ID of the movie to retrieve.
    :type movie_id: int
    :param db: The async SQLAlchemy database session (provided via dependency injection).
    :type db: AsyncSession

    :return: A response containing the details of the movie.
    :rtype: MovieDetailResponseSchema

    :raises HTTPException: Raises a 404 error if the movie with the provided ID is not found.
    """
    return await get_movie_by_id_service(movie_id, db)


@router.post(
    "/{movie_id}/like",
    response_model=LikeResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Like a movie",
    description=(
        "<h3>This endpoint allows a user to like a specific movie.</h3>"
        "The like action is associated with the authenticated user and the provided movie ID."
    ),
    responses={
        200: {
            "description": "The movie was successfully liked.",
        },
        400: {
            "description": "Invalid movie ID or already liked.",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid movie ID or already liked."}
                }
            },
        },
        404: {
            "description": "Movie not found.",
            "content": {
                "application/json": {"example": {"detail": "Movie not found."}}
            },
        },
        403: {
            "description": "Permission denied. Only authenticated users can like a movie.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "You need to be authenticated to like a movie."
                    }
                }
            },
        },
    },
)
async def like_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(get_current_user),
):
    """
    Like a movie by the authenticated user.

    This endpoint allows an authenticated user to like a specific movie. The like action is
    tied to the user’s account, and the movie ID must be valid. If the movie ID is not found
    or the user has already liked the movie, an appropriate error response will be returned.

    :param movie_id: The ID of the movie to like.
    :type movie_id: int
    :param db: The async SQLAlchemy database session (provided via dependency injection).
    :type db: AsyncSession
    :param user: The authenticated user making the request, validated via dependency injection.
    :type user: UserModel

    :return: A response indicating the success of the like action.
    :rtype: LikeResponseSchema

    :raises HTTPException: Raises a 404 error if the movie is not found.
    :raises HTTPException: Raises a 400 error if the like action is invalid or already performed.
    :raises HTTPException: Raises a 403 error if the user is not authenticated.
    """
    return await like_movie_service(movie_id, user.id, db)


@router.post(
    "/{movie_id}/comments",
    response_model=CommentResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create a comment on a movie",
    description=(
        "<h3>This endpoint allows an authenticated user to create a comment on a specific movie.</h3>"
        "The comment is associated with the provided movie ID and the authenticated user's ID."
    ),
    responses={
        201: {
            "description": "The comment was successfully created.",
        },
        400: {
            "description": "Invalid comment data or movie ID.",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid comment data or movie ID."}
                }
            },
        },
        404: {
            "description": "Movie not found.",
            "content": {
                "application/json": {"example": {"detail": "Movie not found."}}
            },
        },
        403: {
            "description": "Permission denied. Only authenticated users can comment on a movie.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "You need to be authenticated to comment on a movie."
                    }
                }
            },
        },
    },
)
async def create_comment(
    movie_id: int,
    comment_data: CommentCreateSchema,
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(get_current_user),
):
    """
    Create a comment on a movie by the authenticated user.

    This endpoint allows an authenticated user to create a comment for a movie. The movie ID
    must be valid, and the comment is tied to the user's account. If the movie ID is not found
    or the comment data is invalid, an appropriate error response will be returned.

    :param movie_id: The ID of the movie to comment on.
    :type movie_id: int
    :param comment_data: The content of the comment to be created.
    :type comment_data: CommentCreateSchema
    :param db: The async SQLAlchemy database session (provided via dependency injection).
    :type db: AsyncSession
    :param user: The authenticated user making the request, validated via dependency injection.
    :type user: UserModel

    :return: A response containing the details of the created comment.
    :rtype: CommentResponseSchema

    :raises HTTPException: Raises a 404 error if the movie is not found.
    :raises HTTPException: Raises a 400 error if the comment data or movie ID is invalid.
    :raises HTTPException: Raises a 403 error if the user is not authenticated.
    """
    return await create_comment_service(movie_id, comment_data.content, user.id, db)


@router.post(
    "/{movie_id}/comments/{comment_id}/like",
    status_code=status.HTTP_200_OK,
    summary="Like a comment on a movie",
    description=(
        "<h3>This endpoint allows an authenticated user to like a specific comment on a movie.</h3>"
        "If the comment is successfully liked, a background task will send a notification."
    ),
    responses={
        200: {
            "description": "The comment was successfully liked.",
            "content": {
                "application/json": {"example": {"status": "success", "liked": True}}
            },
        },
        400: {
            "description": "Invalid movie ID or comment ID.",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid movie ID or comment ID."}
                }
            },
        },
        404: {
            "description": "Movie or comment not found.",
            "content": {
                "application/json": {
                    "example": {"detail": "Movie or comment not found."}
                }
            },
        },
        403: {
            "description": "Permission denied. Only authenticated users can like a comment.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "You need to be authenticated to like a comment."
                    }
                }
            },
        },
    },
)
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
    "/{movie_id}/comments/{comment_id}/reply",
    response_model=CommentResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Reply to a comment on a movie",
    description=(
        "<h3>This endpoint allows an authenticated user to reply to a specific comment on a movie.</h3>"
        "Once the reply is successfully posted, a background task will be triggered to send a notification to "
        "the user who created the original comment."
    ),
    responses={
        201: {
            "description": "The reply was successfully created.",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "content": "Great movie!",
                        "created_at": "2025-03-29T10:00:00",
                        "user_id": 2,
                        "movie_id": 1,
                    }
                }
            },
        },
        400: {
            "description": "Invalid movie ID or comment ID.",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid movie ID or comment ID."}
                }
            },
        },
        404: {
            "description": "Movie or comment not found.",
            "content": {
                "application/json": {
                    "example": {"detail": "Movie or comment not found."}
                }
            },
        },
        403: {
            "description": "Permission denied. Only authenticated users can reply to a comment.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "You need to be authenticated to reply to a comment."
                    }
                }
            },
        },
    },
)
async def reply_to_comment(
    movie_id: int,
    comment_id: int,
    content: CommentCreateSchema,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(get_current_user),
):
    """
    Allows an authenticated user to reply to a specific comment on a movie.

    This endpoint accepts a movie ID, comment ID, and the content of the reply. It allows the authenticated
    user to reply to the specified comment. Once the reply is posted, a background task is triggered to
    send a notification to the user who made the original comment.

    Args:
        movie_id (int): The ID of the movie the comment belongs to.
        comment_id (int): The ID of the comment to reply to.
        content (CommentCreateSchema): The content of the reply to the comment.
        background_tasks (BackgroundTasks): The background task handler to send notifications.
        db (AsyncSession): The database session.
        user (UserModel): The authenticated user who is replying to the comment.

    Returns:
        CommentResponseSchema: The newly created reply to the comment, including metadata like ID, content,
        user ID, and timestamp.

    Responses:
        201: The reply was successfully created.
        400: Invalid movie ID or comment ID.
        404: Movie or comment not found.
        403: Permission denied (user must be authenticated).
    """
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


@router.get(
    "/notifications/",
    response_model=NotificationsResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Get notifications for the authenticated user",
    description=(
        "<h3>This endpoint allows an authenticated user to retrieve all of their notifications.</h3>"
        "The notifications may include alerts about new comments, replies, likes, or other events related "
        "to the user's activity on the platform."
    ),
    responses={
        200: {
            "description": "The notifications were successfully retrieved.",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "notifications": [
                            {
                                "id": 1,
                                "message": "Your comment on 'Movie Title' has received a reply.",
                                "created_at": "2025-03-29T10:00:00",
                                "read": False,
                            },
                            {
                                "id": 2,
                                "message": "Your movie 'Another Movie' has been liked.",
                                "created_at": "2025-03-28T09:30:00",
                                "read": True,
                            },
                        ],
                    }
                }
            },
        },
        401: {
            "description": "Permission denied. Only authenticated users can retrieve notifications.",
            "content": {
                "application/json": {"example": {"detail": "Not authenticated."}}
            },
        },
    },
)
async def get_notifications(
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(get_current_user),
):
    """
    Retrieves all notifications for the authenticated user.

    This endpoint fetches notifications related to the user's activity, such as replies, likes, and other actions.
    Notifications are returned in an ordered list, with the most recent notifications first.

    Args:
        db (AsyncSession): The database session used to query notification data.
        user (UserModel): The authenticated user whose notifications are to be fetched.

    Returns:
        dict: A dictionary containing the status of the operation and a list of notifications.

    Responses:
        200: Successfully retrieved notifications.
        401: User not authenticated.
    """
    notifications = await get_notifications_service(db, user)

    return {"status": "success", "notifications": notifications}


@router.put(
    "/notifications/{notification_id}/read",
    status_code=status.HTTP_200_OK,
    summary="Mark a notification as read/unread",
    description=(
        "<h3>This endpoint allows an authenticated user to toggle the read status of a specific notification.</h3>"
        "The notification will be marked as read if it is currently unread, and as unread if it is currently read."
    ),
    responses={
        200: {
            "description": "The notification was successfully marked as read/unread.",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "message": "Notification marked as read",
                    }
                }
            },
        },
        401: {
            "description": "Unauthorized. Only authenticated users can mark notifications as read/unread.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "You need to be authenticated to mark notifications as read/unread."
                    }
                }
            },
        },
        404: {
            "description": "Notification not found.",
            "content": {
                "application/json": {"example": {"detail": "Notification not found"}}
            },
        },
    },
)
async def mark_notification_as_read(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(get_current_user),
):
    """
    Marks a specific notification as read or unread for the authenticated user.

    This endpoint toggles the read status of a notification. If the notification is currently unread, it will be marked as read,
    and vice versa. It ensures that only the owner of the notification (the authenticated user) can update the status of the notification.

    Args:
        notification_id (int): The ID of the notification to be marked as read/unread.
        db (AsyncSession): The database session used to query and update the notification status.
        user (UserModel): The authenticated user who owns the notification.

    Returns:
        dict: A dictionary containing the status of the operation and a message indicating whether the notification is marked as read or unread.

    Responses:
        200: Successfully marked the notification as read/unread.
        401: Unauthorized if the user is not authenticated.
        404: The notification was not found for the authenticated user.
    """
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


@router.post(
    "/{movie_id}/favorite",
    status_code=status.HTTP_200_OK,
    summary="Add or remove a movie from favorites",
    description=(
        "<h3>This endpoint allows an authenticated user to add or remove a movie from their favorites.</h3>"
        "If the movie is already in the user's favorites, it will be removed. If it is not in their favorites, "
        "it will be added."
    ),
    responses={
        200: {
            "description": "The movie was successfully added or removed from favorites.",
            "content": {
                "application/json": {
                    "example": {"message": "Added to favorites", "status": True}
                }
            },
        },
        401: {
            "description": "Unauthorized. Only authenticated users can add or remove movies from favorites.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "You need to be authenticated to add/remove movies from favorites."
                    }
                }
            },
        },
        404: {
            "description": "Movie not found.",
            "content": {"application/json": {"example": {"detail": "Movie not found"}}},
        },
    },
)
async def add_or_remove_from_favorites(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(get_current_user),
):
    """
    Add or remove a movie from the user's favorites list.

    This endpoint allows a user to toggle whether a movie is in their favorites. If the movie is already in their
    favorites, it will be removed. If it is not in their favorites, it will be added.

    Args:
        movie_id (int): The ID of the movie to be added or removed from favorites.
        db (AsyncSession): The database session used for querying and modifying the favorites.
        user (UserModel): The authenticated user making the request.

    Returns:
        dict: A dictionary containing a message and the status of the movie in the favorites list.

    Responses:
        200: The movie was successfully added or removed from favorites.
        401: Unauthorized if the user is not authenticated.
        404: The movie was not found in the database.
    """
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


@router.get(
    "/favorites",
    status_code=status.HTTP_200_OK,
    summary="Get the user's favorite movies",
    description=(
        "<h3>This endpoint retrieves the list of movies that the authenticated user has marked as favorites.</h3>"
        "You can paginate through the results, apply filters (like movie name, price range), and sort the list."
    ),
    responses={
        200: {
            "description": "The list of favorite movies was successfully retrieved.",
            "content": {
                "application/json": {
                    "example": {
                        "favorite_movies": [
                            {"id": 1, "name": "Movie A", "price": 9.99},
                            {"id": 2, "name": "Movie B", "price": 12.99},
                        ],
                        "total_items": 2,
                        "total_pages": 1,
                        "current_page": 1,
                    }
                }
            },
        },
        401: {
            "description": "Unauthorized. Only authenticated users can access their favorite movies.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "You need to be authenticated to get your favorite movies."
                    }
                }
            },
        },
        404: {
            "description": "No favorite movies found for the user.",
            "content": {
                "application/json": {"example": {"detail": "No favorite movies found."}}
            },
        },
    },
)
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
    """
    Get a paginated list of the authenticated user's favorite movies.

    This endpoint retrieves a list of movies that the user has marked as favorites. It supports pagination, filtering,
    and sorting of the results based on movie name, price range, and other criteria.

    Args:
        db (AsyncSession): The database session to interact with the database.
        user (UserModel): The authenticated user for whom the favorites are being retrieved.
        page (int): The page number for pagination (1-based index).
        per_page (int): The number of items to display per page (max 20).
        name (str): Optional filter for movie name.
        min_price (float): Optional filter for minimum price.
        max_price (float): Optional filter for maximum price.
        sort_by (str): Optional field to sort the results by ('name', 'price').
        sort_order (str): Optional sorting order ('asc' or 'desc').

    Returns:
        dict: A dictionary containing the list of favorite movies, pagination information, and applied filters.

    Responses:
        200: A list of favorite movies with pagination data.
        401: Unauthorized if the user is not authenticated.
        404: If no favorite movies are found for the user.
    """
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


@router.post(
    "/{movie_id}/rate/",
    status_code=status.HTTP_200_OK,
    summary="Rate a movie",
    description=(
        "<h3>This endpoint allows an authenticated user to rate a movie between 1 and 10.</h3>"
        "The user can rate a movie once. If a rating already exists, it will be updated."
    ),
    responses={
        200: {
            "description": "The movie was successfully rated.",
            "content": {
                "application/json": {"example": {"status": "success", "rating": 8}}
            },
        },
        400: {
            "description": "Invalid rating. Rating must be between 1 and 10.",
            "content": {
                "application/json": {
                    "example": {"detail": "Rating must be between 1 and 10."}
                }
            },
        },
        401: {
            "description": "Unauthorized. Only authenticated users can rate a movie.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "You need to be authenticated to rate a movie."
                    }
                }
            },
        },
        404: {
            "description": "Movie not found.",
            "content": {
                "application/json": {"example": {"detail": "Movie not found."}}
            },
        },
    },
)
async def rate_movie(
    movie_id: int,
    rating: int = Query(
        ..., ge=1, le=10, description="Rating must be between 1 and 10"
    ),
    session: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> dict:
    """
    Rate a movie between 1 and 10.

    This endpoint allows the authenticated user to rate a movie. If a rating for the movie already exists, it will be updated with the new rating.
    The rating value must be an integer between 1 and 10.

    Args:
        movie_id (int): The ID of the movie to be rated.
        rating (int): The rating value between 1 and 10.
        session (AsyncSession): The database session to interact with the database.
        current_user (UserModel): The authenticated user who is rating the movie.

    Returns:
        dict: A dictionary containing the status of the operation and the updated rating.

    Responses:
        200: Successfully rated the movie.
        400: If the rating value is not between 1 and 10.
        401: Unauthorized if the user is not authenticated.
        404: If the movie with the given ID is not found.
    """
    return await rate_movie_service(movie_id, rating, current_user.id, session)
