"""
Unit tests for database initialization functionality.
"""
import os
import json
import tempfile
from unittest.mock import patch, MagicMock

import pytest

from pythonweb_installer.database.connection import DatabaseConnection
from pythonweb_installer.database.schema import SchemaManager
from pythonweb_installer.database.data import DataManager
from pythonweb_installer.database.initialization import (
    DatabaseInitializer,
    initialize_database,
    create_database_schema,
    initialize_database_data
)


class TestDatabaseInitialization:
    """Tests for database initialization functionality."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database path."""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.remove(path)
    
    @pytest.fixture
    def connection_string(self, temp_db_path):
        """Create a connection string."""
        return f'sqlite:///{temp_db_path}'
    
    @pytest.fixture
    def initializer(self, connection_string):
        """Create a database initializer."""
        initializer = DatabaseInitializer(connection_string)
        initializer.initialize()
        yield initializer
        initializer.close()
    
    @pytest.fixture
    def temp_schema_file(self):
        """Create a temporary schema file."""
        fd, path = tempfile.mkstemp(suffix='.json')
        os.close(fd)
        
        # Create a simple schema
        schema = {
            "tables": [
                {
                    "name": "users",
                    "columns": [
                        {"name": "id", "type": "INTEGER", "primary_key": True},
                        {"name": "username", "type": "TEXT", "not_null": True, "unique": True},
                        {"name": "email", "type": "TEXT", "not_null": True}
                    ],
                    "indexes": [
                        {"name": "idx_users_email", "columns": ["email"], "unique": False}
                    ]
                }
            ]
        }
        
        # Write the schema to the file
        with open(path, 'w') as f:
            json.dump(schema, f)
        
        yield path
        
        if os.path.exists(path):
            os.remove(path)
    
    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary data directory."""
        temp_dir = tempfile.mkdtemp()
        
        # Create a directory structure
        os.makedirs(os.path.join(temp_dir, 'users'), exist_ok=True)
        
        # Create a data file
        with open(os.path.join(temp_dir, 'users', 'users.json'), 'w') as f:
            json.dump([
                {"id": 1, "username": "alice", "email": "alice@example.com"},
                {"id": 2, "username": "bob", "email": "bob@example.com"}
            ], f)
        
        yield temp_dir
        
        # Clean up
        import shutil
        shutil.rmtree(temp_dir)
    
    def test_initialize(self, connection_string):
        """Test initializing a database."""
        # Create an initializer
        initializer = DatabaseInitializer(connection_string)
        
        # Initialize the database
        success, message = initializer.initialize()
        
        assert success is True
        assert "initialized successfully" in message
        assert initializer.connection is not None
        assert initializer.schema_manager is not None
        assert initializer.data_manager is not None
        
        initializer.close()
    
    def test_initialize_failure(self):
        """Test initializing a database with an invalid connection string."""
        # Create an initializer with an invalid connection string
        initializer = DatabaseInitializer('invalid://connection/string')
        
        # Initialize the database
        success, message = initializer.initialize()
        
        assert success is False
        assert "Failed to" in message
        assert initializer.connection is None
        assert initializer.schema_manager is None
        assert initializer.data_manager is None
    
    def test_close(self, initializer):
        """Test closing a database connection."""
        # Close the connection
        initializer.close()
        
        assert initializer.connection is None
        assert initializer.schema_manager is None
        assert initializer.data_manager is None
    
    def test_create_schema(self, initializer):
        """Test creating a database schema."""
        # Define a simple schema
        schema = {
            "tables": [
                {
                    "name": "users",
                    "columns": [
                        {"name": "id", "type": "INTEGER", "primary_key": True},
                        {"name": "username", "type": "TEXT", "not_null": True}
                    ]
                }
            ]
        }
        
        # Create the schema
        success, message = initializer.create_schema(schema)
        
        assert success is True
        assert "created successfully" in message
        
        # Verify the table exists
        assert initializer.connection.table_exists("users") is True
    
    def test_create_schema_from_file(self, initializer, temp_schema_file):
        """Test creating a database schema from a file."""
        # Create the schema
        success, message = initializer.create_schema_from_file(temp_schema_file)
        
        assert success is True
        assert "created successfully" in message
        
        # Verify the table exists
        assert initializer.connection.table_exists("users") is True
    
    def test_drop_schema(self, initializer):
        """Test dropping a database schema."""
        # Define a simple schema
        schema = {
            "tables": [
                {
                    "name": "users",
                    "columns": [
                        {"name": "id", "type": "INTEGER", "primary_key": True},
                        {"name": "username", "type": "TEXT", "not_null": True}
                    ]
                }
            ]
        }
        
        # Create the schema
        initializer.create_schema(schema)
        
        # Drop the schema
        success, message = initializer.drop_schema(schema)
        
        assert success is True
        assert "dropped successfully" in message
        
        # Verify the table no longer exists
        assert initializer.connection.table_exists("users") is False
    
    def test_validate_schema(self, initializer):
        """Test validating a database schema."""
        # Define a valid schema
        valid_schema = {
            "tables": [
                {
                    "name": "users",
                    "columns": [
                        {"name": "id", "type": "INTEGER", "primary_key": True},
                        {"name": "username", "type": "TEXT", "not_null": True}
                    ]
                }
            ]
        }
        
        # Validate the schema
        valid, errors = initializer.validate_schema(valid_schema)
        
        assert valid is True
        assert len(errors) == 0
        
        # Define an invalid schema
        invalid_schema = {
            "tables": [
                {
                    "columns": [
                        {"name": "id", "type": "INTEGER", "primary_key": True}
                    ]
                }
            ]
        }
        
        # Validate the schema
        valid, errors = initializer.validate_schema(invalid_schema)
        
        assert valid is False
        assert len(errors) > 0
    
    def test_insert_data(self, initializer):
        """Test inserting data into a table."""
        # Create a table
        schema = {
            "tables": [
                {
                    "name": "users",
                    "columns": [
                        {"name": "id", "type": "INTEGER", "primary_key": True},
                        {"name": "username", "type": "TEXT", "not_null": True},
                        {"name": "email", "type": "TEXT"}
                    ]
                }
            ]
        }
        
        initializer.create_schema(schema)
        
        # Define some data
        data = [
            {"id": 1, "username": "alice", "email": "alice@example.com"},
            {"id": 2, "username": "bob", "email": "bob@example.com"}
        ]
        
        # Insert the data
        success, message = initializer.insert_data("users", data)
        
        assert success is True
        assert "inserted successfully" in message
        
        # Verify the data was inserted
        success, results = initializer.execute_query("SELECT * FROM users")
        
        assert success is True
        assert results is not None
        assert len(results) == 2
    
    def test_load_data_from_file(self, initializer, temp_schema_file):
        """Test loading data from a file."""
        # Create the schema
        initializer.create_schema_from_file(temp_schema_file)
        
        # Create a data file
        fd, path = tempfile.mkstemp(suffix='.json')
        os.close(fd)
        
        try:
            # Write some data to the file
            with open(path, 'w') as f:
                json.dump([
                    {"id": 1, "username": "alice", "email": "alice@example.com"},
                    {"id": 2, "username": "bob", "email": "bob@example.com"}
                ], f)
            
            # Load the data
            success, message = initializer.load_data_from_file("users", path)
            
            assert success is True
            assert "inserted successfully" in message
            
            # Verify the data was loaded
            success, results = initializer.execute_query("SELECT * FROM users")
            
            assert success is True
            assert results is not None
            assert len(results) == 2
        finally:
            if os.path.exists(path):
                os.remove(path)
    
    def test_initialize_data(self, initializer, temp_schema_file, temp_data_dir):
        """Test initializing data from a directory."""
        # Create the schema
        initializer.create_schema_from_file(temp_schema_file)
        
        # Initialize the data
        success, message = initializer.initialize_data(temp_data_dir)
        
        assert success is True
        assert "initialized successfully" in message
        
        # Verify the data was loaded
        success, results = initializer.execute_query("SELECT * FROM users")
        
        assert success is True
        assert results is not None
        assert len(results) == 2
    
    def test_validate_data(self, initializer):
        """Test validating data against a table schema."""
        # Create a table
        schema = {
            "tables": [
                {
                    "name": "users",
                    "columns": [
                        {"name": "id", "type": "INTEGER", "primary_key": True},
                        {"name": "username", "type": "TEXT", "not_null": True},
                        {"name": "email", "type": "TEXT"}
                    ]
                }
            ]
        }
        
        initializer.create_schema(schema)
        
        # Define some valid data
        valid_data = [
            {"id": 1, "username": "alice", "email": "alice@example.com"},
            {"id": 2, "username": "bob", "email": "bob@example.com"}
        ]
        
        # Validate the data
        valid, errors = initializer.validate_data("users", valid_data)
        
        assert valid is True
        assert len(errors) == 0
        
        # Define some invalid data
        invalid_data = [
            {"id": 1, "email": "alice@example.com"},  # Missing required username
            {"id": 2, "username": "bob", "email": "bob@example.com"}
        ]
        
        # Validate the data
        valid, errors = initializer.validate_data("users", invalid_data)
        
        assert valid is False
        assert len(errors) > 0
    
    def test_execute_query(self, initializer):
        """Test executing a query."""
        # Create a table
        schema = {
            "tables": [
                {
                    "name": "users",
                    "columns": [
                        {"name": "id", "type": "INTEGER", "primary_key": True},
                        {"name": "username", "type": "TEXT", "not_null": True}
                    ]
                }
            ]
        }
        
        initializer.create_schema(schema)
        
        # Insert some data
        initializer.execute_query("INSERT INTO users (id, username) VALUES (?, ?)", [1, "alice"])
        initializer.execute_query("INSERT INTO users (id, username) VALUES (?, ?)", [2, "bob"])
        
        # Execute a SELECT query
        success, results = initializer.execute_query("SELECT * FROM users")
        
        assert success is True
        assert results is not None
        assert len(results) == 2
        
        # Check the first record
        assert results[0]['id'] == 1
        assert results[0]['username'] == 'alice'
        
        # Check the second record
        assert results[1]['id'] == 2
        assert results[1]['username'] == 'bob'
    
    def test_get_tables(self, initializer):
        """Test getting a list of tables."""
        # Create some tables
        schema = {
            "tables": [
                {
                    "name": "users",
                    "columns": [
                        {"name": "id", "type": "INTEGER", "primary_key": True}
                    ]
                },
                {
                    "name": "posts",
                    "columns": [
                        {"name": "id", "type": "INTEGER", "primary_key": True}
                    ]
                }
            ]
        }
        
        initializer.create_schema(schema)
        
        # Get the tables
        tables = initializer.get_tables()
        
        assert len(tables) == 2
        assert "users" in tables
        assert "posts" in tables
    
    def test_get_columns(self, initializer):
        """Test getting a list of columns in a table."""
        # Create a table
        schema = {
            "tables": [
                {
                    "name": "users",
                    "columns": [
                        {"name": "id", "type": "INTEGER", "primary_key": True},
                        {"name": "username", "type": "TEXT", "not_null": True},
                        {"name": "email", "type": "TEXT"}
                    ]
                }
            ]
        }
        
        initializer.create_schema(schema)
        
        # Get the columns
        columns = initializer.get_columns("users")
        
        assert len(columns) == 3
        assert any(col['name'] == 'id' for col in columns)
        assert any(col['name'] == 'username' for col in columns)
        assert any(col['name'] == 'email' for col in columns)
    
    def test_get_indexes(self, initializer):
        """Test getting a list of indexes for a table."""
        # Create a table with indexes
        schema = {
            "tables": [
                {
                    "name": "users",
                    "columns": [
                        {"name": "id", "type": "INTEGER", "primary_key": True},
                        {"name": "username", "type": "TEXT", "not_null": True},
                        {"name": "email", "type": "TEXT"}
                    ],
                    "indexes": [
                        {"name": "idx_users_username", "columns": ["username"], "unique": True},
                        {"name": "idx_users_email", "columns": ["email"], "unique": False}
                    ]
                }
            ]
        }
        
        initializer.create_schema(schema)
        
        # Get the indexes
        indexes = initializer.get_indexes("users")
        
        assert len(indexes) == 2
        assert any(idx['name'] == 'idx_users_username' for idx in indexes)
        assert any(idx['name'] == 'idx_users_email' for idx in indexes)
    
    def test_initialize_database(self, connection_string):
        """Test initializing a database."""
        # Initialize the database
        success, message, initializer = initialize_database(connection_string)
        
        assert success is True
        assert "initialized successfully" in message
        assert initializer is not None
        assert isinstance(initializer, DatabaseInitializer)
        
        initializer.close()
    
    def test_initialize_database_failure(self):
        """Test initializing a database with an invalid connection string."""
        # Initialize the database
        success, message, initializer = initialize_database('invalid://connection/string')
        
        assert success is False
        assert "Failed to" in message
        assert initializer is None
    
    def test_create_database_schema(self, initializer, temp_schema_file):
        """Test creating a database schema."""
        # Create the schema
        success, message = create_database_schema(initializer, temp_schema_file)
        
        assert success is True
        assert "created successfully" in message
        
        # Verify the table exists
        assert initializer.connection.table_exists("users") is True
    
    def test_create_database_schema_file_not_exists(self, initializer):
        """Test creating a database schema from a non-existent file."""
        # Create the schema
        success, message = create_database_schema(initializer, "nonexistent.json")
        
        assert success is False
        assert "does not exist" in message
    
    def test_initialize_database_data(self, initializer, temp_schema_file, temp_data_dir):
        """Test initializing database data."""
        # Create the schema
        initializer.create_schema_from_file(temp_schema_file)
        
        # Initialize the data
        success, message = initialize_database_data(initializer, temp_data_dir)
        
        assert success is True
        assert "initialized successfully" in message
        
        # Verify the data was loaded
        success, results = initializer.execute_query("SELECT * FROM users")
        
        assert success is True
        assert results is not None
        assert len(results) == 2
    
    def test_initialize_database_data_directory_not_exists(self, initializer):
        """Test initializing database data from a non-existent directory."""
        # Initialize the data
        success, message = initialize_database_data(initializer, "nonexistent")
        
        assert success is False
        assert "does not exist" in message
