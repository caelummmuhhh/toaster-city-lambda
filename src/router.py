from json import dumps
from os import environ

from handlers.inventory_management_handler import InventoryManagementHandler
from handlers.order_processing_handler import OrderProcessingHandler
from utils.database_provider import DatabaseProvider

class Router(object):
    _routes = {
        'inventory-management': InventoryManagementHandler,
        'order-processing': OrderProcessingHandler
    }
    
    @staticmethod
    def route(event: dict, context) -> dict:
        """
        Routes an event to the right service.
        
        Parameters
        ----------
        event : dict
            The event from the HTTP request.
        context : LambdaContext
            The context from the HTTP request.
        
        Returns
        -------
        dict
            A dictionary with the HTTP status code and a body.
        """
        env_var_name = 'toast_db_conn_str'
        conn_str = environ.get(env_var_name)

        resource: str = event['resource']
        parent_resource = resource.split('/')[1]
        if parent_resource and parent_resource in Router._routes:
            handler = Router._routes[parent_resource](DatabaseProvider(conn_str).get_engine())

            status, body = handler.handle_request(event, context)
        else:
            status = 404
            body = f'Resource unknown: {resource}'
        
        return {
            'statusCode': status,
            'body': dumps(body)
        }
