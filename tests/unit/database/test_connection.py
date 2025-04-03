"""
Unit tests for database connection functionality.
"""
import os
import tempfile
import sqlite3
from unittest.mock import patch, MagicMock

import pytest

from pythonweb_installer.database.connection import (
    DatabaseConnection,
    create_connection,
    get_connection_string,
    parse_connection_string,
    test_connection
)


class TestDatabaseConnection:
    """Tests for database connection functionality."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database path."""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.remove(path)
    
    def test_determine_db_type_sqlite(self):
        """Test determining the database type for SQLite."""
        connection = DatabaseConnection('sqlite:///test.db')
        assert connection.db_type == 'sqlite'
    
    @patch('pythonweb_installer.database.connection.POSTGRES_AVAILABLE', True)
    def test_determine_db_type_postgresql(self):
        """Test determining the database type for PostgreSQL."""
        connection = DatabaseConnection('postgresql://user:pass@localhost:5432/testdb')
        assert connection.db_type == 'postgresql'
    
    @patch('pythonweb_installer.database.connection.MYSQL_AVAILABLE', True)
    def test_determine_db_type_mysql(self):
        """Test determining the database type for MySQL."""
        connection = DatabaseConnection('mysql://user:pass@localhost:3306/testdb')
        assert connection.db_type == 'mysql'
    
    def test_determine_db_type_unsupported(self):
        """Test determining an unsupported database type."""
        with pytest.raises(ValueError):
            DatabaseConnection('unsupported://localhost/testdb')
    
    @patch('pythonweb_installer.database.connection.POSTGRES_AVAILABLE', False)
    def test_determine_db_type_postgresql_not_available(self):
        """Test determining the database type for PostgreSQL when not available."""
        with pytest.raises(ImportError):
            DatabaseConnection('postgresql://user:pass@localhost:5432/testdb')
    
    @patch('pythonweb_installer.database.connection.MYSQL_AVAILABLE', False)
    def test_determine_db_type_mysql_not_available(self):
        """Test determining the database type for MySQL when not available."""
        with pytest.raises(ImportError):
            DatabaseConnection('mysql://user:pass@localhost:3306/testdb')
    
    def test_connect_sqlite(self, temp_db_path):
        """Test connecting to a SQLite database."""
        connection_string = f'sqlite:///{temp_db_path}'
        connection = DatabaseConnection(connection_string)
        
        assert connection.connect() is True
        assert connection.connection is not None
        assert connection.cursor is not None
        
        connection.disconnect()
    
    @patch('psycopg2.connect')
    @patch('pythonweb_installer.database.connection.POSTGRES_AVAILABLE', True)
    def test_connect_postgresql(self, mock_connect):
        """Test connecting to a PostgreSQL database."""
        # Mock the connection
        mock_connection = MagicMock()
        mock_connect.return_value = mock_connection
        
        connection_string = 'postgresql://user:pass@localhost:5432/testdb'
        connection = DatabaseConnection(connection_string)
        
        assert connection.connect() is True
        assert connection.connection is not None
        assert connection.cursor is not None
        
        # Check that psycopg2.connect was called with the correct arguments
        mock_connect.assert_called_once_with(
            host='localhost',
            port=5432,
            user='user',
            password='pass',
            dbname='testdb'
        )
        
        connection.disconnect()
    
    @patch('mysql.connector.connect')
    @patch('pythonweb_installer.database.connection.MYSQL_AVAILABLE', True)
    def test_connect_mysql(self, mock_connect):
        """Test connecting to a MySQL database."""
        # Mock the connection
        mock_connection = MagicMock()
        mock_connect.return_value = mock_connection
        
        connection_string = 'mysql://user:pass@localhost:3306/testdb'
        connection = DatabaseConnection(connection_string)
        
        assert connection.connect() is True
        assert connection.connection is not None
        assert connection.cursor is not None
        
        # Check that mysql.connector.connect was called with the correct arguments
        mock_connect.assert_called_once_with(
            host='localhost',
            port=3306,
            user='user',
            password='pass',
            database='testdb'
        )
        
        connection.disconnect()
    
    def test_disconnect(self, temp_db_path):
        """Test disconnecting from a database."""
        connection_string = f'sqlite:///{temp_db_path}'
        connection = DatabaseConnection(connection_string)
        
        # Connect to the database
        connection.connect()
        
        # Disconnect from the database
        assert connection.disconnect() is True
        assert connection.connection is None
        assert connection.cursor is None
    
    def test_disconnect_not_connected(self):
        """Test disconnecting when not connected."""
        connection = DatabaseConnection('sqlite:///test.db')
        
        # Disconnect from the database
        assert connection.disconnect() is False
    
    def test_execute_select(self, temp_db_path):
        """Test executing a SELECT query."""
        connection_string = f'sqlite:///{temp_db_path}'
        connection = DatabaseConnection(connection_string)
        
        # Connect to the database
        connection.connect()
        
        # Create a table
        connection.execute('CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)')
        
        # Insert some data
        connection.execute('INSERT INTO test (id, name) VALUES (1, "test")')
        connection.commit()
        
        # Execute a SELECT query
        success, results = connection.execute('SELECT * FROM test')
        
        assert success is True
        assert results is not None
        assert len(results) == 1
        assert results[0]['id'] == 1
        assert results[0]['name'] == 'test'
        
        connection.disconnect()
    
    def test_execute_insert(self, temp_db_path):
        """Test executing an INSERT query."""
        connection_string = f'sqlite:///{temp_db_path}'
        connection = DatabaseConnection(connection_string)
        
        # Connect to the database
        connection.connect()
        
        # Create a table
        connection.execute('CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)')
        
        # Execute an INSERT query
        success, results = connection.execute('INSERT INTO test (id, name) VALUES (?, ?)', [1, 'test'])
        
        assert success is True
        assert results is None
        
        # Verify the data was inserted
        success, results = connection.execute('SELECT * FROM test')
        
        assert success is True
        assert results is not None
        assert len(results) == 1
        assert results[0]['id'] == 1
        assert results[0]['name'] == 'test'
        
        connection.disconnect()
    
    def test_execute_not_connected(self):
        """Test executing a query when not connected."""
        connection = DatabaseConnection('sqlite:///test.db')
        
        # Execute a query
        success, results = connection.execute('SELECT 1')
        
        assert success is False
        assert results is None
    
    def test_commit(self, temp_db_path):
        """Test committing a transaction."""
        connection_string = f'sqlite:///{temp_db_path}'
        connection = DatabaseConnection(connection_string)
        
        # Connect to the database
        connection.connect()
        
        # Create a table
        connection.execute('CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)')
        
        # Insert some data
        connection.execute('INSERT INTO test (id, name) VALUES (1, "test")')
        
        # Commit the transaction
        assert connection.commit() is True
        
        # Verify the data was committed
        success, results = connection.execute('SELECT * FROM test')
        
        assert success is True
        assert results is not None
        assert len(results) == 1
        
        connection.disconnect()
    
    def test_commit_not_connected(self):
        """Test committing a transaction when not connected."""
        connection = DatabaseConnection('sqlite:///test.db')
        
        # Commit the transaction
        assert connection.commit() is False
    
    def test_rollback(self, temp_db_path):
        """Test rolling back a transaction."""
        connection_string = f'sqlite:///{temp_db_path}'
        connection = DatabaseConnection(connection_string)
        
        # Connect to the database
        connection.connect()
        
        # Create a table
        connection.execute('CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)')
        connection.commit()
        
        # Insert some data
        connection.execute('INSERT INTO test (id, name) VALUES (1, "test")')
        
        # Rollback the transaction
        assert connection.rollback() is True
        
        # Verify the data was not committed
        success, results = connection.execute('SELECT * FROM test')
        
        assert success is True
        assert results is not None
        assert len(results) == 0
        
        connection.disconnect()
    
    def test_rollback_not_connected(self):
        """Test rolling back a transaction when not connected."""
        connection = DatabaseConnection('sqlite:///test.db')
        
        # Rollback the transaction
        assert connection.rollback() is False
    
    def test_table_exists(self, temp_db_path):
        """Test checking if a table exists."""
        connection_string = f'sqlite:///{temp_db_path}'
        connection = DatabaseConnection(connection_string)
        
        # Connect to the database
        connection.connect()
        
        # Create a table
        connection.execute('CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)')
        connection.commit()
        
        # Check if the table exists
        assert connection.table_exists('test') is True
        assert connection.table_exists('nonexistent') is False
        
        connection.disconnect()
    
    def test_table_exists_not_connected(self):
        """Test checking if a table exists when not connected."""
        connection = DatabaseConnection('sqlite:///test.db')
        
        # Check if a table exists
        assert connection.table_exists('test') is False
    
    def test_get_tables(self, temp_db_path):
        """Test getting a list of tables."""
        connection_string = f'sqlite:///{temp_db_path}'
        connection = DatabaseConnection(connection_string)
        
        # Connect to the database
        connection.connect()
        
        # Create some tables
        connection.execute('CREATE TABLE test1 (id INTEGER PRIMARY KEY, name TEXT)')
        connection.execute('CREATE TABLE test2 (id INTEGER PRIMARY KEY, name TEXT)')
        connection.commit()
        
        # Get the tables
        tables = connection.get_tables()
        
        assert len(tables) == 2
        assert 'test1' in tables
        assert 'test2' in tables
        
        connection.disconnect()
    
    def test_get_tables_not_connected(self):
        """Test getting a list of tables when not connected."""
        connection = DatabaseConnection('sqlite:///test.db')
        
        # Get the tables
        tables = connection.get_tables()
        
        assert tables == []
    
    def test_get_columns(self, temp_db_path):
        """Test getting a list of columns in a table."""
        connection_string = f'sqlite:///{temp_db_path}'
        connection = DatabaseConnection(connection_string)
        
        # Connect to the database
        connection.connect()
        
        # Create a table
        connection.execute('CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT NOT NULL, age INTEGER DEFAULT 0)')
        connection.commit()
        
        # Get the columns
        columns = connection.get_columns('test')
        
        assert len(columns) == 3
        
        # Check the id column
        id_column = next(col for col in columns if col['name'] == 'id')
        assert id_column['type'] == 'INTEGER'
        assert id_column['primary_key'] is True
        
        # Check the name column
        name_column = next(col for col in columns if col['name'] == 'name')
        assert name_column['type'] == 'TEXT'
        assert name_column['nullable'] is False
        
        # Check the age column
        age_column = next(col for col in columns if col['name'] == 'age')
        assert age_column['type'] == 'INTEGER'
        assert age_column['default'] == '0'
        
        connection.disconnect()
    
    def test_get_columns_not_connected(self):
        """Test getting a list of columns when not connected."""
        connection = DatabaseConnection('sqlite:///test.db')
        
        # Get the columns
        columns = connection.get_columns('test')
        
        assert columns == []
    
    def test_get_indexes(self, temp_db_path):
        """Test getting a list of indexes for a table."""
        connection_string = f'sqlite:///{temp_db_path}'
        connection = DatabaseConnection(connection_string)
        
        # Connect to the database
        connection.connect()
        
        # Create a table
        connection.execute('CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)')
        
        # Create some indexes
        connection.execute('CREATE INDEX idx_name ON test (name)')
        connection.execute('CREATE UNIQUE INDEX idx_age ON test (age)')
        connection.commit()
        
        # Get the indexes
        indexes = connection.get_indexes('test')
        
        assert len(indexes) == 2
        
        # Check the name index
        name_index = next(idx for idx in indexes if idx['name'] == 'idx_name')
        assert name_index['columns'] == ['name']
        assert name_index['unique'] is False
        
        # Check the age index
        age_index = next(idx for idx in indexes if idx['name'] == 'idx_age')
        assert age_index['columns'] == ['age']
        assert age_index['unique'] is True
        
        connection.disconnect()
    
    def test_get_indexes_not_connected(self):
        """Test getting a list of indexes when not connected."""
        connection = DatabaseConnection('sqlite:///test.db')
        
        # Get the indexes
        indexes = connection.get_indexes('test')
        
        assert indexes == []
    
    def test_create_database_sqlite(self, temp_db_path):
        """Test creating a SQLite database."""
        connection_string = f'sqlite:///{temp_db_path}'
        connection = DatabaseConnection(connection_string)
        
        # Create the database
        assert connection.create_database('test') is True
        
        # Check if the database file was created
        assert os.path.exists(temp_db_path)
    
    @patch('psycopg2.connect')
    @patch('pythonweb_installer.database.connection.POSTGRES_AVAILABLE', True)
    def test_create_database_postgresql(self, mock_connect):
        """Test creating a PostgreSQL database."""
        # Mock the connection and cursor
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        connection_string = 'postgresql://user:pass@localhost:5432/testdb'
        connection = DatabaseConnection(connection_string)
        
        # Create the database
        assert connection.create_database('test') is True
        
        # Check that psycopg2.connect was called with the correct arguments
        mock_connect.assert_called_once_with(
            host='localhost',
            port=5432,
            user='user',
            password='pass',
            dbname='postgres'
        )
        
        # Check that the CREATE DATABASE command was executed
        mock_cursor.execute.assert_called_once_with('CREATE DATABASE test')
    
    @patch('mysql.connector.connect')
    @patch('pythonweb_installer.database.connection.MYSQL_AVAILABLE', True)
    def test_create_database_mysql(self, mock_connect):
        """Test creating a MySQL database."""
        # Mock the connection and cursor
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        connection_string = 'mysql://user:pass@localhost:3306/testdb'
        connection = DatabaseConnection(connection_string)
        
        # Create the database
        assert connection.create_database('test') is True
        
        # Check that mysql.connector.connect was called with the correct arguments
        mock_connect.assert_called_once_with(
            host='localhost',
            port=3306,
            user='user',
            password='pass'
        )
        
        # Check that the CREATE DATABASE command was executed
        mock_cursor.execute.assert_called_once_with('CREATE DATABASE test')
    
    def test_drop_database_sqlite(self, temp_db_path):
        """Test dropping a SQLite database."""
        # Create a database file
        with open(temp_db_path, 'w') as f:
            f.write('')
        
        connection_string = f'sqlite:///{temp_db_path}'
        connection = DatabaseConnection(connection_string)
        
        # Drop the database
        assert connection.drop_database('test') is True
        
        # Check if the database file was deleted
        assert not os.path.exists(temp_db_path)
    
    @patch('psycopg2.connect')
    @patch('pythonweb_installer.database.connection.POSTGRES_AVAILABLE', True)
    def test_drop_database_postgresql(self, mock_connect):
        """Test dropping a PostgreSQL database."""
        # Mock the connection and cursor
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        connection_string = 'postgresql://user:pass@localhost:5432/testdb'
        connection = DatabaseConnection(connection_string)
        
        # Drop the database
        assert connection.drop_database('test') is True
        
        # Check that psycopg2.connect was called with the correct arguments
        mock_connect.assert_called_once_with(
            host='localhost',
            port=5432,
            user='user',
            password='pass',
            dbname='postgres'
        )
        
        # Check that the DROP DATABASE command was executed
        mock_cursor.execute.assert_called_once_with('DROP DATABASE IF EXISTS test')
    
    @patch('mysql.connector.connect')
    @patch('pythonweb_installer.database.connection.MYSQL_AVAILABLE', True)
    def test_drop_database_mysql(self, mock_connect):
        """Test dropping a MySQL database."""
        # Mock the connection and cursor
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        connection_string = 'mysql://user:pass@localhost:3306/testdb'
        connection = DatabaseConnection(connection_string)
        
        # Drop the database
        assert connection.drop_database('test') is True
        
        # Check that mysql.connector.connect was called with the correct arguments
        mock_connect.assert_called_once_with(
            host='localhost',
            port=3306,
            user='user',
            password='pass'
        )
        
        # Check that the DROP DATABASE command was executed
        mock_cursor.execute.assert_called_once_with('DROP DATABASE IF EXISTS test')
    
    def test_create_connection(self, temp_db_path):
        """Test creating a database connection."""
        connection_string = f'sqlite:///{temp_db_path}'
        
        # Create a connection
        connection = create_connection(connection_string)
        
        assert connection is not None
        assert isinstance(connection, DatabaseConnection)
        assert connection.connection is not None
        assert connection.cursor is not None
        
        connection.disconnect()
    
    def test_create_connection_failure(self):
        """Test creating a database connection that fails."""
        connection_string = 'sqlite:///nonexistent/test.db'
        
        # Create a connection
        connection = create_connection(connection_string)
        
        assert connection is None
    
    def test_get_connection_string_sqlite(self):
        """Test getting a SQLite connection string."""
        connection_string = get_connection_string('sqlite', db_path='test.db')
        
        assert connection_string == 'sqlite:///test.db'
    
    def test_get_connection_string_postgresql(self):
        """Test getting a PostgreSQL connection string."""
        # With password
        connection_string = get_connection_string(
            'postgresql',
            username='user',
            password='pass',
            hostname='localhost',
            port=5432,
            database='testdb'
        )
        
        assert connection_string == 'postgresql://user:pass@localhost:5432/testdb'
        
        # Without password
        connection_string = get_connection_string(
            'postgresql',
            username='user',
            hostname='localhost',
            port=5432,
            database='testdb'
        )
        
        assert connection_string == 'postgresql://user@localhost:5432/testdb'
    
    def test_get_connection_string_mysql(self):
        """Test getting a MySQL connection string."""
        # With password
        connection_string = get_connection_string(
            'mysql',
            username='user',
            password='pass',
            hostname='localhost',
            port=3306,
            database='testdb'
        )
        
        assert connection_string == 'mysql://user:pass@localhost:3306/testdb'
        
        # Without password
        connection_string = get_connection_string(
            'mysql',
            username='user',
            hostname='localhost',
            port=3306,
            database='testdb'
        )
        
        assert connection_string == 'mysql://user@localhost:3306/testdb'
    
    def test_get_connection_string_unsupported(self):
        """Test getting a connection string for an unsupported database type."""
        with pytest.raises(ValueError):
            get_connection_string('unsupported')
    
    def test_parse_connection_string_sqlite(self):
        """Test parsing a SQLite connection string."""
        connection_string = 'sqlite:///test.db'
        params = parse_connection_string(connection_string)
        
        assert params['db_type'] == 'sqlite'
        assert params['db_path'] == 'test.db'
    
    def test_parse_connection_string_postgresql(self):
        """Test parsing a PostgreSQL connection string."""
        connection_string = 'postgresql://user:pass@localhost:5432/testdb'
        params = parse_connection_string(connection_string)
        
        assert params['db_type'] == 'postgresql'
        assert params['username'] == 'user'
        assert params['password'] == 'pass'
        assert params['hostname'] == 'localhost'
        assert params['port'] == 5432
        assert params['database'] == 'testdb'
    
    def test_parse_connection_string_mysql(self):
        """Test parsing a MySQL connection string."""
        connection_string = 'mysql://user:pass@localhost:3306/testdb'
        params = parse_connection_string(connection_string)
        
        assert params['db_type'] == 'mysql'
        assert params['username'] == 'user'
        assert params['password'] == 'pass'
        assert params['hostname'] == 'localhost'
        assert params['port'] == 3306
        assert params['database'] == 'testdb'
    
    def test_parse_connection_string_unsupported(self):
        """Test parsing a connection string for an unsupported database type."""
        connection_string = 'unsupported://localhost/testdb'
        
        with pytest.raises(ValueError):
            parse_connection_string(connection_string)
    
    def test_test_connection(self, temp_db_path):
        """Test testing a database connection."""
        connection_string = f'sqlite:///{temp_db_path}'
        
        # Test the connection
        success, message = test_connection(connection_string)
        
        assert success is True
        assert "Successfully connected" in message
    
    def test_test_connection_failure(self):
        """Test testing a database connection that fails."""
        connection_string = 'sqlite:///nonexistent/test.db'
        
        # Test the connection
        success, message = test_connection(connection_string)
        
        assert success is False
        assert "Failed to test database connection" in message
