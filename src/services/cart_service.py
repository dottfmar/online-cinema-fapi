from sqlalchemy.orm import Session

from src.database import CartItemModel, CartModel, MovieModel, UserModel


def add_movie_to_cart(user: UserModel, movie: MovieModel, db: Session):
    cart = user.cart
    if not cart:
        cart = CartModel(user_id=user.id)
        db.add(cart)
        db.commit()
        db.refresh(cart)

    existing_item = (
        db.query(CartItemModel)
        .filter(CartItemModel.cart_id == cart.id, CartItemModel.movie_id == movie.id)
        .first()
    )
    if existing_item:
        raise ValueError("This movie is already in your cart.")

    if movie.is_purchased:
        raise ValueError("This movie has already been purchased.")

    if movie.amount == 0:
        raise ValueError("There is no movie to purchase.")

    cart_item = CartItemModel(cart_id=cart.id, movie_id=movie.id)
    db.add(cart_item)
    db.commit()


def remove_movie_from_cart(user: UserModel, movie: MovieModel, db: Session):
    cart = user.cart
    if not cart:
        raise ValueError("Cart not found.")

    cart_item = (
        db.query(CartItemModel)
        .filter(CartItemModel.cart_id == cart.id, CartItemModel.movie_id == movie.id)
        .first()
    )
    if not cart_item:
        raise ValueError("Movie not found in cart.")

    db.delete(cart_item)
    db.commit()


def view_cart(user: UserModel, db: Session):
    cart = user.cart
    if not cart:
        return []

    cart_items = db.query(CartItemModel).filter(CartItemModel.cart_id == cart.id).all()
    movies_in_cart = []
    for item in cart_items:
        movie = item.movie
        movies_in_cart.append(
            {
                "title": movie.title,
                "price": movie.price,
                "genre": movie.genre,
                "release_year": movie.release_year,
            }
        )
    return movies_in_cart


def clear_cart(user: UserModel, db: Session):
    cart = user.cart
    if not cart:
        raise ValueError("Cart not found.")

    db.query(CartItemModel).filter(CartItemModel.cart_id == cart.id).delete()
    db.commit()


def checkout(user: UserModel, db: Session):
    cart = user.cart
    if not cart:
        raise ValueError("Cart not found.")

    if not cart.items:
        raise ValueError("Your cart is empty.")

    for item in cart.items:
        movie = item.movie
        if movie.is_purchased:
            raise ValueError(f"The movie {movie.title} has already been purchased.")

    for item in cart.items:
        movie = item.movie
        movie.is_purchased = True

    db.query(CartItemModel).filter(CartItemModel.cart_id == cart.id).delete()
    db.commit()
