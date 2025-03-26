from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import PaymentModel


class PaymentService:
    @staticmethod
    async def get_payment_service(db: AsyncSession, order_id: int):
        query = select(PaymentModel).filter(PaymentModel.order_id == order_id)
        result = await db.execute(query)
        return result.scalars().all()
