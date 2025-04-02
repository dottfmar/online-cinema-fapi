from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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

        stmt = (
            select(CartModel)
            .options(selectinload(CartModel.items))
            .where(CartModel.user_id == user.id)
        )
        result = await db.execute(stmt)
        cart = result.scalars().first()

        if not cart:
            cart = CartModel(user_id=user.id)
            db.add(cart)
            await db.commit()
            await db.refresh(cart)

        stmt = select(CartItemModel).where(
            CartItemModel.cart_id == cart.id, CartItemModel.movie_id == movie.id
        )
        result = await db.execute(stmt)
        existing_item = result.scalars().first()

        if existing_item:
            raise ValueError("This movie is already in your cart.")

        cart_item = CartItemModel(cart_id=cart.id, movie_id=movie.id)
        db.add(cart_item)
        await db.commit()
        await db.refresh(cart_item)
        return cart

    @staticmethod
    async def remove_movie_from_cart_service(
        user: UserModel, movie_id: int, db: AsyncSession
    ):
        stmt = (
            select(CartModel)
            .options(selectinload(CartModel.items))
            .where(CartModel.user_id == user.id)
        )
        result = await db.execute(stmt)
        cart = result.scalars().first()

        if not cart:
            raise ValueError("Cart not found.")

        stmt = select(CartItemModel).where(
            CartItemModel.cart_id == cart.id, CartItemModel.movie_id == movie_id
        )
        result = await db.execute(stmt)
        cart_item = result.scalars().first()

        if not cart_item:
            raise ValueError("Movie not found in cart.")

        await db.delete(cart_item)
        await db.commit()

        await db.refresh(cart)
        return cart

    @staticmethod
    async def view_cart_service(user: UserModel, db: AsyncSession):
        stmt = (
            select(CartModel)
            .options(selectinload(CartModel.items).selectinload(CartItemModel.movie))
            .where(CartModel.user_id == user.id)
        )
        result = await db.execute(stmt)
        cart = result.scalars().first()

        if not cart or not cart.items:
            return []

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
        stmt = (
            select(CartModel)
            .options(selectinload(CartModel.items))
            .where(CartModel.user_id == user.id)
        )
        result = await db.execute(stmt)
        cart = result.scalars().first()

        if not cart:
            raise ValueError("Cart not found.")

        await db.execute(delete(CartItemModel).where(CartItemModel.cart_id == cart.id))
        await db.commit()
        return cart

    @staticmethod
    async def checkout_cart_service(user: UserModel, db: AsyncSession):
        stmt = (
            select(CartModel)
            .options(selectinload(CartModel.items).selectinload(CartItemModel.movie))
            .where(CartModel.user_id == user.id)
        )
        result = await db.execute(stmt)
        cart = result.scalars().first()

        if not cart:
            raise ValueError("Cart not found.")

        if not cart.items:
            raise ValueError("Your cart is empty.")

        for item in cart.items:
            movie = item.movie
            if movie.is_purchased:
                raise ValueError(
                    f"The movie '{movie.title}' has already been purchased."
                )

        for item in cart.items:
            movie = item.movie
            movie.is_purchased = True
            db.add(movie)

        await db.execute(delete(CartItemModel).where(CartItemModel.cart_id == cart.id))
        await db.commit()

        return cart
