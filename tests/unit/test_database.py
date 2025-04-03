"""
Unit tests for the high-level database module.
"""
import os
import json
import tempfile
from unittest.mock import patch, MagicMock

import pytest

from pythonweb_installer import database
from pythonweb_installer.database.initialization import DatabaseInitializer


class TestDatabase:
    """Tests for the high-level database module."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database path."""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.remove(path)
    
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
    
    def test_init_database_sqlite(self, temp_db_path):
        """Test initializing a SQLite database."""
        # Initialize the database
        success, message, initializer = database.init_database('sqlite', db_path=temp_db_path)
        
        assert success is True
        assert "initialized successfully" in message
        assert initializer is not None
        assert isinstance(initializer, DatabaseInitializer)
        
        # Clean up
        initializer.close()
    
    @patch('pythonweb_installer.database.connection.POSTGRES_AVAILABLE', True)
    @patch('psycopg2.connect')
    def test_init_database_postgresql(self, mock_connect):
        """Test initializing a PostgreSQL database."""
        # Mock the connection
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        # Initialize the database
        success, message, initializer = database.init_database(
            'postgresql',
            username='user',
            password='pass',
            hostname='localhost',
            port=5432,
            database='testdb'
        )
        
        assert success is True
        assert "initialized successfully" in message
        assert initializer is not None
        assert isinstance(initializer, DatabaseInitializer)
        
        # Clean up
        initializer.close()
    
    @patch('pythonweb_installer.database.connection.MYSQL_AVAILABLE', True)
    @patch('mysql.connector.connect')
    def test_init_database_mysql(self, mock_connect):
        """Test initializing a MySQL database."""
        # Mock the connection
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        # Initialize the database
        success, message, initializer = database.init_database(
            'mysql',
            username='user',
            password='pass',
            hostname='localhost',
            port=3306,
            database='testdb'
        )
        
        assert success is True
        assert "initialized successfully" in message
        assert initializer is not None
        assert isinstance(initializer, DatabaseInitializer)
        
        # Clean up
        initializer.close()
    
    def test_init_database_unsupported(self):
        """Test initializing an unsupported database type."""
        # Initialize the database
        with pytest.raises(ValueError):
            database.init_database('unsupported')
    
    def test_create_schema(self, temp_db_path, temp_schema_file):
        """Test creating a database schema."""
        # Initialize the database
        success, message, initializer = database.init_database('sqlite', db_path=temp_db_path)
        
        assert success is True
        
        try:
            # Create the schema
            success, message = database.create_schema(initializer, temp_schema_file)
            
            assert success is True
            assert "created successfully" in message
            
            # Verify the table exists
            assert initializer.connection.table_exists("users") is True
        finally:
            # Clean up
            initializer.close()
    
    def test_load_data(self, temp_db_path, temp_schema_file, temp_data_dir):
        """Test loading data into the database."""
        # Initialize the database
        success, message, initializer = database.init_database('sqlite', db_path=temp_db_path)
        
        assert success is True
        
        try:
            # Create the schema
            database.create_schema(initializer, temp_schema_file)
            
            # Load the data
            success, message = database.load_data(initializer, temp_data_dir)
            
            assert success is True
            assert "initialized successfully" in message
            
            # Verify the data was loaded
            success, results = database.execute_query(initializer, "SELECT * FROM users")
            
            assert success is True
            assert results is not None
            assert len(results) == 2
        finally:
            # Clean up
            initializer.close()
    
    def test_execute_query(self, temp_db_path):
        """Test executing a query."""
        # Initialize the database
        success, message, initializer = database.init_database('sqlite', db_path=temp_db_path)
        
        assert success is True
        
        try:
            # Create a table
            database.execute_query(initializer, "CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
            
            # Insert some data
            database.execute_query(initializer, "INSERT INTO test (id, name) VALUES (?, ?)", [1, "Alice"])
            database.execute_query(initializer, "INSERT INTO test (id, name) VALUES (?, ?)", [2, "Bob"])
            
            # Execute a SELECT query
            success, results = database.execute_query(initializer, "SELECT * FROM test")
            
            assert success is True
            assert results is not None
            assert len(results) == 2
            
            # Check the first record
            assert results[0]['id'] == 1
            assert results[0]['name'] == 'Alice'
            
            # Check the second record
            assert results[1]['id'] == 2
            assert results[1]['name'] == 'Bob'
        finally:
            # Clean up
            initializer.close()
    
    def test_get_tables(self, temp_db_path):
        """Test getting a list of tables."""
        # Initialize the database
        success, message, initializer = database.init_database('sqlite', db_path=temp_db_path)
        
        assert success is True
        
        try:
            # Create some tables
            database.execute_query(initializer, "CREATE TABLE users (id INTEGER PRIMARY KEY)")
            database.execute_query(initializer, "CREATE TABLE posts (id INTEGER PRIMARY KEY)")
            
            # Get the tables
            tables = database.get_tables(initializer)
            
            assert len(tables) == 2
            assert "users" in tables
            assert "posts" in tables
        finally:
            # Clean up
            initializer.close()
    
    def test_get_columns(self, temp_db_path):
        """Test getting a list of columns in a table."""
        # Initialize the database
        success, message, initializer = database.init_database('sqlite', db_path=temp_db_path)
        
        assert success is True
        
        try:
            # Create a table
            database.execute_query(initializer, """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    username TEXT NOT NULL,
                    email TEXT
                )
            """)
            
            # Get the columns
            columns = database.get_columns(initializer, "users")
            
            assert len(columns) == 3
            assert any(col['name'] == 'id' for col in columns)
            assert any(col['name'] == 'username' for col in columns)
            assert any(col['name'] == 'email' for col in columns)
        finally:
            # Clean up
            initializer.close()
    
    def test_get_indexes(self, temp_db_path):
        """Test getting a list of indexes for a table."""
        # Initialize the database
        success, message, initializer = database.init_database('sqlite', db_path=temp_db_path)
        
        assert success is True
        
        try:
            # Create a table with indexes
            database.execute_query(initializer, """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    username TEXT NOT NULL,
                    email TEXT
                )
            """)
            
            database.execute_query(initializer, "CREATE UNIQUE INDEX idx_users_username ON users (username)")
            database.execute_query(initializer, "CREATE INDEX idx_users_email ON users (email)")
            
            # Get the indexes
            indexes = database.get_indexes(initializer, "users")
            
            assert len(indexes) == 2
            assert any(idx['name'] == 'idx_users_username' for idx in indexes)
            assert any(idx['name'] == 'idx_users_email' for idx in indexes)
        finally:
            # Clean up
            initializer.close()
    
    def test_close_database(self, temp_db_path):
        """Test closing a database connection."""
        # Initialize the database
        success, message, initializer = database.init_database('sqlite', db_path=temp_db_path)
        
        assert success is True
        
        # Close the database
        database.close_database(initializer)
        
        assert initializer.connection is None
        assert initializer.schema_manager is None
        assert initializer.data_manager is None
    
    def test_test_database_connection(self, temp_db_path):
        """Test testing a database connection."""
        # Create a connection string
        connection_string = f'sqlite:///{temp_db_path}'
        
        # Test the connection
        success, message = database.test_database_connection(connection_string)
        
        assert success is True
        assert "Successfully connected" in message
    
    def test_validate_schema(self, temp_db_path):
        """Test validating a database schema."""
        # Initialize the database
        success, message, initializer = database.init_database('sqlite', db_path=temp_db_path)
        
        assert success is True
        
        try:
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
            valid, errors = database.validate_schema(initializer, valid_schema)
            
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
            valid, errors = database.validate_schema(initializer, invalid_schema)
            
            assert valid is False
            assert len(errors) > 0
        finally:
            # Clean up
            initializer.close()
    
    def test_validate_data(self, temp_db_path):
        """Test validating data against a table schema."""
        # Initialize the database
        success, message, initializer = database.init_database('sqlite', db_path=temp_db_path)
        
        assert success is True
        
        try:
            # Create a table
            database.execute_query(initializer, """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    username TEXT NOT NULL,
                    email TEXT
                )
            """)
            
            # Define some valid data
            valid_data = [
                {"id": 1, "username": "alice", "email": "alice@example.com"},
                {"id": 2, "username": "bob", "email": "bob@example.com"}
            ]
            
            # Validate the data
            valid, errors = database.validate_data(initializer, "users", valid_data)
            
            assert valid is True
            assert len(errors) == 0
            
            # Define some invalid data
            invalid_data = [
                {"id": 1, "email": "alice@example.com"},  # Missing required username
                {"id": 2, "username": "bob", "email": "bob@example.com"}
            ]
            
            # Validate the data
            valid, errors = database.validate_data(initializer, "users", invalid_data)
            
            assert valid is False
            assert len(errors) > 0
        finally:
            # Clean up
            initializer.close()
    
    def test_insert_data(self, temp_db_path):
        """Test inserting data into a table."""
        # Initialize the database
        success, message, initializer = database.init_database('sqlite', db_path=temp_db_path)
        
        assert success is True
        
        try:
            # Create a table
            database.execute_query(initializer, """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    username TEXT NOT NULL,
                    email TEXT
                )
            """)
            
            # Define some data
            data = [
                {"id": 1, "username": "alice", "email": "alice@example.com"},
                {"id": 2, "username": "bob", "email": "bob@example.com"}
            ]
            
            # Insert the data
            success, message = database.insert_data(initializer, "users", data)
            
            assert success is True
            assert "inserted successfully" in message
            
            # Verify the data was inserted
            success, results = database.execute_query(initializer, "SELECT * FROM users")
            
            assert success is True
            assert results is not None
            assert len(results) == 2
        finally:
            # Clean up
            initializer.close()
    
    def test_load_data_from_file(self, temp_db_path):
        """Test loading data from a file."""
        # Initialize the database
        success, message, initializer = database.init_database('sqlite', db_path=temp_db_path)
        
        assert success is True
        
        try:
            # Create a table
            database.execute_query(initializer, """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    username TEXT NOT NULL,
                    email TEXT
                )
            """)
            
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
                success, message = database.load_data_from_file(initializer, "users", path)
                
                assert success is True
                assert "inserted successfully" in message
                
                # Verify the data was loaded
                success, results = database.execute_query(initializer, "SELECT * FROM users")
                
                assert success is True
                assert results is not None
                assert len(results) == 2
            finally:
                if os.path.exists(path):
                    os.remove(path)
        finally:
            # Clean up
            initializer.close()
