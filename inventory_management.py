import sqlalchemy as sa
import pandas as pd
from database_provider import DatabaseProvider

class InventoryManager(object):
    """Handles Inventory."""
    _db: sa.engine.Engine

    def __init__(self, db_engine: sa.engine.Engine):
        """
        Parameters
        ----------
        db_engine : SQLAlchemy.engine.Engine
            The engine to connect to the database with the INVENTORY table to manage.
        """
        self._engine = db_engine


    def get_inventory(self, only_in_stock: bool = False) -> pd.DataFrame:
        """
        Retrieves all items in inventory.

        Parameters
        ----------
        only_in_stock : bool = False
            Indicates whether items that are only in stock should be retrieved
        
        Returns
        -------
        pandas.Dataframe
            A DataFrame of the data retrieved.
        """
        sql = 'SELECT * FROM INVENTORY'
        if only_in_stock:
            sql = 'SELECT * FROM INVENTORY WHERE STOCK_QUANTITY > 0' 
        return DatabaseProvider.pandas_read_sql(self._engine, sql)


    def get_item_by_id(self, id: int) -> pd.DataFrame:
        """
        Retrieves item in inventory based on item ID.

        Parameters
        ----------
        id : int
            The ID of the items to be retrieved.
        
        Returns
        -------
        pandas.DataFrame
            A DataFrame containing the item found based on ID, if any.
        """
        sql = 'SELECT * FROM INVENTORY WHERE ITEM_ID = %s'
        params = (id,)
        return DatabaseProvider.pandas_read_sql(self._engine, sql, params=params)

    def get_item_by_name(self, name: str) -> pd.DateOffset:
        """
        Retrieves item in inventory based on item ID.

        Parameters
        ----------
        name : str
            The name of the items to be retrieved.
        
        Returns
        -------
        pandas.DataFrame
            A DataFrame containing the item found based on the item name, if any.
        """
        sql = 'SELECT * FROM INVENTORY WHERE UPPER(ITEM_NAME) = UPPER(%s)'
        params = (name,)
        return DatabaseProvider.pandas_read_sql(self._engine, sql, params=params)

    def item_enough_stock(self, item_id: int | str, quantity: int | str) -> bool:
        """
        Determines if an has enough stock quantity.

        Parameters
        ----------
        item_id : int | str
            The ID of the item to determine stock levels
        quantity : int | str
            The quantity to compare the item stock quantity to
        
        Returns
        -------
        bool
            Returns true if item stock >= quantity, false if not.
            Returns nothing if item not found.
        """
        sql = 'SELECT * FROM INVENTORY WHERE ITEM_ID = %s AND STOCK_QUANTITY >= %s'
        params = (item_id, quantity,)
        df = DatabaseProvider.pandas_read_sql(self._engine, sql, params=params)
        return not df.empty
    

    def purchase_item(self, item_id: int, quantity: int):
        """
        Removes certain item quantity from stock. If not enough quantity, does nothing.

        Parameters
        ----------
        item_id : int
            The ID of the item to remove quantity of stock from
        quantity : int
            The quantity of stock to remove from specified item's stock quantity
        """

        sql = '''
            UPDATE INVENTORY
            SET STOCK_QUANTITY = STOCK_QUANTITY - :quantity
            WHERE ITEM_ID = :id AND STOCK_QUANTITY >= :quantity
            '''
        params = {
            'quantity': quantity,
            'id': item_id
        }
        DatabaseProvider.query_db(self._engine, sql, params)

    def purchase_items(self, items: list):
        """
        Remove specified quantities from each item, if enough stock, if not, does nothing for that item.
        Expected items list format:
        items = [
            {
            'id': int,
            'quantity': int
            }
        ]
        """
        pass