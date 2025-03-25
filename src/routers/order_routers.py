# isort: skip_file
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.dialects.mysql import DECIMAL
from sqlalchemy.orm import Session

from database import OrderItemModel, OrderModel, UserModel
from database.models.order import OrderStatusEnum
from dependencies import get_current_user, get_db
from schemas import (
    OrderCreateSchema,
    OrderItemCreateSchema,
    OrderItemSchema,
    OrderSchema,
    OrderStatisticsSchema,
)
from schemas.payments import PaymentSchema
from services import OrderService, PaymentService

router = APIRouter()


@router.get("/orders/", response_model=List[OrderSchema])
async def get_orders(
    current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Get all orders of the current user.

    - **current_user**: The user making the request (injected by Depends).
    - **db**: Database session (injected by Depends).

    Returns a list of orders for the current user.
    """
    # Receive all the user's orders
    orders = OrderService.get_orders_service(db, current_user)

    if not orders:
        raise HTTPException(status_code=404, detail="No orders found")

    return [OrderSchema.from_orm(order) for order in orders]


@router.get("/orders/{order_id}/", response_model=OrderSchema)
async def get_order(
    order_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get a specific order by its ID for the current user.

    - **order_id**: The ID of the order.
    - **current_user**: The user making the request (injected by Depends).
    - **db**: Database session (injected by Depends).

    Returns the details of the specified order if it belongs to the current user.
    """
    # Find an order by ID
    order = OrderService.get_order_service(db, current_user, order_id)

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return OrderSchema.from_orm(order)


@router.post("/orders/{order_id}/repeat/", response_model=OrderSchema)
async def repeat_order(
    order_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new order by repeating the details of an existing order.

    - **order_id**: The ID of the existing order to repeat.
    - **current_user**: The user making the request (injected by Depends).
    - **db**: Database session (injected by Depends).

    Returns the newly created order.
    """
    # Find an order by ID and user
    order = OrderService.get_order_service(db, current_user, order_id)

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Create a new order
    new_order = OrderService.repeat_order_service(db, order, current_user)

    return OrderSchema.model_validate(new_order)


@router.post("/orders/", response_model=OrderSchema)
async def create_order(
    order_data: OrderCreateSchema,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new order for the current user.

    - **order_data**: The order details (items and prices).
    - **current_user**: The user making the request (injected by Depends).
    - **db**: Database session (injected by Depends).

    Returns the newly created order.
    """
    new_order = OrderService.create_order_service(db, current_user, order_data)

    return OrderSchema.from_orm(new_order)


@router.patch("/orders/{order_id}/cancel/", response_model=OrderSchema)
async def cancel_order(
    order_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Cancel an order if it is in a pending state.

    - **order_id**: The ID of the order to cancel.
    - **current_user**: The user making the request (injected by Depends).
    - **db**: Database session (injected by Depends).

    Returns the updated order with the canceled status.
    """
    order = OrderService.get_order_service(db, current_user, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != OrderStatusEnum.PENDING:
        raise HTTPException(
            status_code=400, detail="Only pending orders can be canceled"
        )

    order.status = OrderService.cancel_order_service(db, order)
    return order


@router.post("/orders/{order_id}/pay")
async def pay_order(
    order_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Pay for an order and update its status.

    - **order_id**: The ID of the order to pay for.
    - **current_user**: The user making the request (injected by Depends).
    - **db**: Database session (injected by Depends).

    Returns a success message indicating the order has been paid.
    """
    order = OrderService.get_order_service(db, current_user, order_id)

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != OrderStatusEnum.PENDING:
        raise HTTPException(status_code=400, detail="Order is already paid or canceled")

    # Here you need to add real payment logic via Stripe
    order.status = OrderStatusEnum.PAID
    db.commit()

    return {"message": "Order paid successfully"}


@router.patch("/orders/{order_id}/", response_model=OrderSchema)
async def update_order(
    order_id: int,
    order_data: OrderCreateSchema,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update the details of an existing order.

    - **order_id**: The ID of the order to update.
    - **order_data**: The new order data (items and prices).
    - **current_user**: The user making the request (injected by Depends).
    - **db**: Database session (injected by Depends).

    Returns the updated order.
    """
    order = OrderService.get_order_service(db, current_user, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Updating order data
    order.total_amount = DECIMAL(sum(item.price for item in order_data.order_items))
    db.commit()

    # Update order items (if changed)
    for item in order_data.order_items:
        existing_item = (
            db.query(OrderItemModel)
            .filter(
                OrderItemModel.order_id == order.id,
                OrderItemModel.movie_id == item.movie_id,
            )
            .first()
        )
        if existing_item:
            existing_item.price_at_order = DECIMAL(item.price)
        else:
            # If the item does not exist in the order, create a new one
            new_item = OrderItemModel(
                order_id=order.id.value(),
                movie_id=item.movie_id,
                price_at_order=DECIMAL(item.price),
            )
            db.add(new_item)

    db.commit()
    return OrderSchema.from_orm(order)


@router.get("/orders/{order_id}/payments/", response_model=List[PaymentSchema])
async def get_order_payments(
    order_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get the payment history for a specific order.

    - **order_id**: The ID of the order.
    - **current_user**: The user making the request (injected by Depends).
    - **db**: Database session (injected by Depends).

    Returns a list of payments for the specified order.
    """
    # Finding an order
    order = OrderService.get_order_service(db, current_user, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Get payment history
    payments = PaymentService.get_payment_service(db, order)
    return [PaymentSchema.from_orm(payment) for payment in payments]


@router.get("/orders/statistics/", response_model=OrderStatisticsSchema)
async def get_order_statistics(
    current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Get statistics for the current user's orders.

    - **current_user**: The user making the request (injected by Depends).
    - **db**: Database session (injected by Depends).

    Returns the total number of orders and total amount spent by the current user.
    """
    # We get the number of orders, total cost, etc.
    total_orders = (
        db.query(OrderModel).filter(OrderModel.user_id == current_user.id).count()
    )
    total_amount = (
        db.query(func.sum(OrderModel.total_amount))
        .filter(OrderModel.user_id == current_user.id)
        .scalar()
    )

    return OrderStatisticsSchema(total_orders=total_orders, total_amount=total_amount)


@router.get("/orders/status/{status}/", response_model=List[OrderSchema])
async def get_orders_by_status(
    status: OrderStatusEnum,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get orders by their status for the current user.

    - **status**: The order status to filter by.
    - **current_user**: The user making the request (injected by Depends).
    - **db**: Database session (injected by Depends).

    Returns a list of orders with the specified status.
    """
    orders = OrderService.get_orders_service()

    if not orders:
        raise HTTPException(
            status_code=404, detail=f"No orders with status {status} found"
        )

    return [OrderSchema.from_orm(order) for order in orders]


@router.post("/orders/{order_id}/items/", response_model=OrderItemSchema)
async def add_order_item(
    order_id: int,
    item_data: OrderItemCreateSchema,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Add an item to an existing order.

    - **order_id**: The ID of the order to add an item to.
    - **item_data**: The item details (movie ID and price).
    - **current_user**: The user making the request (injected by Depends).
    - **db**: Database session (injected by Depends).

    Returns the newly added order item.
    """
    order = OrderService.get_order_service(db, current_user, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    new_item = OrderItemModel(
        order_id=order.id.value(),
        movie_id=item_data.movie_id,
        price_at_order=DECIMAL(item_data.price),
    )
    db.add(new_item)
    db.commit()
    return OrderItemSchema.from_orm(new_item)


@router.delete("/orders/{order_id}/items/{item_id}/", response_model=OrderSchema)
async def remove_order_item(
    order_id: int,
    item_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Remove an item from an existing order.

    - **order_id**: The ID of the order.
    - **item_id**: The ID of the item to remove.
    - **current_user**: The user making the request (injected by Depends).
    - **db**: Database session (injected by Depends).

    Returns the updated order after removing the item.
    """
    order = OrderService.get_order_service(db, current_user, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    item = (
        db.query(OrderItemModel)
        .filter(OrderItemModel.id == item_id, OrderItemModel.order_id == order.id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    db.delete(item)
    db.commit()
    return OrderSchema.from_orm(order)
