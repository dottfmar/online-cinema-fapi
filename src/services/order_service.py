from decimal import Decimal

from sqlalchemy import DECIMAL
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from database import OrderItemModel, OrderModel, UserModel
from database.models.order import OrderStatusEnum
from schemas import OrderCreateSchema


class OrderService:
    @staticmethod
    async def create_order_service(
        db: AsyncSession, user_id: UserModel, order_data: OrderCreateSchema
    ):
        new_order = OrderModel(
            user_id=user_id.id,
            status=OrderStatusEnum.PENDING,
            total_amount=Decimal(
                sum(item.price_at_order for item in order_data.order_items)
            ),
        )
        db.add(new_order)
        await db.commit()
        await db.refresh(new_order)

        order_items = [
            OrderItemModel(
                order_id=new_order.id,
                movie_id=item.movie_id,
                price_at_order=DECIMAL(item.price_at_order),
            )
            for item in order_data.order_items
        ]

        db.add_all(order_items)
        await db.commit()
        return new_order

    @staticmethod
    async def get_orders_service(db: AsyncSession, user_id: [UserModel]):
        query = (
            select(OrderModel)
            .options(joinedload(OrderModel.order_items))
            .filter(OrderModel.user_id == user_id.id)
        )
        result = await db.execute(query)
        return result.unique().scalars().all()

    @staticmethod
    async def get_orders_by_status(
        db: AsyncSession, user_id: [UserModel], status: [OrderStatusEnum]
    ):
        query = (
            select(OrderModel)
            .options(joinedload(OrderModel.order_items))
            .filter(OrderModel.user_id == user_id.id)
            .filter(OrderModel.status == status)
        )
        result = await db.execute(query)
        return result.unique().scalars().all()

    @staticmethod
    async def get_order_service(db: AsyncSession, user_id: UserModel, order_id: int):
        query = (
            select(OrderModel)
            .options(joinedload(OrderModel.order_items))
            .filter(OrderModel.id == order_id, OrderModel.user_id == user_id.id)
        )
        result = await db.execute(query)
        return result.scalars().first()

    @staticmethod
    async def cancel_order_service(db: AsyncSession, order: [OrderModel]):
        order.status = OrderStatusEnum.CANCELED
        await db.commit()
        return order

    @staticmethod
    async def repeat_order_service(
        db: AsyncSession, order: [OrderModel], user_id: [UserModel]
    ):
        new_order = OrderModel(
            user_id=user_id,
            status=OrderStatusEnum.PENDING,
            total_amount=Decimal(order.total_amount),
        )
        db.add(new_order)
        await db.commit()

        new_order_items = [
            OrderItemModel(
                order_id=new_order.id,
                movie_id=item.movie_id,
                price_at_order=item.price_at_order,
            )
            for item in order.order_items
        ]
        db.add_all(new_order_items)
        await db.commit()
        await db.refresh(new_order)
        return new_order
