from sqlalchemy.orm import Session

from database import PaymentModel


class PaymentService:
    @staticmethod
    def get_payment_service(db: Session, order_id: int):
        return db.query(PaymentModel).filter(PaymentModel.order_id == order_id).all()
