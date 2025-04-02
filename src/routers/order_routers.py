# isort: skip_file
from decimal import Decimal
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from database import OrderItemModel, UserModel
from database.models.order import OrderStatusEnum
from dependencies import get_current_user, get_db
from schemas import (
    OrderCreateSchema,
    OrderItemCreateSchema,
    OrderItemSchema,
    OrderSchema,
)
from schemas.payments import PaymentSchema
from services import OrderService, PaymentService

router = APIRouter(tags=["Orders"])


@router.get("/orders/", response_model=List[OrderSchema])
async def get_orders(
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all orders of the current user.

    - **current_user**: The user making the request (injected by Depends).
    - **db**: Database AsyncSession (injected by Depends).

    Returns a list of orders for the current user.
    """
    orders = await OrderService.get_orders_service(db, current_user)

    if not orders:
        raise HTTPException(status_code=404, detail="No orders found")

    return [OrderSchema.from_orm(order) for order in orders]


@router.get("/orders/{order_id}/", response_model=OrderSchema)
async def get_order(
    order_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific order by its ID for the current user.

    - **order_id**: The ID of the order.
    - **current_user**: The user making the request (injected by Depends).
    - **db**: Database AsyncSession (injected by Depends).

    Returns the details of the specified order if it belongs to the current user.
    """
    order = await OrderService.get_order_service(db, current_user, order_id)

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return OrderSchema.from_orm(order)


@router.post("/orders/", response_model=OrderSchema)
async def create_order(
    order_data: OrderCreateSchema,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new order for the current user.

    - **order_data**: The order details (items and prices).
    - **current_user**: The user making the request (injected by Depends).
    - **db**: Database AsyncSession (injected by Depends).

    Returns the newly created order.
    """
    new_order = await OrderService.create_order_service(db, current_user, order_data)

    return OrderSchema.from_orm(new_order)


@router.patch("/orders/{order_id}/cancel/", response_model=OrderSchema)
async def cancel_order(
    order_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Cancel an order if it is in a pending state.

    - **order_id**: The ID of the order to cancel.
    - **current_user**: The user making the request (injected by Depends).
    - **db**: Database AsyncSession (injected by Depends).

    Returns the updated order with the canceled status.
    """
    order = await OrderService.get_order_service(db, current_user, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != OrderStatusEnum.PENDING:
        raise HTTPException(
            status_code=400, detail="Only pending orders can be canceled"
        )

    await OrderService.cancel_order_service(db, order)

    return OrderSchema.from_orm(order)


@router.post("/orders/{order_id}/pay")
async def pay_order(
    order_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Pay for an order and update its status.

    - **order_id**: The ID of the order to pay for.
    - **current_user**: The user making the request (injected by Depends).
    - **db**: Database AsyncSession (injected by Depends).

    Returns a success message indicating the order has been paid.
    """
    order = await OrderService.get_order_service(db, current_user, order_id)

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != OrderStatusEnum.PENDING:
        raise HTTPException(status_code=400, detail="Order is already paid or canceled")

    order.status = OrderStatusEnum.PAID
    await db.commit()

    return {"message": "Order paid successfully"}


@router.patch("/orders/{order_id}/", response_model=OrderSchema)
async def update_order(
    order_id: int,
    order_data: OrderCreateSchema,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update the details of an existing order.

    - **order_id**: The ID of the order to update.
    - **order_data**: The new order data (items and prices).
    - **current_user**: The user making the request (injected by Depends).
    - **db**: Database AsyncSession (injected by Depends).

    Returns the updated order.
    """
    order = await OrderService.get_order_service(db, current_user, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.total_amount = Decimal(
        sum(item.price_at_order for item in order_data.order_items)
    )
    await db.commit()

    for item in order_data.order_items:
        query = select(OrderItemModel).filter(
            OrderItemModel.order_id == order.id,
            OrderItemModel.movie_id == item.movie_id,
        )
        existing_item = await db.execute(query)
        existing_item = existing_item.scalars().first()

        if existing_item:
            existing_item.price_at_order = Decimal(item.price_at_order)
        else:
            new_item = OrderItemModel(
                order_id=order.id,
                movie_id=item.movie_id,
                price_at_order=Decimal(item.price_at_order),
            )
            db.add(new_item)

    await db.commit()
    await db.refresh(order)
    return OrderSchema.from_orm(order)


@router.get("/orders/{order_id}/payments/", response_model=List[PaymentSchema])
async def get_order_payments(
    order_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the payment history for a specific order.

    - **order_id**: The ID of the order.
    - **current_user**: The user making the request (injected by Depends).
    - **db**: Database AsyncSession (injected by Depends).

    Returns a list of payments for the specified order.
    """
    order = await OrderService.get_order_service(db, current_user, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    payments = await PaymentService.get_payment_service(db, order_id)
    return [PaymentSchema.from_orm(payment) for payment in payments]


@router.get("/orders/status/{status}/", response_model=List[OrderSchema])
async def get_orders_by_status(
    status: OrderStatusEnum,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get orders by their status for the current user.

    - **status**: The order status to filter by.
    - **current_user**: The user making the request (injected by Depends).
    - **db**: Database AsyncSession (injected by Depends).

    Returns a list of orders with the specified status.
    """
    orders = await OrderService.get_orders_by_status(db, current_user, status)

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
    db: AsyncSession = Depends(get_db),
):
    """
    Add an item to an existing order.

    - **order_id**: The ID of the order to add an item to.
    - **item_data**: The item details (movie ID and price).
    - **current_user**: The user making the request (injected by Depends).
    - **db**: Database AsyncSession (injected by Depends).

    Returns the newly added order item.
    """
    order = await OrderService.get_order_service(db, current_user, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    new_item = OrderItemModel(
        order_id=order.id,
        movie_id=item_data.movie_id,
        price_at_order=Decimal(item_data.price_at_order),
    )
    db.add(new_item)
    await db.commit()
    await db.refresh(order)
    return OrderItemSchema.from_orm(new_item)


@router.delete("/orders/{order_id}/items/{item_id}/", response_model=OrderSchema)
async def remove_order_item(
    order_id: int,
    item_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Remove an item from an existing order.

    - **order_id**: The ID of the order.
    - **item_id**: The ID of the item to remove.
    - **current_user**: The user making the request (injected by Depends).
    - **db**: Database AsyncSession (injected by Depends).

    Returns the updated order after removing the item.
    """
    order = await OrderService.get_order_service(db, current_user, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    stmt = select(OrderItemModel).filter(
        OrderItemModel.id == item_id, OrderItemModel.order_id == order.id
    )
    result = await db.execute(stmt)
    item = result.scalars().first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    await db.delete(item)
    await db.commit()

    return OrderSchema.from_orm(order)
