from sqlalchemy import DECIMAL
from sqlalchemy.orm import Session

from database import OrderItemModel, OrderModel, UserModel
from database.models.order import OrderStatusEnum
from schemas import OrderCreateSchema


class OrderService:
    @staticmethod
    def create_order_service(
        db: Session, user_id: [UserModel], order_data: OrderCreateSchema
    ):
        new_order = OrderModel(
            user_id=user_id,
            status=OrderStatusEnum.PENDING,
            total_amount=DECIMAL(sum(item.price for item in order_data.order_items)),
        )
        db.add(new_order)
        db.commit()
        db.refresh(new_order)

        order_items = [
            OrderItemModel(
                order_id=new_order.id,
                movie_id=item.movie_id,
                price_at_order=DECIMAL(item.price),
            )
            for item in order_data.order_items
        ]

        db.add_all(order_items)
        db.commit()
        return new_order

    @staticmethod
    def get_orders_service(db: Session, user_id: [UserModel]):
        return db.query(OrderModel).filter(OrderModel.user_id == user_id).all()

    @staticmethod
    def get_order_service(db: Session, user_id: [UserModel], order_id: int):
        return (
            db.query(OrderModel)
            .filter(OrderModel.id == order_id, OrderModel.user_id == user_id)
            .first()
        )

    @staticmethod
    def cancel_order_service(db: Session, order: [OrderModel]):
        order.status = OrderStatusEnum.CANCELED
        db.commit()
        return order

    @staticmethod
    def repeat_order_service(db: Session, order: [OrderModel], user_id: [UserModel]):
        new_order = OrderModel(
            user_id=user_id,
            status=OrderStatusEnum.PENDING,
            total_amount=order.total_amount.value(),
        )
        db.add(new_order)
        db.flush()

        new_order_items = [
            OrderItemModel(
                order_id=new_order.id,
                movie_id=item.movie_id,
                price_at_order=item.price_at_order,
            )
            for item in order.order_items
        ]
        db.add_all(new_order_items)
        db.commit()
        return new_order
