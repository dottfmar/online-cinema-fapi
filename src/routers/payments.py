import stripe
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from starlette.config import Config
from starlette.responses import JSONResponse

from config.dependencies import get_accounts_email_notificator
from database import OrderModel, PaymentItemModel, PaymentModel
from database.models.order import OrderStatusEnum
from dependencies import get_db
from schemas.payments import PaymentSchema, PaymentStatus

# from sqlalchemy.testing import db
# from starlette.responses import JSONResponse


config = Config(".env")
STRIPE_SECRET_KEY = config("STRIPE_SECRET_KEY")
STRIPE_SUCCESS_URL = config(
    "STRIPE_SUCCESS_URL", default="http://127.0.0.1:8000/success"
)
STRIPE_CANCEL_URL = config("STRIPE_CANCEL_URL", default="http://127.0.0.1:8000/cancel")
WEBHOOK_SECRET_KEY = config("WEBHOOK_SECRET_KEY")
BASE_URL = "http://127.0.0.1:8000"

stripe.api_key = STRIPE_SECRET_KEY

router = APIRouter()


@router.post("/create-checkout-session/")
async def create_checkout_session(
    order_id: int, session: AsyncSession = Depends(get_db)
):
    result = await session.execute(select(OrderModel).where(OrderModel.id == order_id))
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    line_items = [
        {
            "price_data": {
                "currency": "usd",
                "unit_amount": int(order.total_amount * 100),
                "product_data": {
                    "name": f"Order #{order.id}",
                    "description": "Purchase of movies",
                },
            },
            "quantity": 1,
        }
    ]

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=line_items,
        mode="payment",
        success_url=f"{STRIPE_SUCCESS_URL}?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=STRIPE_CANCEL_URL,
        metadata={"order_id": str(order.id)},
    )
    return {"checkout_url": session.url}


# Payment success endpoint
@router.get("/success/")
async def handle_payment_success():
    return {"message": "Payment successful"}


# Payment canceled endpoint
@router.get("/cancel/")
async def handle_payment_cancel():
    return {"message": "Payment canceled"}


@router.get("/payments/{payment_id}/", response_model=PaymentSchema)
async def get_payment(payment_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PaymentModel)
        .options(selectinload(PaymentModel.items))
        .filter(PaymentModel.id == payment_id)
    )
    payment = result.scalar_one_or_none()
    print(payment.items)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    return payment


@router.post("/stripe/webhook/")
async def stripe_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    email_notification=Depends(get_accounts_email_notificator),
    db: AsyncSession = Depends(get_db),
):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET_KEY)
    except ValueError:
        return JSONResponse(status_code=400, content={"error": "Invalid payload"})
    except stripe.error.SignatureVerificationError:
        return JSONResponse(status_code=400, content={"error": "Invalid signature"})

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        order_id = int(session["metadata"]["order_id"])
        print("Payment completed for order ID:", order_id)

        async with db.begin():
            order_query = await db.execute(
                select(OrderModel).where(OrderModel.id == order_id)
            )
            order = order_query.scalar_one_or_none()
            if not order:
                return JSONResponse(
                    status_code=404, content={"error": "Order not found"}
                )

            await db.refresh(order, ["order_items", "user"])

            order.status = OrderStatusEnum.PAID

            payment = PaymentModel(
                user_id=order.user_id,
                order_id=order.id,
                amount=order.total_amount,
                status=PaymentStatus.SUCCESSFUL,
            )
            db.add(payment)
            await db.flush()

            payment_items = [
                PaymentItemModel(
                    payment_id=payment.id,
                    order_item_id=item.id,
                    price_at_payment=item.price_at_order,
                )
                for item in order.order_items
            ]
            db.add_all(payment_items)

        if order.user:
            user_email = order.user.email
            url = BASE_URL + f"/payments/{payment.id}/"
            background_tasks.add_task(
                email_notification.send_successfully_payment_email, user_email, url
            )

    return JSONResponse(status_code=200, content={"message": "Webhook received"})
