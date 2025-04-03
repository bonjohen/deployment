"""
Unit tests for database data management functionality.
"""
import os
import csv
import json
import yaml
import tempfile
from unittest.mock import patch, MagicMock

import pytest

from pythonweb_installer.database.connection import DatabaseConnection
from pythonweb_installer.database.schema import SchemaManager
from pythonweb_installer.database.data import (
    DataManager,
    create_data_manager
)


class TestDataManager:
    """Tests for data management functionality."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database path."""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.remove(path)
    
    @pytest.fixture
    def db_connection(self, temp_db_path):
        """Create a database connection."""
        connection_string = f'sqlite:///{temp_db_path}'
        connection = DatabaseConnection(connection_string)
        connection.connect()
        yield connection
        connection.disconnect()
    
    @pytest.fixture
    def schema_manager(self, db_connection):
        """Create a schema manager."""
        return SchemaManager(db_connection)
    
    @pytest.fixture
    def data_manager(self, db_connection):
        """Create a data manager."""
        return DataManager(db_connection)
    
    @pytest.fixture
    def test_table(self, schema_manager):
        """Create a test table."""
        table_name = "test_table"
        columns = [
            {"name": "id", "type": "INTEGER", "primary_key": True},
            {"name": "name", "type": "TEXT", "not_null": True},
            {"name": "age", "type": "INTEGER", "default": 0},
            {"name": "email", "type": "TEXT"}
        ]
        
        schema_manager.create_table(table_name, columns)
        
        return table_name
    
    @pytest.fixture
    def temp_csv_file(self):
        """Create a temporary CSV file."""
        fd, path = tempfile.mkstemp(suffix='.csv')
        os.close(fd)
        
        # Create a simple CSV file
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'name', 'age', 'email'])
            writer.writerow([1, 'Alice', 30, 'alice@example.com'])
            writer.writerow([2, 'Bob', 25, 'bob@example.com'])
            writer.writerow([3, 'Charlie', 35, 'charlie@example.com'])
        
        yield path
        
        if os.path.exists(path):
            os.remove(path)
    
    @pytest.fixture
    def temp_json_file(self):
        """Create a temporary JSON file."""
        fd, path = tempfile.mkstemp(suffix='.json')
        os.close(fd)
        
        # Create a simple JSON file
        data = [
            {"id": 1, "name": "Alice", "age": 30, "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "age": 25, "email": "bob@example.com"},
            {"id": 3, "name": "Charlie", "age": 35, "email": "charlie@example.com"}
        ]
        
        with open(path, 'w') as f:
            json.dump(data, f)
        
        yield path
        
        if os.path.exists(path):
            os.remove(path)
    
    @pytest.fixture
    def temp_yaml_file(self):
        """Create a temporary YAML file."""
        fd, path = tempfile.mkstemp(suffix='.yaml')
        os.close(fd)
        
        # Create a simple YAML file
        data = [
            {"id": 1, "name": "Alice", "age": 30, "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "age": 25, "email": "bob@example.com"},
            {"id": 3, "name": "Charlie", "age": 35, "email": "charlie@example.com"}
        ]
        
        with open(path, 'w') as f:
            yaml.dump(data, f)
        
        yield path
        
        if os.path.exists(path):
            os.remove(path)
    
    @pytest.fixture
    def temp_data_dir(self, temp_csv_file, temp_json_file, temp_yaml_file):
        """Create a temporary data directory."""
        temp_dir = tempfile.mkdtemp()
        
        # Create a directory structure
        os.makedirs(os.path.join(temp_dir, 'users'), exist_ok=True)
        os.makedirs(os.path.join(temp_dir, 'posts'), exist_ok=True)
        
        # Copy the test files to the directory
        with open(os.path.join(temp_dir, 'test_table.csv'), 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'name', 'age', 'email'])
            writer.writerow([1, 'Alice', 30, 'alice@example.com'])
            writer.writerow([2, 'Bob', 25, 'bob@example.com'])
        
        with open(os.path.join(temp_dir, 'users', 'users.json'), 'w') as f:
            json.dump([
                {"id": 1, "username": "alice", "email": "alice@example.com"},
                {"id": 2, "username": "bob", "email": "bob@example.com"}
            ], f)
        
        with open(os.path.join(temp_dir, 'posts', 'posts.yaml'), 'w') as f:
            yaml.dump([
                {"id": 1, "user_id": 1, "title": "Alice's Post", "content": "Hello from Alice"},
                {"id": 2, "user_id": 2, "title": "Bob's Post", "content": "Hello from Bob"}
            ], f)
        
        yield temp_dir
        
        # Clean up
        import shutil
        shutil.rmtree(temp_dir)
    
    def test_insert_data(self, data_manager, test_table):
        """Test inserting data into a table."""
        # Define some test data
        data = [
            {"id": 1, "name": "Alice", "age": 30, "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "age": 25, "email": "bob@example.com"}
        ]
        
        # Insert the data
        success, message = data_manager.insert_data(test_table, data)
        
        assert success is True
        assert "inserted successfully" in message
        
        # Verify the data was inserted
        success, results = data_manager.connection.execute(f"SELECT * FROM {test_table}")
        
        assert success is True
        assert results is not None
        assert len(results) == 2
        
        # Check the first record
        assert results[0]['id'] == 1
        assert results[0]['name'] == 'Alice'
        assert results[0]['age'] == 30
        assert results[0]['email'] == 'alice@example.com'
        
        # Check the second record
        assert results[1]['id'] == 2
        assert results[1]['name'] == 'Bob'
        assert results[1]['age'] == 25
        assert results[1]['email'] == 'bob@example.com'
    
    def test_insert_data_empty(self, data_manager, test_table):
        """Test inserting empty data into a table."""
        # Insert empty data
        success, message = data_manager.insert_data(test_table, [])
        
        assert success is True
        assert "No data to insert" in message
        
        # Verify no data was inserted
        success, results = data_manager.connection.execute(f"SELECT * FROM {test_table}")
        
        assert success is True
        assert results is not None
        assert len(results) == 0
    
    def test_insert_data_table_not_exists(self, data_manager):
        """Test inserting data into a non-existent table."""
        # Define some test data
        data = [
            {"id": 1, "name": "Alice", "age": 30, "email": "alice@example.com"}
        ]
        
        # Insert the data
        success, message = data_manager.insert_data("nonexistent", data)
        
        assert success is False
        assert "does not exist" in message
    
    def test_update_data(self, data_manager, test_table):
        """Test updating data in a table."""
        # Insert some initial data
        initial_data = [
            {"id": 1, "name": "Alice", "age": 30, "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "age": 25, "email": "bob@example.com"}
        ]
        
        data_manager.insert_data(test_table, initial_data)
        
        # Define the update data
        update_data = [
            {"id": 1, "age": 31, "email": "alice.updated@example.com"},
            {"id": 2, "name": "Robert"}
        ]
        
        # Update the data
        success, message = data_manager.update_data(test_table, update_data, "id")
        
        assert success is True
        assert "updated successfully" in message
        
        # Verify the data was updated
        success, results = data_manager.connection.execute(f"SELECT * FROM {test_table}")
        
        assert success is True
        assert results is not None
        assert len(results) == 2
        
        # Check the first record
        assert results[0]['id'] == 1
        assert results[0]['name'] == 'Alice'  # Unchanged
        assert results[0]['age'] == 31  # Updated
        assert results[0]['email'] == 'alice.updated@example.com'  # Updated
        
        # Check the second record
        assert results[1]['id'] == 2
        assert results[1]['name'] == 'Robert'  # Updated
        assert results[1]['age'] == 25  # Unchanged
        assert results[1]['email'] == 'bob@example.com'  # Unchanged
    
    def test_update_data_empty(self, data_manager, test_table):
        """Test updating with empty data."""
        # Update with empty data
        success, message = data_manager.update_data(test_table, [], "id")
        
        assert success is True
        assert "No data to update" in message
    
    def test_update_data_table_not_exists(self, data_manager):
        """Test updating data in a non-existent table."""
        # Define some update data
        update_data = [
            {"id": 1, "name": "Alice"}
        ]
        
        # Update the data
        success, message = data_manager.update_data("nonexistent", update_data, "id")
        
        assert success is False
        assert "does not exist" in message
    
    def test_delete_data(self, data_manager, test_table):
        """Test deleting data from a table."""
        # Insert some initial data
        initial_data = [
            {"id": 1, "name": "Alice", "age": 30, "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "age": 25, "email": "bob@example.com"},
            {"id": 3, "name": "Charlie", "age": 35, "email": "charlie@example.com"}
        ]
        
        data_manager.insert_data(test_table, initial_data)
        
        # Delete data with a condition
        condition = {"id": 2}
        success, message = data_manager.delete_data(test_table, condition)
        
        assert success is True
        assert "deleted successfully" in message
        
        # Verify the data was deleted
        success, results = data_manager.connection.execute(f"SELECT * FROM {test_table}")
        
        assert success is True
        assert results is not None
        assert len(results) == 2
        
        # Check that the record with id=2 was deleted
        assert all(result['id'] != 2 for result in results)
        
        # Delete all data
        success, message = data_manager.delete_data(test_table)
        
        assert success is True
        assert "deleted successfully" in message
        
        # Verify all data was deleted
        success, results = data_manager.connection.execute(f"SELECT * FROM {test_table}")
        
        assert success is True
        assert results is not None
        assert len(results) == 0
    
    def test_delete_data_table_not_exists(self, data_manager):
        """Test deleting data from a non-existent table."""
        # Delete data
        success, message = data_manager.delete_data("nonexistent")
        
        assert success is False
        assert "does not exist" in message
    
    def test_load_data_from_file_csv(self, data_manager, test_table, temp_csv_file):
        """Test loading data from a CSV file."""
        # Load the data
        success, message = data_manager.load_data_from_file(test_table, temp_csv_file)
        
        assert success is True
        assert "inserted successfully" in message
        
        # Verify the data was loaded
        success, results = data_manager.connection.execute(f"SELECT * FROM {test_table}")
        
        assert success is True
        assert results is not None
        assert len(results) == 3
        
        # Check the first record
        assert results[0]['id'] == '1'  # CSV values are strings
        assert results[0]['name'] == 'Alice'
        assert results[0]['age'] == '30'
        assert results[0]['email'] == 'alice@example.com'
    
    def test_load_data_from_file_json(self, data_manager, test_table, temp_json_file):
        """Test loading data from a JSON file."""
        # Load the data
        success, message = data_manager.load_data_from_file(test_table, temp_json_file)
        
        assert success is True
        assert "inserted successfully" in message
        
        # Verify the data was loaded
        success, results = data_manager.connection.execute(f"SELECT * FROM {test_table}")
        
        assert success is True
        assert results is not None
        assert len(results) == 3
        
        # Check the first record
        assert results[0]['id'] == 1
        assert results[0]['name'] == 'Alice'
        assert results[0]['age'] == 30
        assert results[0]['email'] == 'alice@example.com'
    
    def test_load_data_from_file_yaml(self, data_manager, test_table, temp_yaml_file):
        """Test loading data from a YAML file."""
        # Load the data
        success, message = data_manager.load_data_from_file(test_table, temp_yaml_file)
        
        assert success is True
        assert "inserted successfully" in message
        
        # Verify the data was loaded
        success, results = data_manager.connection.execute(f"SELECT * FROM {test_table}")
        
        assert success is True
        assert results is not None
        assert len(results) == 3
        
        # Check the first record
        assert results[0]['id'] == 1
        assert results[0]['name'] == 'Alice'
        assert results[0]['age'] == 30
        assert results[0]['email'] == 'alice@example.com'
    
    def test_load_data_from_file_not_exists(self, data_manager, test_table):
        """Test loading data from a non-existent file."""
        # Load the data
        success, message = data_manager.load_data_from_file(test_table, "nonexistent.csv")
        
        assert success is False
        assert "does not exist" in message
    
    def test_load_data_from_file_invalid_format(self, data_manager, test_table):
        """Test loading data from a file with an invalid format."""
        # Create a file with an invalid extension
        fd, path = tempfile.mkstemp(suffix='.txt')
        os.close(fd)
        
        try:
            # Load the data
            with pytest.raises(ValueError):
                data_manager.load_data_from_file(test_table, path)
        finally:
            if os.path.exists(path):
                os.remove(path)
    
    def test_export_data_to_file_csv(self, data_manager, test_table):
        """Test exporting data to a CSV file."""
        # Insert some data
        data = [
            {"id": 1, "name": "Alice", "age": 30, "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "age": 25, "email": "bob@example.com"}
        ]
        
        data_manager.insert_data(test_table, data)
        
        # Create a temporary file
        fd, path = tempfile.mkstemp(suffix='.csv')
        os.close(fd)
        
        try:
            # Export the data
            success, message = data_manager.export_data_to_file(test_table, path)
            
            assert success is True
            assert "exported successfully" in message
            
            # Verify the file was created
            assert os.path.exists(path)
            
            # Verify the file contents
            with open(path, 'r', newline='') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                assert len(rows) == 2
                
                # Check the first record
                assert rows[0]['id'] == '1'
                assert rows[0]['name'] == 'Alice'
                assert rows[0]['age'] == '30'
                assert rows[0]['email'] == 'alice@example.com'
        finally:
            if os.path.exists(path):
                os.remove(path)
    
    def test_export_data_to_file_json(self, data_manager, test_table):
        """Test exporting data to a JSON file."""
        # Insert some data
        data = [
            {"id": 1, "name": "Alice", "age": 30, "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "age": 25, "email": "bob@example.com"}
        ]
        
        data_manager.insert_data(test_table, data)
        
        # Create a temporary file
        fd, path = tempfile.mkstemp(suffix='.json')
        os.close(fd)
        
        try:
            # Export the data
            success, message = data_manager.export_data_to_file(test_table, path)
            
            assert success is True
            assert "exported successfully" in message
            
            # Verify the file was created
            assert os.path.exists(path)
            
            # Verify the file contents
            with open(path, 'r') as f:
                exported_data = json.load(f)
                
                assert len(exported_data) == 2
                
                # Check the first record
                assert exported_data[0]['id'] == 1
                assert exported_data[0]['name'] == 'Alice'
                assert exported_data[0]['age'] == 30
                assert exported_data[0]['email'] == 'alice@example.com'
        finally:
            if os.path.exists(path):
                os.remove(path)
    
    def test_export_data_to_file_yaml(self, data_manager, test_table):
        """Test exporting data to a YAML file."""
        # Insert some data
        data = [
            {"id": 1, "name": "Alice", "age": 30, "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "age": 25, "email": "bob@example.com"}
        ]
        
        data_manager.insert_data(test_table, data)
        
        # Create a temporary file
        fd, path = tempfile.mkstemp(suffix='.yaml')
        os.close(fd)
        
        try:
            # Export the data
            success, message = data_manager.export_data_to_file(test_table, path)
            
            assert success is True
            assert "exported successfully" in message
            
            # Verify the file was created
            assert os.path.exists(path)
            
            # Verify the file contents
            with open(path, 'r') as f:
                exported_data = yaml.safe_load(f)
                
                assert len(exported_data) == 2
                
                # Check the first record
                assert exported_data[0]['id'] == 1
                assert exported_data[0]['name'] == 'Alice'
                assert exported_data[0]['age'] == 30
                assert exported_data[0]['email'] == 'alice@example.com'
        finally:
            if os.path.exists(path):
                os.remove(path)
    
    def test_export_data_to_file_with_condition(self, data_manager, test_table):
        """Test exporting data to a file with a condition."""
        # Insert some data
        data = [
            {"id": 1, "name": "Alice", "age": 30, "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "age": 25, "email": "bob@example.com"},
            {"id": 3, "name": "Charlie", "age": 35, "email": "charlie@example.com"}
        ]
        
        data_manager.insert_data(test_table, data)
        
        # Create a temporary file
        fd, path = tempfile.mkstemp(suffix='.json')
        os.close(fd)
        
        try:
            # Export the data with a condition
            condition = {"age": 30}
            success, message = data_manager.export_data_to_file(test_table, path, condition)
            
            assert success is True
            assert "exported successfully" in message
            
            # Verify the file was created
            assert os.path.exists(path)
            
            # Verify the file contents
            with open(path, 'r') as f:
                exported_data = json.load(f)
                
                assert len(exported_data) == 1
                
                # Check the record
                assert exported_data[0]['id'] == 1
                assert exported_data[0]['name'] == 'Alice'
                assert exported_data[0]['age'] == 30
                assert exported_data[0]['email'] == 'alice@example.com'
        finally:
            if os.path.exists(path):
                os.remove(path)
    
    def test_export_data_to_file_table_not_exists(self, data_manager):
        """Test exporting data from a non-existent table."""
        # Create a temporary file
        fd, path = tempfile.mkstemp(suffix='.csv')
        os.close(fd)
        
        try:
            # Export the data
            success, message = data_manager.export_data_to_file("nonexistent", path)
            
            assert success is False
            assert "does not exist" in message
        finally:
            if os.path.exists(path):
                os.remove(path)
    
    def test_export_data_to_file_invalid_format(self, data_manager, test_table):
        """Test exporting data to a file with an invalid format."""
        # Insert some data
        data = [
            {"id": 1, "name": "Alice", "age": 30, "email": "alice@example.com"}
        ]
        
        data_manager.insert_data(test_table, data)
        
        # Create a file with an invalid extension
        fd, path = tempfile.mkstemp(suffix='.txt')
        os.close(fd)
        
        try:
            # Export the data
            with pytest.raises(ValueError):
                data_manager.export_data_to_file(test_table, path)
        finally:
            if os.path.exists(path):
                os.remove(path)
    
    def test_validate_data_valid(self, data_manager, test_table):
        """Test validating valid data."""
        # Define some valid data
        data = [
            {"id": 1, "name": "Alice", "age": 30, "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "age": 25, "email": "bob@example.com"}
        ]
        
        # Validate the data
        valid, errors = data_manager.validate_data(test_table, data)
        
        assert valid is True
        assert len(errors) == 0
    
    def test_validate_data_invalid(self, data_manager, test_table):
        """Test validating invalid data."""
        # Define some invalid data (missing required column)
        data = [
            {"id": 1, "age": 30, "email": "alice@example.com"},  # Missing 'name'
            {"id": 2, "name": "Bob", "age": 25, "email": "bob@example.com"}
        ]
        
        # Validate the data
        valid, errors = data_manager.validate_data(test_table, data)
        
        assert valid is False
        assert len(errors) > 0
        assert any("Missing required column" in error for error in errors)
        
        # Define some invalid data (unknown column)
        data = [
            {"id": 1, "name": "Alice", "age": 30, "email": "alice@example.com", "unknown": "value"},
            {"id": 2, "name": "Bob", "age": 25, "email": "bob@example.com"}
        ]
        
        # Validate the data
        valid, errors = data_manager.validate_data(test_table, data)
        
        assert valid is False
        assert len(errors) > 0
        assert any("Unknown column" in error for error in errors)
        
        # Define some invalid data (wrong data type)
        data = [
            {"id": 1, "name": "Alice", "age": "thirty", "email": "alice@example.com"},  # Age should be an integer
            {"id": 2, "name": "Bob", "age": 25, "email": "bob@example.com"}
        ]
        
        # Validate the data
        valid, errors = data_manager.validate_data(test_table, data)
        
        assert valid is False
        assert len(errors) > 0
        assert any("should be an integer" in error for error in errors)
    
    def test_validate_data_empty(self, data_manager, test_table):
        """Test validating empty data."""
        # Validate empty data
        valid, errors = data_manager.validate_data(test_table, [])
        
        assert valid is True
        assert len(errors) == 0
    
    def test_validate_data_table_not_exists(self, data_manager):
        """Test validating data against a non-existent table."""
        # Define some data
        data = [
            {"id": 1, "name": "Alice", "age": 30, "email": "alice@example.com"}
        ]
        
        # Validate the data
        valid, errors = data_manager.validate_data("nonexistent", data)
        
        assert valid is False
        assert len(errors) > 0
        assert any("does not exist" in error for error in errors)
    
    def test_initialize_data(self, data_manager, schema_manager, temp_data_dir):
        """Test initializing data from a directory."""
        # Create the tables
        schema_manager.create_table("test_table", [
            {"name": "id", "type": "INTEGER", "primary_key": True},
            {"name": "name", "type": "TEXT", "not_null": True},
            {"name": "age", "type": "INTEGER"},
            {"name": "email", "type": "TEXT"}
        ])
        
        schema_manager.create_table("users", [
            {"name": "id", "type": "INTEGER", "primary_key": True},
            {"name": "username", "type": "TEXT", "not_null": True},
            {"name": "email", "type": "TEXT", "not_null": True}
        ])
        
        schema_manager.create_table("posts", [
            {"name": "id", "type": "INTEGER", "primary_key": True},
            {"name": "user_id", "type": "INTEGER", "not_null": True},
            {"name": "title", "type": "TEXT", "not_null": True},
            {"name": "content", "type": "TEXT", "not_null": True}
        ])
        
        # Initialize the data
        success, message = data_manager.initialize_data(temp_data_dir)
        
        assert success is True
        assert "initialized successfully" in message
        
        # Verify the data was loaded
        success, results = data_manager.connection.execute("SELECT * FROM test_table")
        
        assert success is True
        assert results is not None
        assert len(results) == 2
        
        success, results = data_manager.connection.execute("SELECT * FROM users")
        
        assert success is True
        assert results is not None
        assert len(results) == 2
        
        success, results = data_manager.connection.execute("SELECT * FROM posts")
        
        assert success is True
        assert results is not None
        assert len(results) == 2
    
    def test_initialize_data_directory_not_exists(self, data_manager):
        """Test initializing data from a non-existent directory."""
        # Initialize the data
        success, message = data_manager.initialize_data("nonexistent")
        
        assert success is False
        assert "does not exist" in message
    
    def test_initialize_data_no_files(self, data_manager):
        """Test initializing data from a directory with no data files."""
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Initialize the data
            success, message = data_manager.initialize_data(temp_dir)
            
            assert success is True
            assert "No data files found" in message
        finally:
            import shutil
            shutil.rmtree(temp_dir)
    
    def test_create_data_manager(self, db_connection):
        """Test creating a data manager."""
        # Create a data manager
        data_manager = create_data_manager(db_connection)
        
        assert data_manager is not None
        assert isinstance(data_manager, DataManager)
        assert data_manager.connection is db_connection
