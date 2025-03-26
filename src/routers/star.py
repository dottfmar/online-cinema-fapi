from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import UserModel
from dependencies import get_current_user, get_db
from schemas.star import StarCreateSchema, StarListSchema, StarUpdateSchema
from services import star_service
from services.star_service import create_star, get_all_stars, update_star
from services.user_service import check_admin_or_moderator

router = APIRouter(prefix="/stars", tags=["Stars"])


@router.get(
    "/",
    response_model=List[StarListSchema],
    status_code=status.HTTP_200_OK,
    summary="Get a list of stars",
    description=(
        "<h3>This endpoint retrieves a list of all stars from the database.</h3>"
        "The response includes basic information about each star."
    ),
    responses={
        404: {
            "description": "No stars found.",
            "content": {"application/json": {"example": {"detail": "No stars found."}}},
        }
    },
)
async def get_stars(db: AsyncSession = Depends(get_db)):
    """
    Fetch a list of all stars from the database.

    This function retrieves a list of all stars with their `id` and `name`.

    :param db: The async SQLAlchemy database session (provided via dependency injection).
    :type db: AsyncSession

    :return: A list of stars with `id` and `name`.
    :rtype: List[StarListSchema]

    :raises HTTPException: Raises a 404 error if no stars are found.
    """
    stars = await get_all_stars(db)
    return stars


@router.post(
    "/",
    response_model=StarListSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new star",
    description=(
        "<h3>This endpoint allows you to create a new star in the system.</h3>"
        "You need to provide the `name` of the star to create it. The star name must be unique."
    ),
    responses={
        400: {
            "description": "Star with this name already exists.",
            "content": {
                "application/json": {
                    "example": {"detail": "Star with this name already exists"}
                }
            },
        }
    },
)
async def create_star_route(
    star: StarCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Create a new star in the system.

    This function checks the uniqueness of the star's name and creates a new star if valid.

    :param star: The star's information, including `name`.
    :type star: StarCreateSchema
    :param db: The async SQLAlchemy database session (provided via dependency injection).
    :type db: AsyncSession

    :return: The newly created star with `id` and `name`.
    :rtype: StarListSchema

    :raises HTTPException: Raises a 400 error if the star with the given name already exists.
    """
    await check_admin_or_moderator(current_user)
    new_star = await create_star(db, star.name)
    return new_star


@router.put(
    "/{star_id}/",
    response_model=StarListSchema,
    status_code=status.HTTP_200_OK,
    summary="Update an existing star",
    description=(
        "<h3>This endpoint allows you to update the information of an existing star.</h3>"
        "You can modify the `name` of the star. If the star is not found, an error will be returned."
    ),
    responses={
        404: {
            "description": "Star not found.",
            "content": {"application/json": {"example": {"detail": "Star not found."}}},
        }
    },
)
async def update_star_route(
    star_id: int,
    star: StarUpdateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Update the details of an existing star.

    This function checks if the star exists and applies the updated data for the star.

    :param star_id: The ID of the star to update.
    :type star_id: int
    :param star: The new data to update the star with.
    :type star: StarUpdateSchema
    :param db: The async SQLAlchemy database session (provided via dependency injection).
    :type db: AsyncSession

    :return: The updated star with `id` and `name`.
    :rtype: StarListSchema

    :raises HTTPException: Raises a 404 error if the star with the given ID does not exist.
    """
    await check_admin_or_moderator(current_user)
    updated_star = await update_star(db, star_id, star.name)
    if not updated_star:
        raise HTTPException(status_code=404, detail="Star not found")
    return updated_star


@router.delete(
    "/{star_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a star",
    description=(
        "<h3>This endpoint allows you to delete a star from the system.</h3>"
        "If the star is associated with any movies, it cannot be deleted, and an error will be returned."
    ),
    responses={
        404: {
            "description": "Star not found or has related movies.",
            "content": {
                "application/json": {
                    "example": {"detail": "Star not found or has related movies."}
                }
            },
        },
        204: {"description": "Star deleted successfully."},
    },
)
async def delete_star(
    star_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Delete an existing star.

    This function deletes a star by its ID. If the star is associated with movies, it cannot be deleted.

    :param star_id: The ID of the star to delete.
    :type star_id: int
    :param db: The async SQLAlchemy database session (provided via dependency injection).
    :type db: AsyncSession

    :raises HTTPException: Raises a 404 error if the star is not found or has related movies.
    """
    await check_admin_or_moderator(current_user)
    success = await star_service.delete_star(db, star_id)
    if not success:
        raise HTTPException(
            status_code=404, detail="Star not found or has related movies"
        )
    return None
