"""
Database initialization for PythonWeb Installer.

This module provides high-level functions for database initialization and management.
"""
import os
import logging
from typing import Dict, Any, List, Tuple, Optional, Union

from pythonweb_installer.database.connection import (
    DatabaseConnection,
    create_connection,
    get_connection_string,
    test_connection,
    parse_connection_string
)
from pythonweb_installer.database.schema import (
    SchemaManager,
    create_schema_manager
)
from pythonweb_installer.database.data import (
    DataManager,
    create_data_manager
)
from pythonweb_installer.database.initialization import (
    DatabaseInitializer,
    initialize_database,
    create_database_schema,
    initialize_database_data
)

logger = logging.getLogger(__name__)


def init_database(db_type: str, **kwargs) -> Tuple[bool, str, Optional[DatabaseInitializer]]:
    """
    Initialize a database.
    
    Args:
        db_type: Database type (sqlite, postgresql, mysql)
        **kwargs: Additional connection parameters
        
    Returns:
        Tuple[bool, str, Optional[DatabaseInitializer]]: Success status, message, and initializer
    """
    try:
        # Get the connection string
        connection_string = get_connection_string(db_type, **kwargs)
        
        # Initialize the database
        return initialize_database(connection_string)
    
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        return False, f"Failed to initialize database: {str(e)}", None


def create_schema(initializer: DatabaseInitializer, schema_file: str) -> Tuple[bool, str]:
    """
    Create a database schema.
    
    Args:
        initializer: Database initializer
        schema_file: Path to the schema file
        
    Returns:
        Tuple[bool, str]: Success status and message
    """
    return create_database_schema(initializer, schema_file)


def load_data(initializer: DatabaseInitializer, data_dir: str) -> Tuple[bool, str]:
    """
    Load data into the database.
    
    Args:
        initializer: Database initializer
        data_dir: Path to the data directory
        
    Returns:
        Tuple[bool, str]: Success status and message
    """
    return initialize_database_data(initializer, data_dir)


def execute_query(initializer: DatabaseInitializer, query: str, 
                 params: Optional[Union[List, Dict]] = None) -> Tuple[bool, Optional[List[Dict[str, Any]]]]:
    """
    Execute a query.
    
    Args:
        initializer: Database initializer
        query: SQL query
        params: Query parameters
        
    Returns:
        Tuple[bool, Optional[List[Dict[str, Any]]]]: Success status and results
    """
    return initializer.execute_query(query, params)


def get_tables(initializer: DatabaseInitializer) -> List[str]:
    """
    Get a list of all tables in the database.
    
    Args:
        initializer: Database initializer
        
    Returns:
        List[str]: List of table names
    """
    return initializer.get_tables()


def get_columns(initializer: DatabaseInitializer, table_name: str) -> List[Dict[str, Any]]:
    """
    Get a list of columns in a table.
    
    Args:
        initializer: Database initializer
        table_name: Name of the table
        
    Returns:
        List[Dict[str, Any]]: List of column information
    """
    return initializer.get_columns(table_name)


def get_indexes(initializer: DatabaseInitializer, table_name: str) -> List[Dict[str, Any]]:
    """
    Get a list of indexes for a table.
    
    Args:
        initializer: Database initializer
        table_name: Name of the table
        
    Returns:
        List[Dict[str, Any]]: List of index information
    """
    return initializer.get_indexes(table_name)


def close_database(initializer: DatabaseInitializer) -> None:
    """
    Close the database connection.
    
    Args:
        initializer: Database initializer
    """
    initializer.close()


def test_database_connection(connection_string: str) -> Tuple[bool, str]:
    """
    Test a database connection.
    
    Args:
        connection_string: Database connection string
        
    Returns:
        Tuple[bool, str]: Success status and message
    """
    return test_connection(connection_string)


def validate_schema(initializer: DatabaseInitializer, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a database schema.
    
    Args:
        initializer: Database initializer
        schema: Schema definition
        
    Returns:
        Tuple[bool, List[str]]: Validation status and list of errors
    """
    return initializer.validate_schema(schema)


def validate_data(initializer: DatabaseInitializer, table_name: str, 
                 data: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """
    Validate data against a table schema.
    
    Args:
        initializer: Database initializer
        table_name: Name of the table
        data: List of data records
        
    Returns:
        Tuple[bool, List[str]]: Validation status and list of errors
    """
    return initializer.validate_data(table_name, data)


def insert_data(initializer: DatabaseInitializer, table_name: str, 
               data: List[Dict[str, Any]]) -> Tuple[bool, str]:
    """
    Insert data into a table.
    
    Args:
        initializer: Database initializer
        table_name: Name of the table
        data: List of data records
        
    Returns:
        Tuple[bool, str]: Success status and message
    """
    return initializer.insert_data(table_name, data)


def load_data_from_file(initializer: DatabaseInitializer, table_name: str, 
                       data_file: str) -> Tuple[bool, str]:
    """
    Load data from a file into a table.
    
    Args:
        initializer: Database initializer
        table_name: Name of the table
        data_file: Path to the data file
        
    Returns:
        Tuple[bool, str]: Success status and message
    """
    return initializer.load_data_from_file(table_name, data_file)
