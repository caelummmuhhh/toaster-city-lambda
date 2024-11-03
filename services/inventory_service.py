import sqlalchemy as sa
import pandas as pd

from utils.database_provider import DatabaseProvider
from models.toasterdb_orms import *

class InventoryManagingService(object):
    """Handles Inventory management related requests."""
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
        sql = sa.select(Inventory)
        if only_in_stock:
            sql = sa.select(Inventory).where(Inventory.stock_quantity > 0)
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
        sql = sa.select(Inventory).where(Inventory.item_id == id)
        return DatabaseProvider.pandas_read_sql(self._engine, sql)

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
        sql = sa.select(Inventory).where(Inventory.item_name == name)
        return DatabaseProvider.pandas_read_sql(self._engine, sql)

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
        sql = sa.select(Inventory).where(
            (Inventory.item_id == item_id) & (Inventory.stock_quantity >= quantity)
        )
        df = DatabaseProvider.pandas_read_sql(self._engine, sql)
        return not df.empty
    