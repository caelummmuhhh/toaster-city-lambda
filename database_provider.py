import sqlalchemy as sa
from sqlalchemy.exc import ResourceClosedError
import pandas as pd

class DatabaseProvider:
    """
    """
    _conn_str: str
    _engine: sa.engine.Engine = None

    def __init__(self, connection_str: str):
        """
        Parameters
        ----------
        connection_str : str
            The connection string to the host server and database. Should be in the format:
            ``dialect+driver://username:password@host:port/database``
        """
        self._conn_str = connection_str
    

    def get_engine(self, **engine_args) -> sa.engine.Engine:
        """
        Creates a ``SQLAlchemy.engine.Engine`` instance for the specified database and returns it.

        Parameters
        ----------
        **engineArgs :
            the variety of options which are routed towards the appropriate components for the engine
            when using SQLAlchemy.create_engine()

        Returns
        -------
        SQLAlchemy.engine.Engine
            The created engine.
        """
        self._engine = sa.create_engine(self._conn_str, **engine_args)
        return self._engine
    
    @staticmethod
    def query_db(engine: sa.engine.Engine, sql: str, params = None) -> list:
        """
        Executes a SQL query against the specified database and commits.
        Returns result set if query returns anything.

        Parameters
        ----------
        engine : SQLAlchemy.engine.Engine
            The SQLAlchemy engine to establish the database connection with
        sql : str
            The query to execute
        
        Returns
        -------
        list
            The result of the query
        """
        with engine.connect() as conn:
            cur = conn.execute(sa.text(sql), parameters=params)
            try:
                rs = cur.fetchall()
            except ResourceClosedError as err:
                rs = None
            conn.commit()
        return rs
    
    @staticmethod
    def pandas_read_sql(engine: sa.engine.Engine, sql: str, **read_sql_args) -> pd.DataFrame:
        """
        Executes the SQL query and returns the result as a pandas DataFrame.

        Parameters
        ----------
        engine : SQLAlchemy.engine.Engine
            The SQLAlchemy engine to establish the database connection with
        sql : str
            The SQL query to execute
        **read_sql_args : keyword arguments
            Additional arguments to pass to the `pd.read_sql` function
        
        Returns
        -------
        pandas.DataFrame
            A DataFrame containing the result set of the executed query.
        """        
        with engine.connect() as conn:
            df = pd.read_sql(sql, conn, **read_sql_args)
        return df
