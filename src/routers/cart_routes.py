from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database import CartItemModel, CartModel, MovieModel, UserModel
from src.dependencies import get_current_user, get_db
from src.schemas import AddMovieToCartSchema, CartSchema

router = APIRouter()


@router.post("/cart", response_model=CartSchema)
async def add_movie_to_cart(
    add_movie: AddMovieToCartSchema,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    movie = db.query(MovieModel).filter(MovieModel.id == add_movie.movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    # Check if the user has a shopping basket
    if not current_user.cart:
        cart = CartModel(user_id=current_user.id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    else:
        cart = current_user.cart

    # Check if the film is already in your basket
    existing_item = (
        db.query(CartItemModel)
        .filter(CartItemModel.cart_id == cart.id, CartItemModel.movie_id == movie.id)
        .first()
    )

    if existing_item:
        raise HTTPException(status_code=400, detail="Movie already in cart")

    # Add a new item to the basket
    cart_item = CartItemModel(
        cart_id=cart.id, movie_id=movie.id, added_at=datetime.now()  # noqa F821
    )
    db.add(cart_item)
    db.commit()
    db.refresh(cart_item)

    # Updating the basket data
    db.refresh(cart)

    return CartSchema.from_orm(cart)


@router.get("/cart", response_model=CartSchema)
async def get_cart(
    current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)
):
    if not current_user.cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    return CartSchema.from_orm(current_user.cart)


@router.delete("/cart", response_model=CartSchema)
async def remove_movie_from_cart(
    movie_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Check if the user has a shopping basket
    if not current_user.cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    # Find an item in the basket
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

    # Remove an item from the basket
    db.delete(cart_item)
    db.commit()

    # Updating the shopping basket
    db.refresh(current_user.cart)

    return CartSchema.from_orm(current_user.cart)


@router.delete("/cart/clear", response_model=CartSchema)
async def clear_cart(
    current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)
):
    # Check if the user has a shopping basket
    if not current_user.cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    # Remove all items from the basket
    db.query(CartItemModel).filter(
        CartItemModel.cart_id == current_user.cart.id
    ).delete()
    db.commit()

    # Updating the shopping basket
    db.refresh(current_user.cart)

    return CartSchema.from_orm(current_user.cart)


@router.post("/cart/checkout", response_model=CartSchema)
async def checkout_cart(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = Depends(),
):
    # Check if the user has a shopping basket
    if not current_user.cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    # If the basket is empty, return an error
    if not current_user.cart.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # Here you can add logic for processing the payment, for example, integration with the payment system

    # Emulate payment processing in the background process
    background_tasks.add_task(process_payment, current_user.cart)

    # After placing an order, clear the basket
    db.query(CartItemModel).filter(
        CartItemModel.cart_id == current_user.cart.id
    ).delete()
    db.commit()

    # Updating the shopping basket
    db.refresh(current_user.cart)

    return CartSchema.from_orm(current_user.cart)


def process_payment(cart):
    # Function for asynchronous payment processing (e.g. using Stripe, PayPal)
    # This is just an example, implementation depends on the selected payment system.
    print(f"Processing payment for cart with {len(cart.items)} items.")
    # Логика обработки платежей
