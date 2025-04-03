"""
Database connection functionality.
"""
import os
import re
import logging
import sqlite3
from typing import Dict, Any, List, Tuple, Optional, Union
from urllib.parse import urlparse

try:
    import psycopg2
    import psycopg2.extras
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

try:
    import mysql.connector
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """
    Database connection manager.
    """
    
    def __init__(self, connection_string: str):
        """
        Initialize the database connection manager.
        
        Args:
            connection_string: Database connection string
        """
        self.connection_string = connection_string
        self.connection = None
        self.cursor = None
        self.db_type = self._determine_db_type(connection_string)
    
    def _determine_db_type(self, connection_string: str) -> str:
        """
        Determine the database type from the connection string.
        
        Args:
            connection_string: Database connection string
            
        Returns:
            str: Database type (sqlite, postgresql, mysql)
            
        Raises:
            ValueError: If the database type is not supported
        """
        if connection_string.startswith('sqlite:///'):
            return 'sqlite'
        elif connection_string.startswith('postgresql://'):
            if not POSTGRES_AVAILABLE:
                raise ImportError("PostgreSQL support requires psycopg2 package. "
                                 "Install it with 'pip install psycopg2-binary'.")
            return 'postgresql'
        elif connection_string.startswith('mysql://'):
            if not MYSQL_AVAILABLE:
                raise ImportError("MySQL support requires mysql-connector-python package. "
                                 "Install it with 'pip install mysql-connector-python'.")
            return 'mysql'
        else:
            raise ValueError(f"Unsupported database type in connection string: {connection_string}")
    
    def connect(self) -> bool:
        """
        Connect to the database.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            if self.db_type == 'sqlite':
                # Extract the database path from the connection string
                db_path = self.connection_string.replace('sqlite:///', '')
                
                # Create the directory if it doesn't exist
                db_dir = os.path.dirname(db_path)
                if db_dir and not os.path.exists(db_dir):
                    os.makedirs(db_dir, exist_ok=True)
                
                # Connect to the database
                self.connection = sqlite3.connect(db_path)
                self.connection.row_factory = sqlite3.Row
            
            elif self.db_type == 'postgresql':
                # Parse the connection string
                parsed_url = urlparse(self.connection_string)
                
                # Extract connection parameters
                username = parsed_url.username
                password = parsed_url.password
                hostname = parsed_url.hostname
                port = parsed_url.port or 5432
                database = parsed_url.path.lstrip('/')
                
                # Connect to the database
                self.connection = psycopg2.connect(
                    host=hostname,
                    port=port,
                    user=username,
                    password=password,
                    dbname=database
                )
                self.connection.autocommit = False
            
            elif self.db_type == 'mysql':
                # Parse the connection string
                parsed_url = urlparse(self.connection_string)
                
                # Extract connection parameters
                username = parsed_url.username
                password = parsed_url.password
                hostname = parsed_url.hostname
                port = parsed_url.port or 3306
                database = parsed_url.path.lstrip('/')
                
                # Connect to the database
                self.connection = mysql.connector.connect(
                    host=hostname,
                    port=port,
                    user=username,
                    password=password,
                    database=database
                )
                self.connection.autocommit = False
            
            # Create a cursor
            self.cursor = self.connection.cursor()
            
            logger.info(f"Connected to {self.db_type} database")
            return True
        
        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            return False
    
    def disconnect(self) -> bool:
        """
        Disconnect from the database.
        
        Returns:
            bool: True if disconnection successful, False otherwise
        """
        try:
            if self.connection:
                self.connection.close()
                self.connection = None
                self.cursor = None
                
                logger.info("Disconnected from database")
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Failed to disconnect from database: {str(e)}")
            return False
    
    def execute(self, query: str, params: Optional[Union[List, Dict]] = None) -> Tuple[bool, Optional[List[Dict[str, Any]]]]:
        """
        Execute a query.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            Tuple[bool, Optional[List[Dict[str, Any]]]]: Success status and results
        """
        try:
            if not self.connection:
                logger.error("Not connected to database")
                return False, None
            
            # Execute the query
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            
            # Check if the query returns results
            if query.strip().upper().startswith(('SELECT', 'SHOW', 'DESCRIBE')):
                # Fetch the results
                if self.db_type == 'sqlite':
                    results = [dict(row) for row in self.cursor.fetchall()]
                elif self.db_type == 'postgresql':
                    results = [dict(row) for row in self.cursor.fetchall()]
                elif self.db_type == 'mysql':
                    columns = [col[0] for col in self.cursor.description]
                    results = [dict(zip(columns, row)) for row in self.cursor.fetchall()]
                
                return True, results
            else:
                # No results to fetch
                return True, None
        
        except Exception as e:
            logger.error(f"Failed to execute query: {str(e)}")
            return False, None
    
    def commit(self) -> bool:
        """
        Commit the current transaction.
        
        Returns:
            bool: True if commit successful, False otherwise
        """
        try:
            if not self.connection:
                logger.error("Not connected to database")
                return False
            
            self.connection.commit()
            logger.debug("Transaction committed")
            return True
        
        except Exception as e:
            logger.error(f"Failed to commit transaction: {str(e)}")
            return False
    
    def rollback(self) -> bool:
        """
        Rollback the current transaction.
        
        Returns:
            bool: True if rollback successful, False otherwise
        """
        try:
            if not self.connection:
                logger.error("Not connected to database")
                return False
            
            self.connection.rollback()
            logger.debug("Transaction rolled back")
            return True
        
        except Exception as e:
            logger.error(f"Failed to rollback transaction: {str(e)}")
            return False
    
    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists.
        
        Args:
            table_name: Name of the table
            
        Returns:
            bool: True if the table exists, False otherwise
        """
        try:
            if not self.connection:
                logger.error("Not connected to database")
                return False
            
            if self.db_type == 'sqlite':
                query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
                success, results = self.execute(query, [table_name])
            
            elif self.db_type == 'postgresql':
                query = "SELECT table_name FROM information_schema.tables WHERE table_name=%s"
                success, results = self.execute(query, [table_name])
            
            elif self.db_type == 'mysql':
                query = "SHOW TABLES LIKE %s"
                success, results = self.execute(query, [table_name])
            
            if success and results:
                return len(results) > 0
            
            return False
        
        except Exception as e:
            logger.error(f"Failed to check if table exists: {str(e)}")
            return False
    
    def get_tables(self) -> List[str]:
        """
        Get a list of all tables in the database.
        
        Returns:
            List[str]: List of table names
        """
        try:
            if not self.connection:
                logger.error("Not connected to database")
                return []
            
            if self.db_type == 'sqlite':
                query = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                success, results = self.execute(query)
                
                if success and results:
                    return [row['name'] for row in results]
            
            elif self.db_type == 'postgresql':
                query = "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
                success, results = self.execute(query)
                
                if success and results:
                    return [row['table_name'] for row in results]
            
            elif self.db_type == 'mysql':
                query = "SHOW TABLES"
                success, results = self.execute(query)
                
                if success and results:
                    return [list(row.values())[0] for row in results]
            
            return []
        
        except Exception as e:
            logger.error(f"Failed to get tables: {str(e)}")
            return []
    
    def get_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get a list of columns in a table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            List[Dict[str, Any]]: List of column information
        """
        try:
            if not self.connection:
                logger.error("Not connected to database")
                return []
            
            if self.db_type == 'sqlite':
                query = f"PRAGMA table_info({table_name})"
                success, results = self.execute(query)
                
                if success and results:
                    return [
                        {
                            'name': row['name'],
                            'type': row['type'],
                            'nullable': not row['notnull'],
                            'default': row['dflt_value'],
                            'primary_key': bool(row['pk'])
                        }
                        for row in results
                    ]
            
            elif self.db_type == 'postgresql':
                query = """
                SELECT column_name, data_type, is_nullable, column_default,
                       (SELECT true FROM information_schema.table_constraints tc
                        JOIN information_schema.key_column_usage kcu
                        ON tc.constraint_name = kcu.constraint_name
                        WHERE tc.constraint_type = 'PRIMARY KEY'
                        AND tc.table_name = %s
                        AND kcu.column_name = columns.column_name
                        LIMIT 1) as primary_key
                FROM information_schema.columns
                WHERE table_name = %s
                """
                success, results = self.execute(query, [table_name, table_name])
                
                if success and results:
                    return [
                        {
                            'name': row['column_name'],
                            'type': row['data_type'],
                            'nullable': row['is_nullable'] == 'YES',
                            'default': row['column_default'],
                            'primary_key': bool(row['primary_key'])
                        }
                        for row in results
                    ]
            
            elif self.db_type == 'mysql':
                query = f"DESCRIBE {table_name}"
                success, results = self.execute(query)
                
                if success and results:
                    return [
                        {
                            'name': row['Field'],
                            'type': row['Type'],
                            'nullable': row['Null'] == 'YES',
                            'default': row['Default'],
                            'primary_key': row['Key'] == 'PRI'
                        }
                        for row in results
                    ]
            
            return []
        
        except Exception as e:
            logger.error(f"Failed to get columns for table {table_name}: {str(e)}")
            return []
    
    def get_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get a list of indexes for a table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            List[Dict[str, Any]]: List of index information
        """
        try:
            if not self.connection:
                logger.error("Not connected to database")
                return []
            
            if self.db_type == 'sqlite':
                query = f"PRAGMA index_list({table_name})"
                success, results = self.execute(query)
                
                if success and results:
                    indexes = []
                    for row in results:
                        index_name = row['name']
                        index_query = f"PRAGMA index_info({index_name})"
                        index_success, index_results = self.execute(index_query)
                        
                        if index_success and index_results:
                            columns = [index_row['name'] for index_row in index_results]
                            indexes.append({
                                'name': index_name,
                                'columns': columns,
                                'unique': bool(row['unique'])
                            })
                    
                    return indexes
            
            elif self.db_type == 'postgresql':
                query = """
                SELECT
                    i.relname as index_name,
                    a.attname as column_name,
                    ix.indisunique as is_unique
                FROM
                    pg_class t,
                    pg_class i,
                    pg_index ix,
                    pg_attribute a
                WHERE
                    t.oid = ix.indrelid
                    AND i.oid = ix.indexrelid
                    AND a.attrelid = t.oid
                    AND a.attnum = ANY(ix.indkey)
                    AND t.relkind = 'r'
                    AND t.relname = %s
                ORDER BY
                    i.relname, a.attnum
                """
                success, results = self.execute(query, [table_name])
                
                if success and results:
                    indexes = {}
                    for row in results:
                        index_name = row['index_name']
                        if index_name not in indexes:
                            indexes[index_name] = {
                                'name': index_name,
                                'columns': [],
                                'unique': row['is_unique']
                            }
                        indexes[index_name]['columns'].append(row['column_name'])
                    
                    return list(indexes.values())
            
            elif self.db_type == 'mysql':
                query = f"SHOW INDEX FROM {table_name}"
                success, results = self.execute(query)
                
                if success and results:
                    indexes = {}
                    for row in results:
                        index_name = row['Key_name']
                        if index_name not in indexes:
                            indexes[index_name] = {
                                'name': index_name,
                                'columns': [],
                                'unique': not row['Non_unique']
                            }
                        indexes[index_name]['columns'].append(row['Column_name'])
                    
                    return list(indexes.values())
            
            return []
        
        except Exception as e:
            logger.error(f"Failed to get indexes for table {table_name}: {str(e)}")
            return []
    
    def create_database(self, database_name: str) -> bool:
        """
        Create a new database.
        
        Args:
            database_name: Name of the database
            
        Returns:
            bool: True if creation successful, False otherwise
        """
        try:
            if self.db_type == 'sqlite':
                # For SQLite, the database is created automatically when connecting
                return True
            
            elif self.db_type == 'postgresql':
                # Connect to the postgres database to create a new database
                parsed_url = urlparse(self.connection_string)
                
                # Extract connection parameters
                username = parsed_url.username
                password = parsed_url.password
                hostname = parsed_url.hostname
                port = parsed_url.port or 5432
                
                # Connect to the postgres database
                conn = psycopg2.connect(
                    host=hostname,
                    port=port,
                    user=username,
                    password=password,
                    dbname='postgres'
                )
                conn.autocommit = True
                cursor = conn.cursor()
                
                # Create the database
                cursor.execute(f"CREATE DATABASE {database_name}")
                
                # Close the connection
                cursor.close()
                conn.close()
                
                logger.info(f"Created PostgreSQL database: {database_name}")
                return True
            
            elif self.db_type == 'mysql':
                # Connect to MySQL without specifying a database
                parsed_url = urlparse(self.connection_string)
                
                # Extract connection parameters
                username = parsed_url.username
                password = parsed_url.password
                hostname = parsed_url.hostname
                port = parsed_url.port or 3306
                
                # Connect to MySQL
                conn = mysql.connector.connect(
                    host=hostname,
                    port=port,
                    user=username,
                    password=password
                )
                cursor = conn.cursor()
                
                # Create the database
                cursor.execute(f"CREATE DATABASE {database_name}")
                
                # Close the connection
                cursor.close()
                conn.close()
                
                logger.info(f"Created MySQL database: {database_name}")
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Failed to create database {database_name}: {str(e)}")
            return False
    
    def drop_database(self, database_name: str) -> bool:
        """
        Drop a database.
        
        Args:
            database_name: Name of the database
            
        Returns:
            bool: True if drop successful, False otherwise
        """
        try:
            if self.db_type == 'sqlite':
                # For SQLite, just delete the database file
                db_path = self.connection_string.replace('sqlite:///', '')
                if os.path.exists(db_path):
                    os.remove(db_path)
                    logger.info(f"Dropped SQLite database: {db_path}")
                    return True
                return False
            
            elif self.db_type == 'postgresql':
                # Connect to the postgres database to drop a database
                parsed_url = urlparse(self.connection_string)
                
                # Extract connection parameters
                username = parsed_url.username
                password = parsed_url.password
                hostname = parsed_url.hostname
                port = parsed_url.port or 5432
                
                # Connect to the postgres database
                conn = psycopg2.connect(
                    host=hostname,
                    port=port,
                    user=username,
                    password=password,
                    dbname='postgres'
                )
                conn.autocommit = True
                cursor = conn.cursor()
                
                # Drop the database
                cursor.execute(f"DROP DATABASE IF EXISTS {database_name}")
                
                # Close the connection
                cursor.close()
                conn.close()
                
                logger.info(f"Dropped PostgreSQL database: {database_name}")
                return True
            
            elif self.db_type == 'mysql':
                # Connect to MySQL without specifying a database
                parsed_url = urlparse(self.connection_string)
                
                # Extract connection parameters
                username = parsed_url.username
                password = parsed_url.password
                hostname = parsed_url.hostname
                port = parsed_url.port or 3306
                
                # Connect to MySQL
                conn = mysql.connector.connect(
                    host=hostname,
                    port=port,
                    user=username,
                    password=password
                )
                cursor = conn.cursor()
                
                # Drop the database
                cursor.execute(f"DROP DATABASE IF EXISTS {database_name}")
                
                # Close the connection
                cursor.close()
                conn.close()
                
                logger.info(f"Dropped MySQL database: {database_name}")
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Failed to drop database {database_name}: {str(e)}")
            return False


def create_connection(connection_string: str) -> Optional[DatabaseConnection]:
    """
    Create a database connection.
    
    Args:
        connection_string: Database connection string
        
    Returns:
        Optional[DatabaseConnection]: Database connection object or None if connection failed
    """
    try:
        # Create a database connection
        connection = DatabaseConnection(connection_string)
        
        # Connect to the database
        if connection.connect():
            return connection
        
        return None
    
    except Exception as e:
        logger.error(f"Failed to create database connection: {str(e)}")
        return None


def get_connection_string(db_type: str, **kwargs) -> str:
    """
    Get a database connection string.
    
    Args:
        db_type: Database type (sqlite, postgresql, mysql)
        **kwargs: Additional connection parameters
        
    Returns:
        str: Database connection string
        
    Raises:
        ValueError: If the database type is not supported
    """
    if db_type == 'sqlite':
        db_path = kwargs.get('db_path', 'app.db')
        return f"sqlite:///{db_path}"
    
    elif db_type == 'postgresql':
        username = kwargs.get('username', 'postgres')
        password = kwargs.get('password', '')
        hostname = kwargs.get('hostname', 'localhost')
        port = kwargs.get('port', 5432)
        database = kwargs.get('database', 'postgres')
        
        if password:
            return f"postgresql://{username}:{password}@{hostname}:{port}/{database}"
        else:
            return f"postgresql://{username}@{hostname}:{port}/{database}"
    
    elif db_type == 'mysql':
        username = kwargs.get('username', 'root')
        password = kwargs.get('password', '')
        hostname = kwargs.get('hostname', 'localhost')
        port = kwargs.get('port', 3306)
        database = kwargs.get('database', 'mysql')
        
        if password:
            return f"mysql://{username}:{password}@{hostname}:{port}/{database}"
        else:
            return f"mysql://{username}@{hostname}:{port}/{database}"
    
    else:
        raise ValueError(f"Unsupported database type: {db_type}")


def parse_connection_string(connection_string: str) -> Dict[str, Any]:
    """
    Parse a database connection string.
    
    Args:
        connection_string: Database connection string
        
    Returns:
        Dict[str, Any]: Connection parameters
        
    Raises:
        ValueError: If the connection string is invalid
    """
    try:
        # Determine the database type
        if connection_string.startswith('sqlite:///'):
            db_type = 'sqlite'
            db_path = connection_string.replace('sqlite:///', '')
            
            return {
                'db_type': db_type,
                'db_path': db_path
            }
        
        elif connection_string.startswith('postgresql://'):
            db_type = 'postgresql'
            parsed_url = urlparse(connection_string)
            
            return {
                'db_type': db_type,
                'username': parsed_url.username,
                'password': parsed_url.password,
                'hostname': parsed_url.hostname,
                'port': parsed_url.port or 5432,
                'database': parsed_url.path.lstrip('/')
            }
        
        elif connection_string.startswith('mysql://'):
            db_type = 'mysql'
            parsed_url = urlparse(connection_string)
            
            return {
                'db_type': db_type,
                'username': parsed_url.username,
                'password': parsed_url.password,
                'hostname': parsed_url.hostname,
                'port': parsed_url.port or 3306,
                'database': parsed_url.path.lstrip('/')
            }
        
        else:
            raise ValueError(f"Invalid connection string: {connection_string}")
    
    except Exception as e:
        raise ValueError(f"Failed to parse connection string: {str(e)}")


def test_connection(connection_string: str) -> Tuple[bool, str]:
    """
    Test a database connection.
    
    Args:
        connection_string: Database connection string
        
    Returns:
        Tuple[bool, str]: Success status and message
    """
    try:
        # Create a database connection
        connection = DatabaseConnection(connection_string)
        
        # Connect to the database
        if connection.connect():
            # Get the database type
            db_type = connection.db_type
            
            # Get the number of tables
            tables = connection.get_tables()
            
            # Disconnect from the database
            connection.disconnect()
            
            return True, f"Successfully connected to {db_type} database with {len(tables)} tables"
        
        return False, "Failed to connect to database"
    
    except Exception as e:
        return False, f"Failed to test database connection: {str(e)}"
