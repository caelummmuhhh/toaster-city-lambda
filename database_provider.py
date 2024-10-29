import sqlalchemy as sa
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
        self._engine = sa.create_engine(self._conn_str, engine_args)
        return self._engine
    

    def query_db(self, sql: str) -> list:
        """
        Executes a SQL query against the specified database and returns the result set.
        If no engine exists yet, creates engine.

        Parameters
        ----------
        sql : str
            The query to execute
        
        Returns
        -------
        list
            The result of the query
        """
        if not self._engine:
            self.get_engine()
        
        with self._engine.connect() as conn:
            rs = conn.execute(sa.text(sql)).fetchall()
        return rs
    

    def pandas_read_sql(self, sql: str, **read_sql_args) -> pd.DataFrame:
        """
        Executes the SQL query and returns the result as a pandas DataFrame.
        If no engine exists yet, creates engine.

        Parameters
        ----------
        sql : str
            The SQL query to execute
        **read_sql_args : keyword arguments
            Additional arguments to pass to the `pd.read_sql` function
        
        Returns
        -------
        pandas.DataFrame
            A DataFrame containing the result set of the executed query.
        """
        if not self._engine:
            self.get_engine()
        
        with self._engine.connect() as conn:
            df = pd.read_sql(sql, conn, read_sql_args)
        return df
