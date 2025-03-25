# isort: skip_file
from __future__ import annotations

import json
import os
from typing import List

import stripe
from dotenv import load_dotenv
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Request,
    responses,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from config.dependencies import get_successfully_payment_email_notificator
from database import PaymentItemModel, PaymentModel
from dependencies.database_session import get_db
from database.models import order
from notifications import EmailSenderInterface
from schemas.payments import PaymentCreateSchema, PaymentSchema, PaymentStatus

load_dotenv()
router = APIRouter()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

BASE_URL = os.getenv("BASE_URL") or "http://127.0.0.1:8000"


@router.get("/checkout/")
async def create_checkout_session(price: int = 10):
    checkout_session = stripe.checkout.Session.create(
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": "FastAPI Stripe Checkout",
                    },
                    "unit_amount": price * 100,
                },
                "quantity": 1,
            }
        ],
        metadata={"user_id": 3, "email": "abc@gmail.com", "request_id": 1234567890},
        mode="payment",
        success_url=BASE_URL + "/success/",
        cancel_url=BASE_URL + "/cancel/",
        customer_email="ping@fastapitutorial.com",
    )
    return responses.RedirectResponse(checkout_session.url, status_code=303)


@router.get("/success/")
async def handle_payment_success():
    return {"message": "Payment successful"}


@router.get("/cancel/")
async def handle_payment_cancel():
    return {"message": "Payment canceled"}


@router.post("/payments/", response_model=PaymentSchema)
async def create_payment(
    payment_data: PaymentCreateSchema,
    background_tasks: BackgroundTasks,
    email_notification: EmailSenderInterface = Depends(
        get_successfully_payment_email_notificator
    ),
    db: AsyncSession = Depends(get_db),
):
    payment = PaymentModel(
        user_id=payment_data.user_id,
        order_id=payment_data.order_id,
        amount=payment_data.amount,
        status=PaymentStatus.SUCCESSFUL,
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)

    payment_items = [
        PaymentItemModel(
            payment_id=payment.id,
            order_item_id=item.order_item_id,
            price_at_payment=item.price_at_payment,
        )
        for item in payment_data.payment_items
    ]
    db.add_all(payment_items)
    await db.commit()
    url = f"{BASE_URL}/payments/{payment.id}/"

    if hasattr(order, "user_email"):
        background_tasks.add_task(
            email_notification.send_successfully_payment_email, order.user_email, url
        )

    return payment


@router.get("/payments/", response_model=List[PaymentSchema])
async def get_payments(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PaymentModel))
    return result.scalars().all()


@router.get("/payments/{payment_id}", response_model=PaymentSchema)
async def get_payment(payment_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PaymentModel).filter(PaymentModel.id == payment_id)
    )
    payment = result.scalars().first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@router.post("/webhook/")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()

    try:
        event = stripe.Event.construct_from(json.loads(payload), stripe.api_key)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "checkout.session.completed":
        payment_data = event["data"]["object"]
        external_payment_id = payment_data["id"]
        amount = payment_data["amount_total"] / 100
        user_id = int(payment_data["metadata"]["user_id"])
        order_id = int(payment_data["metadata"]["request_id"])

        payment = PaymentModel(
            user_id=user_id,
            order_id=order_id,
            amount=amount,
            status=PaymentStatus.SUCCESSFUL,
            external_payment_id=external_payment_id,
        )
        db.add(payment)
        await db.commit()
        await db.refresh(payment)

    return {"status": "success"}
