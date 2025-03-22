from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Cart(Base):
    __tablename__ = "carts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    user = relationship("User", back_populates="cart", uselist=False)

    shopping_cart = relationship("ShoppingCart", back_populates="cart")

    def __repr__(self):
        return f"<Cart(id={self.id}, user_id={self.user_id})>"
