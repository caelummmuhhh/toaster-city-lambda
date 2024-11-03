import sqlalchemy as sa
import pandas as pd

from services.inventory_service import InventoryManagingService

class InventoryManagementHandler():
    """Handles events (HTTP requests) for the inventory-management resource."""
    _engine: sa.engine.Engine
    _manager: InventoryManagingService

    def __init__(self, engine: sa.engine.Engine):
        """
        Parameters
        ----------
        engine : sqlalchemy.engine.Engine
            The engine to connect to the database with the Inventory information.
        """
        super().__init__()
        self._engine = engine
        self._manager = InventoryManagingService(self._engine)

    
    def handle_request(self, event: dict, context) -> tuple[int, dict | str]:
        """Handles requests related to the inventory-management resource."""
        path = event['resource']
        if path == '/inventory-management/inventory':
            status_code, body = self.get_inventory(event['queryStringParameters'])
        elif path == '/inventory-management/inventory/items/{id}':
            status_code, body = self.get_item_from_id(event['pathParameters'])
        elif path == '/inventory-management/inventory/items':
            status_code, body = self.get_item(event['multiValueQueryStringParameters'], event['queryStringParameters'])
        else:
            status_code = 400
            body = 'Unknown path for inventory-management resource.'
        return status_code, body


    def get_inventory(self, query_str_params: dict | None) -> tuple[int, dict | str]:
        """
        Retrieves the inventory based on params.
        
        Parameters
        ----------
        query_str_params : dict | None
            The query string parameters from the event
        
        Returns
        -------
        tuple[int, str | dict]
            An HTTP status code and a message.
            If no error, the message is a dictionary of the inventory items.
        """
        only_items_in_stock = False
        if isinstance(query_str_params, dict) and 'in_stock' in query_str_params and query_str_params['query_str_params'].lower() == 'true':
            only_items_in_stock = True
        
        return 200, self._manager.get_inventory(only_items_in_stock).to_dict('records')


    def get_item(self, multi_query_str_params: dict | None, query_str_params: dict | None) -> tuple[int, dict | str]:
        """
        Retrieves items based on params.

        Parameters
        ----------
        multi_query_str_params: dict | None
            The multi value query string parameters from the event.
            If this is provided and is valid, takes priority over `query_str_params`
        query_str_params : dict | None
            The query string parameters from the event
        
        Returns
        -------
        tuple[int, dict | str]
            An HTTP status code and a message.
            If no error, the message is a dictionary of the inventory item(s).
            If multi_query_str_params is provided and is valid, returns all items found.
            If query_str_params but not multi_query_str_params, returns item found, if any.
            If no valid params are provided, returns the entire inventory.

        """
        # Handle multiple names
        # If both query_str_params and multi_query_str_params are provided, multi takes priority
        if isinstance(multi_query_str_params, dict) and 'item_name' in multi_query_str_params:
            item_names: list = multi_query_str_params['item_name']
            items_found = pd.DataFrame()
            for item_name in item_names:
                item_df = self._manager.get_item_by_name(item_name)
                if not item_df.empty:
                    # avoid future problems when concat a non-empty with an empty DataFrame
                    items_found = pd.concat([items_found, item_df], ignore_index=True)
            
            if items_found.empty:
                return 404, f'No item with names "{item_names}" were found.'
            return 200, items_found.to_dict('records')

        # Handle single name item
        if isinstance(query_str_params, dict) and 'item_name' in query_str_params:
            item_name = query_str_params['item_name']
            item_df = self._manager.get_item_by_name(item_name)

            if item_df.empty:
                return 404, f'Item with name "{item_name}" not found.'
            return 200, item_df.to_dict('records')
        
        # No params provided, return entire inventory
        return self.get_inventory(None)
            

    def get_item_from_id(self, path_params: dict | None) -> tuple[int, dict | str]:
        """
        Retrieves item infomation from inventory based on its ID.

        Parameters
        ----------
        path_params : dict | None
            The path parameters from the event.
        
        Returns
        -------
        tuple[int, dict | str]
            An HTTP status code and a message.
            If id is in `path_param` and is valid, the message is a dictionary of the item found.
        """
        if not isinstance(path_params, dict) or 'id' not in path_params:
            return 400, 'Missing path parameter, item ID.'
        
        if not path_params['id'].isdigit():
            return 400, 'ID needs to be a positive integer.'
        
        id = int(path_params['id'])
        item = self._manager.get_item_by_id(id)

        if item.empty:
            return 404, f'No item with ID {id} found.'
        return 200, item.to_dict('records')
