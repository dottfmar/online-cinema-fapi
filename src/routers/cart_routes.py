# isort: skip_file
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from database import CartItemModel, MovieModel, UserModel
from dependencies import get_current_user, get_db
from schemas import AddMovieToCartSchema, CartItemSchema, CartSchema
from services import (
    add_movie_to_cart_service,
    checkout_cart_service,
    clear_cart_service,
    remove_movie_from_cart_service,
)

router = APIRouter()


@router.post("/cart/", response_model=CartSchema)
async def add_movie_to_cart(
    add_movie: AddMovieToCartSchema,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Adds a movie to the user's cart.

    **Query Parameters:**
    - `movie_id`: The ID of the movie to be added to the cart.

    **Response:**
    Returns the updated cart after the movie is added.

    **Errors:**
    - 404: If the movie is not found.
    - 400: If there was an error adding the movie to the cart.
    """
    movie = db.query(MovieModel).filter(MovieModel.id == add_movie.movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    # Using service function to add movie to the cart
    try:
        cart = add_movie_to_cart_service(current_user, movie, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return CartSchema.from_orm(cart)


@router.get("/cart/", response_model=CartSchema)
async def get_cart(
    current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Retrieves the user's cart information.

    **Response:**
    Returns the current user's cart.

    **Errors:**
    - 404: If the user's cart does not exist.
    """
    if not current_user.cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    return CartSchema.from_orm(current_user.cart)


@router.delete("/cart/", response_model=CartSchema)
async def remove_movie_from_cart(
    movie_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Removes a movie from the user's cart.

    **Query Parameters:**
    - `movie_id`: The ID of the movie to be removed from the cart.

    **Response:**
    Returns the updated cart after the movie is removed.

    **Errors:**
    - 404: If the movie is not found in the cart.
    """
    # Using service function to remove movie from the cart
    try:
        cart = remove_movie_from_cart_service(current_user, movie_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return CartSchema.from_orm(cart)


@router.delete("/cart/clear/", response_model=CartSchema)
async def clear_cart(
    current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Clears the user's cart.

    **Response:**
    Returns the empty cart after clearing.

    **Errors:**
    - 404: If the user's cart does not exist.
    """
    # Using service function to clear the cart
    try:
        cart = clear_cart_service(current_user, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return CartSchema.from_orm(cart)


@router.post("/cart/checkout/", response_model=CartSchema)
async def checkout_cart(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = Depends(),
):
    """
    Checks out the user's cart and processes payment.

    **Response:**
    Returns the updated cart after checkout.

    **Errors:**
    - 400: If there was an error during the checkout process.
    """
    # Using service function to check out the cart
    try:
        cart = checkout_cart_service(current_user, db, background_tasks)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return CartSchema.from_orm(cart)


@router.get("/cart/movie/{movie_id}", response_model=CartItemSchema)
async def get_movie_in_cart(
    movie_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves a movie's information from the user's cart.

    **Query Parameters:**
    - `movie_id`: The ID of the movie to retrieve from the cart.

    **Response:**
    Returns the movie information in the user's cart.

    **Errors:**
    - 404: If the movie is not found in the cart.
    """
    if not current_user.cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    cart_item = (
        db.query(CartItemModel)
        .filter(
            CartItemModel.cart_id == current_user.cart.id,
            CartItemModel.movie_id == movie_id,
        )
        .first()
    )

    if not cart_item:
        raise HTTPException(status_code=404, detail="Movie not in cart")

    return CartItemSchema.from_orm(cart_item)


@router.put("/cart/movie/{movie_id}", response_model=CartItemSchema)
async def update_movie_quantity_in_cart(
    movie_id: int,
    quantity: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Updates the quantity of a movie in the user's cart.

    **Query Parameters:**
    - `movie_id`: The ID of the movie to update the quantity.
    - `quantity`: The new quantity of the movie in the cart.

    **Response:**
    Returns the updated movie information in the cart.

    **Errors:**
    - 404: If the movie is not found in the cart.
    - 400: If the quantity provided is invalid (less than or equal to 0).
    """
    if not current_user.cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    cart_item = (
        db.query(CartItemModel)
        .filter(
            CartItemModel.cart_id == current_user.cart.id,
            CartItemModel.movie_id == movie_id,
        )
        .first()
    )

    if not cart_item:
        raise HTTPException(status_code=404, detail="Movie not in cart")

    # Ensure quantity is positive
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than 0")

    cart_item.quantity = quantity
    db.commit()
    db.refresh(cart_item)

    return CartItemSchema.from_orm(cart_item)


@router.get("/cart/items/", response_model=List[CartItemSchema])
async def get_cart_items(
    current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Retrieves all items in the user's cart.

    **Response:**
    Returns a list of all items in the user's cart.

    **Errors:**
    - 404: If the user's cart does not exist.
    """
    if not current_user.cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    cart_items = (
        db.query(CartItemModel)
        .filter(CartItemModel.cart_id == current_user.cart.id)
        .all()
    )
    return [CartItemSchema.from_orm(cart_item) for cart_item in cart_items]
