import json

import sqlalchemy as sa

from services.order_processing_service import OrderProcessingService

class OrderProcessingHandler():
    """Handles events (HTTP requests) for the order-processing resource."""
    _engine: sa.engine.Engine
    _processor: OrderProcessingService

    def __init__(self, engine: sa.engine.Engine):
        """
        Parameters
        ----------
        engine : sqlalchemy.engine.Engine
            The engine to connect to the database with the Inventory information.
        """
        super().__init__()
        self._engine = engine
        self._processor = OrderProcessingService(self._engine)


    def handle_request(self, event, context) -> tuple[int, dict | str]:
        """Handles requests related to the order-processing resource."""
        path = event['resource']

        if path == '/order-processing/order':
            status_code, body = self.post_order(event['body'])
        else:
            status_code = 400
            body = 'Unknown path for order-processing resource.'

        return status_code, body
    

    def post_order(self, order) -> tuple[int, str | dict]:
        """
        POST an order to the database.

        Parameters
        ----------
        order : Any
            The order to be posted. Order will be validated.
        
        Returns
        -------
        tuple[int, str | dict]
            An HTTP status code and a message. If no error, message is confirmation number.
        """
        if not self.__validate_order__(order):
            return 400, 'Order not properly formatted.'

        order = json.loads(order)
        status_code, msg =  self._processor.process_order(order)

        if isinstance(msg, int):
            msg = {
                'confirmation_number': msg
            }
        
        return 200, msg


    def __validate_order__(self, order) -> bool:
        """
        Validates if the raw order has all the information required.

        Parameters
        ----------
        order : Any
            The order to validate

        Returns
        -------
        bool
            True if the order has all required information, False otherwise.
        """
        order = json.loads(order)
        if not isinstance(order, dict):
            return False

        # Check for top level keys
        required_top_level_keys = {'items', 'payment_info', 'shipping_info'}
        if not required_top_level_keys.issubset(order.keys()):
            return False

        # Check items
        if not isinstance(order['items'], list) or not order['items']:
            return False
        
        for item in order['items']:
            if not isinstance(item, dict):
                return False
            if not {'item_id', 'quantity'}.issubset(item.keys()):
                return False
            if not isinstance(item['item_id'], int) or not isinstance(item['quantity'], int):
                return False

        # Check payment_info
        payment_info = order['payment_info']
        required_payment_keys = {'name', 'card_number', 'expiration_date', 'cvv', 'billing_address'}
        if not required_payment_keys.issubset(payment_info.keys()):
            return False
        
        # Check billing_address within payment_info
        billing_address = payment_info['billing_address']
        required_billing_keys = {'address_1', 'address_2', 'city', 'state', 'zip'}
        if not required_billing_keys.issubset(billing_address.keys()):
            return False

        # Check shipping_info
        shipping_info = order['shipping_info']
        required_shipping_keys = {'name', 'address_1', 'address_2', 'city', 'state', 'zip'}
        if not required_shipping_keys.issubset(shipping_info.keys()):
            return False

        return True
