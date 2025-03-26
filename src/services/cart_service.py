from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import CartItemModel, CartModel, MovieModel, UserModel


class CartService:
    @staticmethod
    async def add_movie_to_cart_service(
        user: UserModel, movie: MovieModel, db: AsyncSession
    ):
        if movie.is_purchased:
            raise ValueError("This movie has already been purchased.")

        if movie.amount == 0:
            raise ValueError("There is no movie to purchase.")

        # Preload the cart and its items using joinedload to prevent N+1 queries
        stmt = select(UserModel).options(joinedload(UserModel.cart))  # Preload the cart
        result = await db.execute(stmt)
        user = result.scalars().first()

        if not user.cart:
            # Create a new cart if not exists
            cart = CartModel(user_id=user.id)
            db.add(cart)
            await db.commit()
            await db.refresh(cart)
        else:
            cart = user.cart

        # Check if the movie is already in the cart
        stmt = select(CartItemModel).filter(
            CartItemModel.cart_id == cart.id, CartItemModel.movie_id == movie.id
        )
        result = await db.execute(stmt)
        existing_item = result.scalars().first()

        if existing_item:
            raise ValueError("This movie is already in your cart.")

        # Add new cart item
        cart_item = CartItemModel(cart_id=cart.id, movie_id=movie.id)
        db.add(cart_item)
        await db.commit()
        await db.refresh(cart_item)
        return cart

    @staticmethod
    async def remove_movie_from_cart_service(
        user: UserModel, movie_id: int, db: AsyncSession
    ):
        cart = user.cart
        if not cart:
            raise ValueError("Cart not found.")

        cart_item = (
            (
                await db.execute(
                    select(CartItemModel).filter(
                        CartItemModel.cart_id == cart.id,
                        CartItemModel.movie_id == movie_id,
                    )
                )
            )
            .scalars()
            .first()
        )

        if not cart_item:
            raise ValueError("Movie not found in cart.")

        await db.delete(cart_item)
        await db.commit()

    @staticmethod
    async def view_cart_service(user: UserModel, db: AsyncSession):
        cart = user.cart
        if not cart:
            return []

        db.refresh(cart)
        return [
            {
                "title": item.movie.title,
                "price": item.movie.price,
                "genre": item.movie.genre,
                "release_year": item.movie.release_year,
            }
            for item in cart.items
        ]

    @staticmethod
    async def clear_cart_service(user: UserModel, db: AsyncSession):
        cart = user.cart
        if not cart:
            raise ValueError("Cart not found.")

        for item in cart.items:
            db.delete(item)

        db.commit()

    @staticmethod
    async def checkout_cart_service(user: UserModel, db: AsyncSession):
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
            db.add(movie)

        db.query(CartItemModel).filter(CartItemModel.cart_id == cart.id).delete()
        db.commit()
