from enum import Enum

import pandas as pd
import sqlalchemy as sa
from sqlalchemy.orm import Session

from database_provider import DatabaseProvider
from toasterdb_orms import *

class OrderStatus(Enum):
    RECEIVED = 'Received'
    IN_PROGRESS = 'Processed'
    SHIPPED = 'Shipped'
    COMPLETE = 'Complete'
    CANCELLED = 'Cancelled'


class OrderProcessor(object):
    """Handles order processing for a singular order."""
    _engine: sa.engine.Engine

    _raw_order: dict

    _order_df: pd.DataFrame = None
    _order_items_df: pd.DataFrame = None
    _payment_df: pd.DataFrame = None
    _shipping_df: pd.DataFrame = None

    _order_id: int = None
    _shipping_info_id: int = None
    _payment_info_id: int = None

    def __init__(self, engine: sa.engine.Engine):
        """
        Parameters
        ----------
        db_engine : SQLAlchemy.engine.Engine
            The engine to connect to the database to handle the order.
        """
        self._engine = engine

    def process_order(self, order: dict) -> tuple[int, str]:
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
            A an HTTP response status code and a message.
        """
        self._raw_order = order

        if not self.__validate_raw_order__():
            return 400, 'Invalid order format.' # Bad Request

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
            self.__update_database_with_order__()
        except Exception as err:
            return 500, f'An error occurred when processing order. {type(err).__name__}'
    
    def __validate_raw_order__(self) -> bool:
        """
        Validates if the raw order has all the information required.

        Returns
        -------
        bool
            True if the order has all required information, False otherwise.
        """
        # Check for top level keys
        required_top_level_keys = {'items', 'payment_info', 'shipping_info'}
        if not required_top_level_keys.issubset(self._raw_order.keys()):
            return False

        # Check items
        if not isinstance(self._raw_order['items'], list) or not self._raw_order['items']:
            return False
        
        for item in self._raw_order['items']:
            if not isinstance(item, dict):
                return False
            if not {'item_id', 'quantity'}.issubset(item.keys()):
                return False
            if not isinstance(item['item_id'], int) or not isinstance(item['quantity'], int):
                return False

        # Check payment_info
        payment_info = self._raw_order['payment_info']
        required_payment_keys = {'name', 'card_number', 'expiration_date', 'cvv', 'billing_address'}
        if not required_payment_keys.issubset(payment_info.keys()):
            return False
        
        # Check billing_address within payment_info
        billing_address = payment_info['billing_address']
        required_billing_keys = {'address_1', 'address_2', 'city', 'state', 'zip'}
        if not required_billing_keys.issubset(billing_address.keys()):
            return False

        # Check shipping_info
        shipping_info = self._raw_order['shipping_info']
        required_shipping_keys = {'name', 'address_1', 'address_2', 'city', 'state', 'zip'}
        if not required_shipping_keys.issubset(shipping_info.keys()):
            return False

        return True


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
        # TODO: This query is really inefficient and will be really slow once the table gets large
        #       Implement a logging in system or something where we'll properly save to a user's account.
        #       Matter fact, payment info probably shouldn't be stored without user permission anyways...
        payment = self._raw_order['payment_info']
        params = {
            PaymentInfo.name.name: payment['name'],
            PaymentInfo.card_number.name: payment['card_number'],
            PaymentInfo.expiration_date.name: payment['expiration_date'],
            PaymentInfo.cvv.name: payment['cvv'],
            PaymentInfo.address_1.name: payment['billing_address']['address_1'],
            PaymentInfo.address_2.name: payment['billing_address']['address_2'],
            PaymentInfo.city.name: payment['billing_address']['city'],
            PaymentInfo.state.name: payment['billing_address']['state'],
            PaymentInfo.zip.name: payment['billing_address']['zip'],
        }

        sql = sa.select(PaymentInfo.id).where(
            (sa.func.upper(PaymentInfo.name) == sa.func.upper(params[PaymentInfo.name.name]))
            & (sa.func.upper(PaymentInfo.card_number) == sa.func.upper(params[PaymentInfo.card_number.name]))
            & (sa.func.upper(PaymentInfo.expiration_date) == sa.func.upper(params[PaymentInfo.expiration_date.name]))
            & (sa.func.upper(PaymentInfo.cvv) == sa.func.upper(params[PaymentInfo.cvv.name]))
            & (sa.func.upper(PaymentInfo.address_1) == sa.func.upper(params[PaymentInfo.address_1.name]))
            & (sa.func.upper(PaymentInfo.address_2) == sa.func.upper(params[PaymentInfo.address_2.name]))
            & (sa.func.upper(PaymentInfo.city) == sa.func.upper(params[PaymentInfo.city.name]))
            & (sa.func.upper(PaymentInfo.state) == sa.func.upper(params[PaymentInfo.state.name]))
            & (sa.func.upper(PaymentInfo.zip) == sa.func.upper(params[PaymentInfo.zip.name]))
        )

        # Check if payment info already exists
        id = DatabaseProvider.query_db(self._engine, sql)
        if id:
            self._payment_info_id = id[0][0] # query_db returns a list of tuples
            return
        
        # Payment doesn't exist, insert new row
        # Retrieve/calculate new ID for row, since to_sql doesn't return new ID from auto_increment
        id = DatabaseProvider.query_db(self._engine, sa.select(sa.func.ifnull(sa.func.max(PaymentInfo.id), 0) + 1))[0][0]
        
        self._payment_df = pd.DataFrame([], columns=[PaymentInfo.id.name] + list(params.keys()))
        self._payment_df.loc[0] = [id] + [str(c) for c in params.values()]

        self._payment_info_id = id


    def __process_shipping__(self) -> int:
        """
        Process shipping information from order. If shipping info does not already exist in database,
        sets `self._shipping_df` with `pandas.DataFrame` of the shipping info. Also sets `self._shipping_info_id`
        with the existing shipping info in database or new one that's going to be inserted.
        """
        shipment = self._raw_order['shipping_info']        
        sql = sa.select(ShippingInfo.id).where(
            (sa.func.upper(ShippingInfo.name) == sa.func.upper(shipment['name']))
            & (sa.func.upper(ShippingInfo.address_1) == sa.func.upper(shipment['address_1']))
            & (sa.func.upper(ShippingInfo.address_2) == sa.func.upper(shipment['address_2']))
            & (sa.func.upper(ShippingInfo.city) == sa.func.upper(shipment['city']))
            & (sa.func.upper(ShippingInfo.state) == sa.func.upper(shipment['state']))
            & (sa.func.upper(ShippingInfo.zip) == sa.func.upper(shipment['zip']))
        )
        
        id = DatabaseProvider.query_db(self._engine, sql)
        if id:
            self._shipping_info_id = id[0][0] # query_db returns a list of tuples
            return
        
        # Payment doesn't exist, insert new row
        # Retrieve/calculate new ID for row, since to_sql doesn't return new ID from auto_increment
        id = DatabaseProvider.query_db(self._engine, sa.select(sa.func.ifnull(sa.func.max(ShippingInfo.id), 0) + 1))[0][0]

        # column names are the same as keys in shipment, but uppercase
        self._shipping_df = pd.DataFrame([], columns=[ShippingInfo.id.name] + list(shipment.keys()))
        self._shipping_df.loc[0] = [id] + [str(c) for c in shipment.values()]

        self._shipping_info_id = id

    
    def __in_stock__(self) -> bool:
        """
        Checks if the items have enough stock quantity based on the order quantity.

        Returns
        -------
        bool
            True if quantity all items in order are <= the corresponding item stock, False otherwise.
        """
        for item in self._raw_order['items']:
            query = sa.select(Inventory).where(
                (Inventory.item_id == item['item_id'])
                & (Inventory.stock_quantity >= item['quantity'])
            )
            res = DatabaseProvider.query_db(self._engine, query)

            if not res:
                # Empty list was returned, so item does not have enough stock
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
                # Shipping and payment may already exist
                if (self._payment_df is not None and not self._payment_df.empty):
                    session.execute(sa.insert(PaymentInfo).values(self._payment_df.to_dict('records')))
                if (self._shipping_df is not None and not self._shipping_df.empty):
                    session.execute(sa.insert(ShippingInfo).values(self._shipping_df.to_dict('records')))

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
                # TODO: Return a message indicating an error occurred making changes to database
            else:
                session.commit()
        return success


        
    

order_example = {
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
