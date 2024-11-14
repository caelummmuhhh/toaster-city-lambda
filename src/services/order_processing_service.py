from enum import Enum

import boto3
import pandas as pd
import sqlalchemy as sa
import requests
from sqlalchemy.orm import Session
import json

from utils.database_provider import DatabaseProvider
from models.toasterdb_orms import *

class OrderStatus(Enum):
    RECEIVED = 'Received'
    IN_PROGRESS = 'Processed'
    SHIPPED = 'Shipped'
    COMPLETE = 'Complete'
    CANCELLED = 'Cancelled'


class OrderProcessingService(object):
    """Handles order processing for a singular order."""
    _engine: sa.engine.Engine

    _raw_order: dict

    _order_df: pd.DataFrame = None
    _order_items_df: pd.DataFrame = None

    _order_id: int = None
    _payment_confirmation: str = None

    def __init__(self, engine: sa.engine.Engine):
        """
        Parameters
        ----------
        db_engine : SQLAlchemy.engine.Engine
            The engine to connect to the database to handle the order.
        """
        self._engine = engine


    def process_order(self, order: dict) -> tuple[int, str | int]:
        """
        Processes an order with the ordered items, payment info, and shipping info.
        Updates the database as neccessary.

        Parameters
        ----------
        order : dict
            The order that's to be processed. Expected format of the order:
            ```
            {
                'items': [
                    {
                        'item_id': 123,
                        'quantity': 123
                    }
                ],
                'payment_info': {
                    'name': 'Jane Doe',
                    'card_number': '123',
                    'expiration_date': '10/20',
                    'cvv': 123,
                    'billing_address': {
                        'address_1': '123 Main St',
                        'address_2': '321 2nd Ave',
                        'city': 'Columbus',
                        'state': 'OH',
                        'zip': 43210
                    }
                },
                'shipping_info': {
                    'name': 'Jane Doe',
                    'address_1': '123 Main St',
                    'address_2': '321 2nd Ave',
                    'city': 'Columbus',
                    'state': 'OH',
                    'zip': 43210
                }
            }
            ```
        
        Returns
        -------
        tuple[int, str]
            A an HTTP response status code and a message. If no error, message is confirmation number.
        """
        self._raw_order = order

        if not self.__in_stock__():
            # Item not in stock, return -1 to indicate it
            return 409, 'Not enough items in stock.' # Conflict
        
        try:
            self.__process_payment__()
            self.__process_shipping__()

            self._order_id = DatabaseProvider.query_db(
                self._engine,
                sa.select(sa.func.ifnull(sa.func.max(CustomerOrder.id), 0) + 1)
            )[0][0]
            
            self._order_df = pd.DataFrame({
                CustomerOrder.id.name: [self._order_id],
                CustomerOrder.customer_name.name: [order['payment_info']['name']],
                CustomerOrder.shipping_info_id.name: [self._shipping_info_id],
                CustomerOrder.payment_info_id.name: [self._payment_info_id],
                CustomerOrder.status.name: [OrderStatus.RECEIVED.value]
            })

            self.__process_order_items__()
        except Exception as err:
            return 500, f'An error occurred when processing order. {type(err).__name__}'
        
        if not self.__update_database_with_order__():
            return 500, f'An error occurred when making changes to database.'

        return 200, self._order_id
    

    def __process_order_items__(self):
        """
        Processes all the items in the order.
        Creates a DataFrame of the order with item_id and corresponding quantity.
        """
        items = self._raw_order['items']
        items_data = {
            CustomerOrderLineItem.customer_order_id.name: [],
            CustomerOrderLineItem.item_id.name: [],
            CustomerOrderLineItem.quantity.name: []
        }

        # Add each item to data list to make df
        for item in items:
            items_data[CustomerOrderLineItem.customer_order_id.name].append(self._order_id)
            items_data[CustomerOrderLineItem.item_id.name].append(item['item_id'])
            items_data[CustomerOrderLineItem.quantity.name].append(item['quantity'])

        self._order_items_df = pd.DataFrame(items_data)

    def __process_payment__(self):
        """
        Process payment information from order. If payment info does not already exist in database,
        sets `self._payment_df` with `pandas.DataFrame` of the payment info. Also sets `self._payment_info_id`
        with the existing payment info in database or new one that's going to be inserted.
        """
        # TODO: call payments API to POST payment info, get confirmation #
        pass

    def __get_business_shipping_info__(self) -> None:
        """Retrieves business information (name, address, business id, etc.)"""
        pass


    def __process_shipping__(self) -> int:
        """
        Async process shipment by putting an event on an event bus.
        Sending shipping info (addresses, packets, etc.) to shiping "vendor".
        """
        pass
    

    def __in_stock__(self) -> bool:
        """
        Checks if the items have enough stock quantity based on the order quantity.

        Returns
        -------
        bool
            True if quantity all items in order are <= the corresponding item stock, False otherwise.
        """
        for item in self._raw_order['items']:
            res = requests.get(
                f'https://1zpl4u5btg.execute-api.us-east-2.amazonaws.com/Test/inventory-management/inventory/items/{item['item_id']}'
            )

            if res.status_code != 200:
                return False
            
            data = res.json()
            if data[0]['stock_quantity'] < item['quantity']:
                return False
        return True
    
    
    def __update_database_with_order__(self) -> bool:
        """
        Makes necessary changes to the database based on the order.
        Inserts payment and shipping info if they are new.
        Inserts order and order items.
        Updates inventory by subtracting the stock quantity by what's ordered.

        Returns
        -------
        bool
            An indicator of success. True if transaction was success, False otherwise.
        """
        session = Session(self._engine)
        success = True
        with Session(self._engine) as session:
            session.begin()
            try:
                # TODO: get payment confirmation number 
                session.execute(sa.insert(CustomerOrder).values(self._order_df.to_dict('records')))
                session.execute(sa.insert(CustomerOrderLineItem).values(self._order_items_df.to_dict('records')))

                for i, row in self._order_items_df.iterrows():
                    session.execute(
                        sa.update(Inventory).where(
                            Inventory.item_id == row[CustomerOrderLineItem.item_id.name]
                        ).values(stock_quantity=Inventory.stock_quantity - row[CustomerOrderLineItem.quantity.name])
                    )
            except Exception as err:
                session.rollback()
                success = False
            else:
                session.commit()
        # TODO: Async send shipping info
        return success
