from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import DECIMAL, INT, VARCHAR
from sqlalchemy.orm import relationship, DeclarativeBase

class Base(DeclarativeBase):
    pass

class CustomerOrder(Base):
    __tablename__ = 'CUSTOMER_ORDER'

    id = Column(INT, primary_key=True, autoincrement=True)
    customer_name = Column(VARCHAR(50), nullable=False)
    status = Column(VARCHAR(255), nullable=True)
    payment_confirmation_id = Column(VARCHAR(37), nullable=False)

    line_items = relationship("CustomerOrderLineItem", back_populates="customer_order")


class CustomerOrderLineItem(Base):
    __tablename__ = 'CUSTOMER_ORDER_LINE_ITEM'

    id = Column(INT, primary_key=True, autoincrement=True)
    customer_order_id = Column(INT, ForeignKey('CUSTOMER_ORDER.id'), nullable=False)
    item_id = Column(INT, ForeignKey('INVENTORY.item_id'), nullable=False)
    quantity = Column(INT, nullable=False)

    customer_order = relationship("CustomerOrder", back_populates="line_items")
    inventory_item = relationship("Inventory", back_populates="line_items")


class Inventory(Base):
    __tablename__ = 'INVENTORY'

    item_id = Column(INT, primary_key=True, autoincrement=True)
    item_name = Column(VARCHAR(75), nullable=False)
    unit_price = Column(DECIMAL(9, 2), nullable=False)
    stock_quantity = Column(INT, nullable=False)
    weight = Column(DECIMAL(5, 2), nullable=False)

    line_items = relationship("CustomerOrderLineItem", back_populates="inventory_item")


class BusinessInfo(Base):
    __tablename__ = 'BUSINESS_INFO'

    business_name = Column(VARCHAR(30), nullable=False)
    address = Column(VARCHAR(45), nullable=False)
    city = Column(VARCHAR(45), nullable=False)
    state = Column(VARCHAR(45), nullable=False)
    zip = Column(VARCHAR(7), nullable=False)
    shipment_business_id = Column(VARCHAR(40), nullable=False, primary_key=True)
