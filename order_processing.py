import hashlib
import time
import pandas as pd
import sqlalchemy as sa
from inventory_management import InventoryManager
from database_provider import DatabaseProvider

class OrderProcessor(object):
    """Handles order processing for a singular order."""
    _inventory: InventoryManager
    _engine: sa.engine.Engine

    def __init__(self, inventory: InventoryManager, engine: sa.engine.Engine):
        self._inventory = inventory
        self._engine = engine

    def process_order(self, order):
        
        pass

    def __process_order_items__(self, items: list):
        pass

    def __process_payment__(self, payment) -> int:
        # TODO: This query is really inefficient and will be really slow once the table gets large
        #       Implement a logging in system or something where we'll properly save to a user's account.
        #       Matter fact, payment info probably shouldn't be stored without user permission anyways...
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
            return id
        
        # Payment doesn't exist, insert new row
        id = DatabaseProvider.query_db(self._engine, 'SELECT IFNULL(MAX(ID),0)+1 FROM PAYMENT_INFO')[0][0]
        df = pd.DataFrame([], columns=['ID'] + list(params.keys()))
        df.loc[0] = [id] + [str(c) for c in params.values()]
        df.to_sql('PAYMENT_INFO', self._engine, index=False, if_exists='append')
        return id


    def __process_shipping__(self, shipment) -> int:
        sql = '''
            SELECT ID
            FROM SHIPPING_INFO
            WHERE UPPER(NAME) = UPPER(:NAME)
                AND UPPER(ADDRESS_1) = UPPER(:ADDRESS_1)
                AND UPPER(ADDRESS_2) = UPPER(:ADDRESS_2)
                AND UPPER(CITY) = UPPER(:CITY)
                AND UPPER(STATE) = UPPER(:STATE)
                AND UPPER(ZIP) = UPPER(:ZIP)
            '''
        

        shipping_info = {
        'NAME': shipment['NAME'],
        'ADDRESS_1': shipment['ADDRESS_1'],
        'ADDRESS_2': shipment['ADDRESS_2'],
        'CITY': shipment['CITY'],
        'STATE': shipment['STATE'],
        'ZIP': shipment['ZIP']
        }

        id = DatabaseProvider.query_db(self._engine, sql, shipping_info)
        if id:
            return id
        
        # Payment doesn't exist, insert new row
        id = DatabaseProvider.query_db(self._engine, 'SELECT IFNULL(MAX(ID),0)+1 FROM SHIPPING_INFO')[0][0]
        df = pd.DataFrame([], columns=['ID'] + list(shipping_info.keys()))
        df.loc[0] = [id] + [str(c) for c in shipping_info.values()]
        df.to_sql('SHIPPING_INFO', self._engine, index=False, if_exists='append')
        return id
    
    def __generate_confirmation_number__(self, order):
        unique_string = f"{order['id']}_{order['user_id']}_{time.time()}"
        confirmation_number = hashlib.sha256(unique_string.encode()).hexdigest()[:10]
        return confirmation_number

    def __get_shipping_info_id__(self, shipping_info: dict) -> int | None:
        """
        Retrieves the corresponding shipping information ID in the database, if it exists.

        Parameters
        ----------
        shipping_info : dict
            The shipping information to search for. Expecting the following keys:
            ``'name', 'address_1', 'address_2', 'city', 'state', 'zip'``
        
        Returns
        -------
        int | None
            The ID of the shipping information found, if not found, then None.
        """
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
        data = DatabaseProvider.query_db(self._engine, sql, shipping_info)
        return data[0][0] if data else None


    def __get_payment_info_id__(self, payment_info: dict) -> int | None:
        """
        Retrieves the corresponding payment information ID in the database, if it exists.

        Parameters
        ----------
        payment_info : dict
            The payment information to search for. Expecting the following keys:
            ``'card_number', 'expiration_date', 'cvv', 'name', 'address_1',
            'address_2', 'city', 'state', 'zip'``
        
        Returns
        -------
        int | None
            The ID of the payment information found, if not found, then None.
        """
        sql = '''
            SELECT ID
            FROM PAYMENT_INFO
            WHERE UPPER(NAME) = UPPER(:name)
                AND UPPER(CARD_NUMBER) = UPPER(:card_number)
                AND UPPER (EXPIRATION_DATE) = UPPER(:expiration_date)
                AND UPPER (CVV) = UPPER(:cvv)
                AND UPPER(ADDRESS_1) = UPPER(:address_1)
                AND UPPER(ADDRESS_2) = UPPER(:address_2)
                AND UPPER(CITY) = UPPER(:city)
                AND UPPER(STATE) = UPPER(:state)
                AND UPPER(ZIP) = UPPER(:zip)
        '''
        data = DatabaseProvider.query_db(self._engine, sql, payment_info)
        return data[0][0] if data else None



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
