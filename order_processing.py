import pandas as pd
import sqlalchemy as sa
from sqlalchemy.orm import Session, sessionmaker
from inventory_management import InventoryManager
from database_provider import DatabaseProvider
from toasterdb_orms import *
from enum import Enum


### NOTE: NONE OF THIS NEW ORM CODE HAS BEEN FULLY TESTED!!

class OrderStatus(Enum):
    RECEIVED = 'Received'
    IN_PROGRESS = 'Processed'
    SHIPPED = 'Shipped'
    COMPLETE = 'Complete'
    CANCELLED = 'Cancelled'


class OrderProcessor(object):
    """Handles order processing for a singular order."""
    _inventory: InventoryManager
    _engine: sa.engine.Engine

    _raw_order: dict

    _order_df: pd.DataFrame = None
    _order_items_df: pd.DataFrame = None
    _payment_df: pd.DataFrame = None
    _shipping_df: pd.DataFrame = None

    _order_id: int = None
    _shipping_info_id: int = None
    _payment_info_id: int = None

    def __init__(self, inventory: InventoryManager, engine: sa.engine.Engine):
        self._inventory = inventory
        self._engine = engine

    def process_order(self, order) -> int:
        self._raw_order = order

        if not self.__in_stock__(order['items']):
            # Item not in stock, return -1 to indicate it
            return -1

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

    def __process_order_items__(self):
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
            self._payment_info_id = id
            return
        
        # Payment doesn't exist, insert new row
        # Retrieve/calculate new ID for row, since to_sql doesn't return new ID from auto_increment
        id = DatabaseProvider.query_db(self._engine, sa.select(sa.func.ifnull(sa.func.max(PaymentInfo.id), 0) + 1))[0][0]
        
        df = pd.DataFrame([], columns=[PaymentInfo.id.name] + list(params.keys()))
        df.loc[0] = [id] + [str(c) for c in params.values()]

        self._payment_info_id = id


    def __process_shipping__(self) -> int:
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
            self._shipping_info_id = id
            return
        
        # Payment doesn't exist, insert new row
        # Retrieve/calculate new ID for row, since to_sql doesn't return new ID from auto_increment
        id = DatabaseProvider.query_db(self._engine, sa.select(sa.func.ifnull(sa.func.max(ShippingInfo.id), 0) + 1))[0][0]

        # column names are the same as keys in shipment, but uppercase
        df = pd.DataFrame([], columns=['ID'] + [key.upper() for key in shipment.keys()])
        df.loc[0] = [id] + [str(c) for c in shipment.values()]

        self._shipping_info_id = id

    
    def __in_stock__(self) -> bool:
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
    
    def __update_database_with_order__(self):
        session = Session(self._engine)
        with Session(self._engine) as session:
            session.begin()
            try:
                session.execute(sa.insert(PaymentInfo).values(self._payment_df.to_dict('records')))
                session.execute(sa.insert(ShippingInfo).values(self._shipping_df.to_dict('records')))
                session.execute(sa.insert(CustomerOrder).values(self._order_df.to_dict('records')))
                session.execute(sa.insert(CustomerOrderLineItem).values(self._order_items_df.to_dict('records')))

                for i, row in self._order_items_df.iterrows():
                    session.execute(
                        sa.update(Inventory).where(
                            Inventory.item_id == row[CustomerOrderLineItem.item_id.name]
                        ).values(quantity=Inventory.stock_quantity - row[CustomerOrderLineItem.quantity.name])
                    )
            except Exception as err:
                session.rollback()
                # TODO: Return a message indicating an error occurred making changes to database
            else:
                session.commit()


        
    

order_example = {
    'items': [
        {
            'item_id': 123,
            'quantity': 123
        }
    ],
    'payment_info': {
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
        'name': 'jane doe',
        'address_1': '123 Main St',
        'address_2': '321 2nd Ave',
        'city': 'Columbus',
        'state': 'OH',
        'zip': 43210
    }
}
