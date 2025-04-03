"""
Database initialization functionality.
"""
import os
import logging
from typing import Dict, Any, List, Tuple, Optional, Union

from pythonweb_installer.database.connection import (
    DatabaseConnection,
    create_connection,
    get_connection_string,
    test_connection
)
from pythonweb_installer.database.schema import SchemaManager, create_schema_manager
from pythonweb_installer.database.data import DataManager, create_data_manager

logger = logging.getLogger(__name__)


class DatabaseInitializer:
    """
    Database initializer.
    """
    
    def __init__(self, connection_string: str):
        """
        Initialize the database initializer.
        
        Args:
            connection_string: Database connection string
        """
        self.connection_string = connection_string
        self.connection = None
        self.schema_manager = None
        self.data_manager = None
    
    def initialize(self) -> Tuple[bool, str]:
        """
        Initialize the database.
        
        Returns:
            Tuple[bool, str]: Success status and message
        """
        try:
            # Connect to the database
            self.connection = create_connection(self.connection_string)
            
            if not self.connection:
                return False, "Failed to connect to database"
            
            # Create the schema manager
            self.schema_manager = create_schema_manager(self.connection)
            
            # Create the data manager
            self.data_manager = create_data_manager(self.connection)
            
            logger.info("Initialized database")
            return True, "Database initialized successfully"
        
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            return False, f"Failed to initialize database: {str(e)}"
    
    def close(self) -> None:
        """
        Close the database connection.
        """
        if self.connection:
            self.connection.disconnect()
            self.connection = None
            self.schema_manager = None
            self.data_manager = None
    
    def create_schema(self, schema: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Create a database schema.
        
        Args:
            schema: Schema definition
            
        Returns:
            Tuple[bool, str]: Success status and message
        """
        if not self.schema_manager:
            return False, "Schema manager not initialized"
        
        return self.schema_manager.create_schema(schema)
    
    def create_schema_from_file(self, schema_file: str) -> Tuple[bool, str]:
        """
        Create a database schema from a file.
        
        Args:
            schema_file: Path to the schema file
            
        Returns:
            Tuple[bool, str]: Success status and message
        """
        if not self.schema_manager:
            return False, "Schema manager not initialized"
        
        return self.schema_manager.create_schema_from_file(schema_file)
    
    def drop_schema(self, schema: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Drop a database schema.
        
        Args:
            schema: Schema definition
            
        Returns:
            Tuple[bool, str]: Success status and message
        """
        if not self.schema_manager:
            return False, "Schema manager not initialized"
        
        return self.schema_manager.drop_schema(schema)
    
    def validate_schema(self, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate a database schema.
        
        Args:
            schema: Schema definition
            
        Returns:
            Tuple[bool, List[str]]: Validation status and list of errors
        """
        if not self.schema_manager:
            return False, ["Schema manager not initialized"]
        
        return self.schema_manager.validate_schema(schema)
    
    def insert_data(self, table_name: str, data: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """
        Insert data into a table.
        
        Args:
            table_name: Name of the table
            data: List of data records
            
        Returns:
            Tuple[bool, str]: Success status and message
        """
        if not self.data_manager:
            return False, "Data manager not initialized"
        
        return self.data_manager.insert_data(table_name, data)
    
    def load_data_from_file(self, table_name: str, data_file: str) -> Tuple[bool, str]:
        """
        Load data from a file into a table.
        
        Args:
            table_name: Name of the table
            data_file: Path to the data file
            
        Returns:
            Tuple[bool, str]: Success status and message
        """
        if not self.data_manager:
            return False, "Data manager not initialized"
        
        return self.data_manager.load_data_from_file(table_name, data_file)
    
    def initialize_data(self, data_dir: str) -> Tuple[bool, str]:
        """
        Initialize data from a directory.
        
        Args:
            data_dir: Path to the data directory
            
        Returns:
            Tuple[bool, str]: Success status and message
        """
        if not self.data_manager:
            return False, "Data manager not initialized"
        
        return self.data_manager.initialize_data(data_dir)
    
    def validate_data(self, table_name: str, data: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """
        Validate data against a table schema.
        
        Args:
            table_name: Name of the table
            data: List of data records
            
        Returns:
            Tuple[bool, List[str]]: Validation status and list of errors
        """
        if not self.data_manager:
            return False, ["Data manager not initialized"]
        
        return self.data_manager.validate_data(table_name, data)
    
    def execute_query(self, query: str, params: Optional[Union[List, Dict]] = None) -> Tuple[bool, Optional[List[Dict[str, Any]]]]:
        """
        Execute a query.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            Tuple[bool, Optional[List[Dict[str, Any]]]]: Success status and results
        """
        if not self.connection:
            return False, None
        
        return self.connection.execute(query, params)
    
    def get_tables(self) -> List[str]:
        """
        Get a list of all tables in the database.
        
        Returns:
            List[str]: List of table names
        """
        if not self.connection:
            return []
        
        return self.connection.get_tables()
    
    def get_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get a list of columns in a table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            List[Dict[str, Any]]: List of column information
        """
        if not self.connection:
            return []
        
        return self.connection.get_columns(table_name)
    
    def get_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get a list of indexes for a table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            List[Dict[str, Any]]: List of index information
        """
        if not self.connection:
            return []
        
        return self.connection.get_indexes(table_name)


def initialize_database(connection_string: str) -> Tuple[bool, str, Optional[DatabaseInitializer]]:
    """
    Initialize a database.
    
    Args:
        connection_string: Database connection string
        
    Returns:
        Tuple[bool, str, Optional[DatabaseInitializer]]: Success status, message, and initializer
    """
    try:
        # Create a database initializer
        initializer = DatabaseInitializer(connection_string)
        
        # Initialize the database
        success, message = initializer.initialize()
        
        if success:
            return True, message, initializer
        else:
            return False, message, None
    
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        return False, f"Failed to initialize database: {str(e)}", None


def create_database_schema(initializer: DatabaseInitializer, schema_file: str) -> Tuple[bool, str]:
    """
    Create a database schema.
    
    Args:
        initializer: Database initializer
        schema_file: Path to the schema file
        
    Returns:
        Tuple[bool, str]: Success status and message
    """
    try:
        # Validate the schema file
        if not os.path.exists(schema_file):
            return False, f"Schema file {schema_file} does not exist"
        
        # Create the schema
        return initializer.create_schema_from_file(schema_file)
    
    except Exception as e:
        logger.error(f"Failed to create database schema: {str(e)}")
        return False, f"Failed to create database schema: {str(e)}"


def initialize_database_data(initializer: DatabaseInitializer, data_dir: str) -> Tuple[bool, str]:
    """
    Initialize database data.
    
    Args:
        initializer: Database initializer
        data_dir: Path to the data directory
        
    Returns:
        Tuple[bool, str]: Success status and message
    """
    try:
        # Validate the data directory
        if not os.path.exists(data_dir):
            return False, f"Data directory {data_dir} does not exist"
        
        # Initialize the data
        return initializer.initialize_data(data_dir)
    
    except Exception as e:
        logger.error(f"Failed to initialize database data: {str(e)}")
        return False, f"Failed to initialize database data: {str(e)}"
