import pandas as pd
import sqlalchemy as sa
from inventory_management import InventoryManager
from database_provider import DatabaseProvider
from enum import Enum

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

        self._order_id = DatabaseProvider.query_db(self._engine, 'SELECT IFNULL(MAX(ID),0)+1 FROM CUSTOMER_ORDER')[0][0]
        self._order_df = pd.DataFrame({
            'ID': [self._order_id],
            'CUSTOMER_NAME': [order['payment_info']['name']],
            'SHIPPING_INFO_ID': [self._shipping_info_id],
            'PAYMENT_INFO_ID': [self._payment_info_id],
            'STATUS': [OrderStatus.RECEIVED.value]
        })
        self.__process_order_items__()

    def __process_order_items__(self):
        items = self._raw_order['items']
        items_data = {
            'CUSTOMER_ORDER_ID': [],
            'ITEM_ID': [],
            'QUANTITY': []
        }

        for item in items:
            items_data['CUSTOMER_ORDER_ID'].append(self._order_id)
            items_data['ITEM_ID'].append(item['item_id'])
            items_data['QUANTITY'].append(item['quantity'])

        self._order_items_df = pd.DataFrame(items_data)

    def __process_payment__(self):
        # TODO: This query is really inefficient and will be really slow once the table gets large
        #       Implement a logging in system or something where we'll properly save to a user's account.
        #       Matter fact, payment info probably shouldn't be stored without user permission anyways...
        payment = self._raw_order['payment_info']
        sql = '''
            SELECT ID
            FROM PAYMENT_INFO
            WHERE UPPER(NAME) = UPPER(:NAME)
                AND UPPER(CARD_NUMBER) = UPPER(:CARD_NUMBER)
                AND UPPER (EXPIRATION_DATE) = UPPER(:EXPIRATION_DATE)
                AND UPPER (CVV) = UPPER(:CVV)
                AND UPPER(ADDRESS_1) = UPPER(:ADDRESS_1)
                AND UPPER(ADDRESS_2) = UPPER(:ADDRESS_2)
                AND UPPER(CITY) = UPPER(:CITY)
                AND UPPER(STATE) = UPPER(:STATE)
                AND UPPER(ZIP) = UPPER(:ZIP)
        '''

        params = {
            'NAME': payment['name'],
            'CARD_NUMBER': payment['card_number'],
            'EXPIRATION_DATE': payment['expiration_date'],
            'CVV': payment['cvv'],
            'ADDRESS_1': payment['billing_address']['address_1'],
            'ADDRESS_2': payment['billing_address']['address_2'],
            'CITY': payment['billing_address']['city'],
            'STATE': payment['billing_address']['state'],
            'ZIP': payment['billing_address']['zip'],
        }

        # Check if payment info already exists
        id = DatabaseProvider.query_db(self._engine, sql, params)
        if id:
            self._payment_info_id = id
            return
        
        # Payment doesn't exist, insert new row
        # Retrieve/calculate new ID for row, since to_sql doesn't return new ID from auto_increment
        id = DatabaseProvider.query_db(self._engine, 'SELECT IFNULL(MAX(ID),0)+1 FROM PAYMENT_INFO')[0][0]

        df = pd.DataFrame([], columns=['ID'] + list(params.keys()))
        df.loc[0] = [id] + [str(c) for c in params.values()]

        self._payment_info_id = id


    def __process_shipping__(self) -> int:
        shipment = self._raw_order['shipping_info']
        sql = '''
            SELECT ID
            FROM SHIPPING_INFO
            WHERE UPPER(NAME) = UPPER(:name)
                AND UPPER(ADDRESS_1) = UPPER(:address_1)
                AND UPPER(ADDRESS_2) = UPPER(:address_2)
                AND UPPER(CITY) = UPPER(:city)
                AND UPPER(STATE) = UPPER(:state)
                AND UPPER(ZIP) = UPPER(:zip)
            '''
        
        id = DatabaseProvider.query_db(self._engine, sql, shipment)
        if id:
            self._shipping_info_id = id
            return
        
        # Payment doesn't exist, insert new row
        # Retrieve/calculate new ID for row, since to_sql doesn't return new ID from auto_increment
        id = DatabaseProvider.query_db(self._engine, 'SELECT IFNULL(MAX(ID),0)+1 FROM SHIPPING_INFO')[0][0]

        # column names are the same as keys in shipment, but uppercase
        df = pd.DataFrame([], columns=['ID'] + [key.upper() for key in shipment.keys()])
        df.loc[0] = [id] + [str(c) for c in shipment.values()]

        self._shipping_info_id = id

    
    def __in_stock__(self) -> bool:
        for item in self._raw_order['items']:
            res = DatabaseProvider.query_db(
                self._engine,
                'SELECT * FROM INVENTORY WHERE ITEM_ID = :item_id AND QUANTITY >= :quantity',
                {'item_id': item['item_id'], 'quantity': item['quantity']}
            )

            if not res:
                # Empty list was returned, so item does not have enough stock
                return False
        return True
    
    def __update_database_with_order__(self):
        pass


        
    

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
