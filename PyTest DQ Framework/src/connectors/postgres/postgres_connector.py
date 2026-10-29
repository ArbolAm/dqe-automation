
from typing import Optional, Union

import pandas as pd
import psycopg2
from psycopg2.extensions import connection


class PostgresConnectorContextManager:
    def __init__(
        self,
        db_user: str,
        db_password: str,
        db_host: str,
        db_name: str,
        db_port: Union[int, str],
        autocommit: bool = False,
    ) -> None:
        self.db_user = db_user
        self.db_password = db_password
        self.db_host = db_host
        self.db_name = db_name
        self.db_port = int(db_port)
        self.autocommit = autocommit
        self.connection: Optional[connection] = None

    def __enter__(self) -> "PostgresConnectorContextManager":
        self.connection = psycopg2.connect(
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
            user=self.db_user,
            password=self.db_password,
        )
        self.connection.autocommit = self.autocommit
        return self

    def __exit__(self, exc_type, exc_value, exc_tb) -> None:
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def get_connection(self) -> Optional[connection]:
        return self.connection

    def get_data_sql(self, query: str) -> pd.DataFrame:
        if self.connection is None:
            raise RuntimeError("The PostgreSQL connection has not been opened.")
        return pd.read_sql_query(query, self.connection)


