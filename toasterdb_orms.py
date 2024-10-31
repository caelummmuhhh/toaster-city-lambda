from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import DECIMAL, INT, VARCHAR
from sqlalchemy.orm import relationship, DeclarativeBase

class Base(DeclarativeBase):
    pass

class CustomerOrder(Base):
    __tablename__ = 'CUSTOMER_ORDER'

    id = Column(INT, primary_key=True, autoincrement=True)
    customer_name = Column(VARCHAR(100), nullable=True)
    shipping_info_id = Column(INT, ForeignKey('SHIPPING_INFO.id'), nullable=True)
    payment_info_id = Column(INT, ForeignKey('PAYMENT_INFO.id'), nullable=True)
    status = Column(VARCHAR(255), nullable=True)

    shipping_info = relationship("ShippingInfo", back_populates="orders")
    payment_info = relationship("PaymentInfo", back_populates="orders")
    line_items = relationship("CustomerOrderLineItem", back_populates="customer_order")


class CustomerOrderLineItem(Base):
    __tablename__ = 'CUSTOMER_ORDER_LINE_ITEM'

    id = Column(INT, primary_key=True, autoincrement=True)
    customer_order_id = Column(INT, ForeignKey('CUSTOMER_ORDER.id'), nullable=True)
    item_id = Column(INT, ForeignKey('INVENTORY.item_id'), nullable=True)
    quantity = Column(INT, nullable=True)

    customer_order = relationship("CustomerOrder", back_populates="line_items")
    inventory_item = relationship("Inventory", back_populates="line_items")


class Inventory(Base):
    __tablename__ = 'INVENTORY'

    item_id = Column(INT, primary_key=True, autoincrement=True)
    item_name = Column(VARCHAR(75), nullable=False)
    unit_price = Column(DECIMAL(9, 2), nullable=False)
    stock_quantity = Column(INT, nullable=False)

    line_items = relationship("CustomerOrderLineItem", back_populates="inventory_item")


class PaymentInfo(Base):
    __tablename__ = 'PAYMENT_INFO'

    id = Column(INT, primary_key=True, autoincrement=True)
    name = Column(VARCHAR(45), nullable=True)
    card_number = Column(VARCHAR(45), nullable=True)
    expiration_date = Column(VARCHAR(5), nullable=True)
    cvv = Column(VARCHAR(45), nullable=True)
    address_1 = Column(VARCHAR(45), nullable=True)
    address_2 = Column(VARCHAR(45), nullable=True)
    city = Column(VARCHAR(45), nullable=True)
    state = Column(VARCHAR(45), nullable=True)
    zip = Column(VARCHAR(45), nullable=True)

    orders = relationship("CustomerOrder", back_populates="payment_info")


class ShippingInfo(Base):
    __tablename__ = 'SHIPPING_INFO'

    id = Column(INT, primary_key=True, autoincrement=True)
    name = Column(VARCHAR(45), nullable=True)
    address_1 = Column(VARCHAR(45), nullable=True)
    address_2 = Column(VARCHAR(45), nullable=True)
    city = Column(VARCHAR(45), nullable=True)
    state = Column(VARCHAR(45), nullable=True)
    zip = Column(VARCHAR(45), nullable=True)

    orders = relationship("CustomerOrder", back_populates="shipping_info")
