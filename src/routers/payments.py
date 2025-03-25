# isort: skip_file
from __future__ import annotations

import stripe
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from config.dependencies import get_successfully_payment_email_notificator
from database import OrderModel, PaymentModel
from dependencies import get_db
from notifications import EmailSenderInterface
from schemas.payments import PaymentCreate, PaymentResponseSchema, PaymentSchema

router = APIRouter()

URL_PAYMENTS = "http://127.0.0.1:8000/payments/"


@router.post("/payments/")
async def create_payment(
    payment_data: PaymentCreate,
    background_tasks: BackgroundTasks,
    email_notification: EmailSenderInterface = Depends(
        get_successfully_payment_email_notificator
    ),
    db: AsyncSession = Depends(get_db),
):
    order_query = await db.execute(
        select(OrderModel).filter(OrderModel.id == payment_data.order_id)
    )
    order = order_query.scalars().first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if not payment_data.token:
        raise HTTPException(status_code=400, detail="Payment token is required")

    try:
        payment_intent = stripe.PaymentIntent.create(
            amount=int(payment_data.amount * 100),
            currency="usd",
            payment_method=payment_data.token,
            confirm=True,
        )
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    status = "successful" if payment_intent.status == "succeeded" else "pending"

    payment = PaymentModel(
        user_id=order.user_id,
        order_id=order.id,
        amount=payment_data.amount,
        external_payment_id=payment_intent.id,
        status=status,
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)

    url = URL_PAYMENTS + "{payments_id}/"

    if hasattr(order, "user_email"):
        background_tasks.add_task(
            email_notification.send_successfully_payment_email, order.user_email, url
        )

    return PaymentResponseSchema(message="Payment successful", payment_id=payment.id)


@router.get("/payments/history/", response_model=list[PaymentSchema])
async def get_payment_history(user_id: int, db: AsyncSession = Depends(get_db)):
    payments_query = await db.execute(
        select(PaymentModel).filter(PaymentModel.user_id == user_id)
    )
    return payments_query.scalars().all()
