# isort: skip_file

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

import services.genre_service as genre_service
from database import GenreModel, MovieModel, MoviesGenresModel, UserModel
from dependencies import get_current_user
from dependencies.database_session import get_db
from schemas.genre import (
    GenreCreateSchema,
    GenreCreateUpdateResponseSchema,
    GenreDetailSchema,
    GenreListSchema,
    GenreUpdateSchema,
    MovieForGenresSchema,
    GenreListResponseSchema,
)
from services.user_service import check_admin_or_moderator

router = APIRouter(prefix="/genres", tags=["Genres"])


@router.get(
    "/",
    response_model=GenreListResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Get a list of genres",
    description=(
        "<h3>This endpoint retrieves a list of genres from the database.</h3> "
        "The response includes details about the genres and the number of movies associated with each genre."
    ),
    responses={
        404: {
            "description": "No genres found.",
            "content": {
                "application/json": {"example": {"detail": "No genres found."}}
            },
        }
    },
)
async def get_genres(db: AsyncSession = Depends(get_db)) -> GenreListResponseSchema:
    """
    Fetch a list of genres from the database (asynchronously) with joined movie data.

    This function retrieves a list of all genres and includes the count of movies
    associated with each genre, using `joinedload` for efficient data fetching.

    :param db: The async SQLAlchemy database session (provided via dependency injection).
    :type db: AsyncSession

    :return: A response containing the list of genres and movie counts.
    :rtype: GenreListResponseSchema

    :raises HTTPException: Raises a 404 error if no genres are found.
    """
    stmt = (
        select(
            GenreModel.id,
            GenreModel.name,
            func.count(MoviesGenresModel.c.movie_id).label("movie_count"),
        )
        .outerjoin(MoviesGenresModel, GenreModel.id == MoviesGenresModel.c.genre_id)
        .group_by(GenreModel.id)
    )

    result = await db.execute(stmt)
    genres = result.all()

    if not genres:
        raise HTTPException(status_code=404, detail="No genres found.")

    genre_list = [
        GenreListSchema(id=row.id, name=row.name, movie_count=row.movie_count or 0)
        for row in genres
    ]

    return GenreListResponseSchema(genres=genre_list)


@router.get(
    "/{genre_id}/",
    response_model=GenreDetailSchema,
    status_code=status.HTTP_200_OK,
    summary="Get details of a genre",
    description=(
        "<h3>This endpoint retrieves detailed information about a specific genre.</h3>"
        "The response includes the genre's name and a list of related movies (if any). "
        "If no movies are associated with the genre, an empty list will be returned."
    ),
    responses={
        404: {
            "description": "Genre not found.",
            "content": {
                "application/json": {"example": {"detail": "Genre not found."}}
            },
        }
    },
)
async def get_genre_by_id(genre_id: int, db: AsyncSession = Depends(get_db)):
    """
    Fetch detailed information about a specific genre, including the related movies.

    This function retrieves the genre's name and a list of movies associated with the genre.
    If no movies are associated with the genre, an empty list will be returned.

    :param genre_id: The ID of the genre to retrieve.
    :type genre_id: int
    :param db: The async SQLAlchemy database session (provided via dependency injection).
    :type db: AsyncSession

    :return: A response containing the genre's details and the list of related movies.
    :rtype: GenreDetailSchema

    :raises HTTPException: Raises a 404 error if the genre is not found.
    """
    stmt = (
        select(GenreModel)
        .outerjoin(MoviesGenresModel, GenreModel.id == MoviesGenresModel.c.genre_id)
        .outerjoin(MovieModel, MovieModel.id == MoviesGenresModel.c.movie_id)
        .where(GenreModel.id == genre_id)
    )

    result = await db.execute(stmt)
    genre = result.scalar_one_or_none()

    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found")

    stmt_movies = (
        select(MovieModel.name)
        .join(MoviesGenresModel, MovieModel.id == MoviesGenresModel.c.movie_id)
        .where(MoviesGenresModel.c.genre_id == genre_id)
    )

    result_movies = await db.execute(stmt_movies)
    movies = result_movies.all()

    related_movies = [MovieForGenresSchema(name=movie.name) for movie in movies]

    return GenreDetailSchema(
        id=genre.id, name=genre.name, related_movies=related_movies
    )


@router.post(
    "/",
    response_model=GenreCreateUpdateResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new genre",
    description=(
        "<h3>This endpoint allows you to create a new genre in the system.</h3>"
        "It checks for the uniqueness of the genre name and creates a new genre if valid."
    ),
    responses={
        400: {
            "description": "Genre with this name already exists.",
            "content": {
                "application/json": {
                    "example": {"detail": "Genre with this name already exists"}
                }
            },
        }
    },
)
async def create_genre(
    genre: GenreCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Create a new genre in the system.

    This endpoint checks for the uniqueness of the genre name and creates a new genre if valid.
    An error will be raised if the genre name already exists in the system.

    :param genre: The data required to create the genre.
    :type genre: GenreCreateSchema
    :param db: The async SQLAlchemy database session (provided via dependency injection).
    :type db: AsyncSession
    :param current_user: The user making the request, validated via dependency injection.
    :type current_user: UserModel

    :return: A response containing the details of the created genre.
    :rtype: GenreCreateUpdateResponseSchema

    :raises HTTPException: Raises a 400 error if the genre name already exists.
    """
    await check_admin_or_moderator(current_user)

    new_genre = await genre_service.create_genre(db, genre)
    if not new_genre:
        raise HTTPException(
            status_code=400, detail="Genre with this name already exists"
        )
    return new_genre


@router.put(
    "/{genre_id}/",
    response_model=GenreCreateUpdateResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Update an existing genre",
    description=(
        "<h3>This endpoint allows you to update an existing genre's information.</h3>"
        "It checks if the genre exists and applies the updated data for the genre."
    ),
    responses={
        404: {
            "description": "Genre not found.",
            "content": {"application/json": {"example": {"detail": "Genre not found"}}},
        }
    },
)
async def update_genre(
    genre_id: int,
    genre: GenreUpdateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Update an existing genre's information.

    This endpoint checks if the genre exists and applies the updated data for the genre.
    If the genre does not exist, a 404 error will be raised.

    :param genre_id: The ID of the genre to update.
    :type genre_id: int
    :param genre: The updated genre data.
    :type genre: GenreUpdateSchema
    :param db: The async SQLAlchemy database session (provided via dependency injection).
    :type db: AsyncSession
    :param current_user: The user making the request, validated via dependency injection.
    :type current_user: UserModel

    :return: A response containing the details of the updated genre.
    :rtype: GenreCreateUpdateResponseSchema

    :raises HTTPException: Raises a 404 error if the genre is not found.
    """
    await check_admin_or_moderator(current_user)

    updated_genre = await genre_service.update_genre(db, genre_id, genre)

    if not updated_genre:
        raise HTTPException(status_code=404, detail="Genre not found")

    return updated_genre


@router.delete(
    "/{genre_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a genre",
    description=(
        "<h3>This endpoint allows you to delete a genre from the system.</h3>"
        "If the genre has related movies, it will not be deleted, and an error will be returned."
    ),
    responses={
        404: {
            "description": "Genre not found or has related movies.",
            "content": {
                "application/json": {
                    "example": {"detail": "Genre not found or has related movies"}
                }
            },
        },
        204: {"description": "Genre deleted successfully."},
    },
)
async def delete_genre(
    genre_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Delete a genre from the system.

    This endpoint allows you to delete a genre, but it will not delete the genre if there are related movies.
    If the genre has related movies, an error will be raised.

    :param genre_id: The ID of the genre to delete.
    :type genre_id: int
    :param db: The async SQLAlchemy database session (provided via dependency injection).
    :type db: AsyncSession
    :param current_user: The user making the request, validated via dependency injection.
    :type current_user: UserModel

    :return: None if the genre is deleted successfully.
    :rtype: None

    :raises HTTPException: Raises a 404 error if the genre is not found or has related movies.
    """
    await check_admin_or_moderator(current_user)

    success = await genre_service.delete_genre(db, genre_id)
    if not success:
        raise HTTPException(
            status_code=404, detail="Genre not found or has related movies"
        )
    return None
