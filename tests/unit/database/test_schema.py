"""
Unit tests for database schema management functionality.
"""
import os
import json
import yaml
import tempfile
from unittest.mock import patch, MagicMock

import pytest

from pythonweb_installer.database.connection import DatabaseConnection
from pythonweb_installer.database.schema import (
    SchemaManager,
    create_schema_manager
)


class TestSchemaManager:
    """Tests for schema management functionality."""
    
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
                        {"name": "email", "type": "TEXT", "not_null": True},
                        {"name": "created_at", "type": "TIMESTAMP", "default": "CURRENT_TIMESTAMP"}
                    ],
                    "indexes": [
                        {"name": "idx_users_email", "columns": ["email"], "unique": False}
                    ]
                },
                {
                    "name": "posts",
                    "columns": [
                        {"name": "id", "type": "INTEGER", "primary_key": True},
                        {"name": "user_id", "type": "INTEGER", "not_null": True, 
                         "foreign_key": {"table": "users", "column": "id", "on_delete": "CASCADE"}},
                        {"name": "title", "type": "TEXT", "not_null": True},
                        {"name": "content", "type": "TEXT", "not_null": True},
                        {"name": "created_at", "type": "TIMESTAMP", "default": "CURRENT_TIMESTAMP"}
                    ],
                    "indexes": [
                        {"name": "idx_posts_user_id", "columns": ["user_id"], "unique": False},
                        {"name": "idx_posts_title", "columns": ["title"], "unique": False}
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
    def temp_yaml_schema_file(self):
        """Create a temporary YAML schema file."""
        fd, path = tempfile.mkstemp(suffix='.yaml')
        os.close(fd)
        
        # Create a simple schema
        schema = {
            "tables": [
                {
                    "name": "users",
                    "columns": [
                        {"name": "id", "type": "INTEGER", "primary_key": True},
                        {"name": "username", "type": "TEXT", "not_null": True, "unique": True},
                        {"name": "email", "type": "TEXT", "not_null": True},
                        {"name": "created_at", "type": "TIMESTAMP", "default": "CURRENT_TIMESTAMP"}
                    ],
                    "indexes": [
                        {"name": "idx_users_email", "columns": ["email"], "unique": False}
                    ]
                }
            ]
        }
        
        # Write the schema to the file
        with open(path, 'w') as f:
            yaml.dump(schema, f)
        
        yield path
        
        if os.path.exists(path):
            os.remove(path)
    
    def test_create_table(self, schema_manager):
        """Test creating a table."""
        # Define a simple table
        table_name = "test_table"
        columns = [
            {"name": "id", "type": "INTEGER", "primary_key": True},
            {"name": "name", "type": "TEXT", "not_null": True},
            {"name": "age", "type": "INTEGER", "default": 0}
        ]
        
        # Create the table
        success, message = schema_manager.create_table(table_name, columns)
        
        assert success is True
        assert "created successfully" in message
        
        # Verify the table exists
        assert schema_manager.connection.table_exists(table_name) is True
        
        # Verify the columns
        columns_info = schema_manager.connection.get_columns(table_name)
        
        assert len(columns_info) == 3
        
        # Check the id column
        id_column = next(col for col in columns_info if col['name'] == 'id')
        assert id_column['type'] == 'INTEGER'
        assert id_column['primary_key'] is True
        
        # Check the name column
        name_column = next(col for col in columns_info if col['name'] == 'name')
        assert name_column['type'] == 'TEXT'
        assert name_column['nullable'] is False
        
        # Check the age column
        age_column = next(col for col in columns_info if col['name'] == 'age')
        assert age_column['type'] == 'INTEGER'
        assert age_column['default'] == '0'
    
    def test_create_table_if_exists(self, schema_manager):
        """Test creating a table that already exists."""
        # Define a simple table
        table_name = "test_table"
        columns = [
            {"name": "id", "type": "INTEGER", "primary_key": True},
            {"name": "name", "type": "TEXT", "not_null": True}
        ]
        
        # Create the table
        schema_manager.create_table(table_name, columns)
        
        # Try to create the table again
        success, message = schema_manager.create_table(table_name, columns)
        
        assert success is True
        assert "created successfully" in message
        
        # Try to create the table again without IF NOT EXISTS
        success, message = schema_manager.create_table(table_name, columns, if_not_exists=False)
        
        assert success is False
        assert "already exists" in message
    
    def test_create_index(self, schema_manager):
        """Test creating an index."""
        # Create a table first
        table_name = "test_table"
        columns = [
            {"name": "id", "type": "INTEGER", "primary_key": True},
            {"name": "name", "type": "TEXT", "not_null": True},
            {"name": "age", "type": "INTEGER", "default": 0}
        ]
        
        schema_manager.create_table(table_name, columns)
        
        # Create an index
        index_name = "idx_test_name"
        index_columns = ["name"]
        
        success, message = schema_manager.create_index(table_name, index_name, index_columns)
        
        assert success is True
        assert "created successfully" in message
        
        # Verify the index exists
        indexes = schema_manager.connection.get_indexes(table_name)
        
        assert len(indexes) == 1
        assert indexes[0]['name'] == index_name
        assert indexes[0]['columns'] == index_columns
        assert indexes[0]['unique'] is False
        
        # Create a unique index
        unique_index_name = "idx_test_age"
        unique_index_columns = ["age"]
        
        success, message = schema_manager.create_index(table_name, unique_index_name, unique_index_columns, unique=True)
        
        assert success is True
        assert "created successfully" in message
        
        # Verify the unique index exists
        indexes = schema_manager.connection.get_indexes(table_name)
        
        assert len(indexes) == 2
        
        unique_index = next(idx for idx in indexes if idx['name'] == unique_index_name)
        assert unique_index['columns'] == unique_index_columns
        assert unique_index['unique'] is True
    
    def test_drop_table(self, schema_manager):
        """Test dropping a table."""
        # Create a table first
        table_name = "test_table"
        columns = [
            {"name": "id", "type": "INTEGER", "primary_key": True},
            {"name": "name", "type": "TEXT", "not_null": True}
        ]
        
        schema_manager.create_table(table_name, columns)
        
        # Drop the table
        success, message = schema_manager.drop_table(table_name)
        
        assert success is True
        assert "dropped successfully" in message
        
        # Verify the table no longer exists
        assert schema_manager.connection.table_exists(table_name) is False
    
    def test_drop_table_not_exists(self, schema_manager):
        """Test dropping a table that doesn't exist."""
        # Drop a non-existent table
        success, message = schema_manager.drop_table("nonexistent")
        
        assert success is True
        assert "dropped successfully" in message
        
        # Drop a non-existent table without IF EXISTS
        success, message = schema_manager.drop_table("nonexistent", if_exists=False)
        
        assert success is False
        assert "does not exist" in message
    
    def test_drop_index(self, schema_manager):
        """Test dropping an index."""
        # Create a table first
        table_name = "test_table"
        columns = [
            {"name": "id", "type": "INTEGER", "primary_key": True},
            {"name": "name", "type": "TEXT", "not_null": True}
        ]
        
        schema_manager.create_table(table_name, columns)
        
        # Create an index
        index_name = "idx_test_name"
        index_columns = ["name"]
        
        schema_manager.create_index(table_name, index_name, index_columns)
        
        # Drop the index
        success, message = schema_manager.drop_index(index_name)
        
        assert success is True
        assert "dropped successfully" in message
        
        # Verify the index no longer exists
        indexes = schema_manager.connection.get_indexes(table_name)
        
        assert len(indexes) == 0
    
    def test_alter_table(self, schema_manager):
        """Test altering a table."""
        # Create a table first
        table_name = "test_table"
        columns = [
            {"name": "id", "type": "INTEGER", "primary_key": True},
            {"name": "name", "type": "TEXT", "not_null": True}
        ]
        
        schema_manager.create_table(table_name, columns)
        
        # Add a column
        alterations = [
            {
                "type": "add_column",
                "name": "age",
                "type": "INTEGER",
                "default": 0
            }
        ]
        
        success, message = schema_manager.alter_table(table_name, alterations)
        
        assert success is True
        assert "altered successfully" in message
        
        # Verify the column was added
        columns_info = schema_manager.connection.get_columns(table_name)
        
        assert len(columns_info) == 3
        
        age_column = next(col for col in columns_info if col['name'] == 'age')
        assert age_column['type'] == 'INTEGER'
        assert age_column['default'] == '0'
        
        # Rename a column
        alterations = [
            {
                "type": "rename_column",
                "old_name": "name",
                "new_name": "username"
            }
        ]
        
        success, message = schema_manager.alter_table(table_name, alterations)
        
        assert success is True
        assert "altered successfully" in message
        
        # Verify the column was renamed
        columns_info = schema_manager.connection.get_columns(table_name)
        
        assert len(columns_info) == 3
        assert any(col['name'] == 'username' for col in columns_info)
        assert not any(col['name'] == 'name' for col in columns_info)
    
    def test_alter_table_not_exists(self, schema_manager):
        """Test altering a table that doesn't exist."""
        # Alter a non-existent table
        alterations = [
            {
                "type": "add_column",
                "name": "age",
                "type": "INTEGER",
                "default": 0
            }
        ]
        
        success, message = schema_manager.alter_table("nonexistent", alterations)
        
        assert success is False
        assert "does not exist" in message
    
    def test_create_schema_from_file_json(self, schema_manager, temp_schema_file):
        """Test creating a schema from a JSON file."""
        # Create the schema
        success, message = schema_manager.create_schema_from_file(temp_schema_file)
        
        assert success is True
        assert "created successfully" in message
        
        # Verify the tables exist
        assert schema_manager.connection.table_exists("users") is True
        assert schema_manager.connection.table_exists("posts") is True
        
        # Verify the columns
        users_columns = schema_manager.connection.get_columns("users")
        
        assert len(users_columns) == 4
        assert any(col['name'] == 'id' for col in users_columns)
        assert any(col['name'] == 'username' for col in users_columns)
        assert any(col['name'] == 'email' for col in users_columns)
        assert any(col['name'] == 'created_at' for col in users_columns)
        
        # Verify the indexes
        users_indexes = schema_manager.connection.get_indexes("users")
        
        assert len(users_indexes) == 1
        assert users_indexes[0]['name'] == "idx_users_email"
        assert users_indexes[0]['columns'] == ["email"]
        assert users_indexes[0]['unique'] is False
    
    def test_create_schema_from_file_yaml(self, schema_manager, temp_yaml_schema_file):
        """Test creating a schema from a YAML file."""
        # Create the schema
        success, message = schema_manager.create_schema_from_file(temp_yaml_schema_file)
        
        assert success is True
        assert "created successfully" in message
        
        # Verify the tables exist
        assert schema_manager.connection.table_exists("users") is True
        
        # Verify the columns
        users_columns = schema_manager.connection.get_columns("users")
        
        assert len(users_columns) == 4
        assert any(col['name'] == 'id' for col in users_columns)
        assert any(col['name'] == 'username' for col in users_columns)
        assert any(col['name'] == 'email' for col in users_columns)
        assert any(col['name'] == 'created_at' for col in users_columns)
    
    def test_create_schema_from_file_not_exists(self, schema_manager):
        """Test creating a schema from a file that doesn't exist."""
        # Create the schema
        success, message = schema_manager.create_schema_from_file("nonexistent.json")
        
        assert success is False
        assert "does not exist" in message
    
    def test_create_schema_from_file_invalid_format(self, schema_manager, temp_db_path):
        """Test creating a schema from a file with an invalid format."""
        # Create a file with an invalid extension
        fd, path = tempfile.mkstemp(suffix='.txt')
        os.close(fd)
        
        try:
            # Create the schema
            with pytest.raises(ValueError):
                schema_manager.create_schema_from_file(path)
        finally:
            if os.path.exists(path):
                os.remove(path)
    
    def test_create_schema(self, schema_manager):
        """Test creating a schema."""
        # Define a simple schema
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
        
        # Create the schema
        success, message = schema_manager.create_schema(schema)
        
        assert success is True
        assert "created successfully" in message
        
        # Verify the tables exist
        assert schema_manager.connection.table_exists("users") is True
        
        # Verify the columns
        users_columns = schema_manager.connection.get_columns("users")
        
        assert len(users_columns) == 3
        assert any(col['name'] == 'id' for col in users_columns)
        assert any(col['name'] == 'username' for col in users_columns)
        assert any(col['name'] == 'email' for col in users_columns)
        
        # Verify the indexes
        users_indexes = schema_manager.connection.get_indexes("users")
        
        assert len(users_indexes) == 1
        assert users_indexes[0]['name'] == "idx_users_email"
        assert users_indexes[0]['columns'] == ["email"]
        assert users_indexes[0]['unique'] is False
    
    def test_drop_schema(self, schema_manager):
        """Test dropping a schema."""
        # Define a simple schema
        schema = {
            "tables": [
                {
                    "name": "users",
                    "columns": [
                        {"name": "id", "type": "INTEGER", "primary_key": True},
                        {"name": "username", "type": "TEXT", "not_null": True}
                    ]
                },
                {
                    "name": "posts",
                    "columns": [
                        {"name": "id", "type": "INTEGER", "primary_key": True},
                        {"name": "user_id", "type": "INTEGER", "not_null": True},
                        {"name": "title", "type": "TEXT", "not_null": True}
                    ]
                }
            ]
        }
        
        # Create the schema
        schema_manager.create_schema(schema)
        
        # Drop the schema
        success, message = schema_manager.drop_schema(schema)
        
        assert success is True
        assert "dropped successfully" in message
        
        # Verify the tables no longer exist
        assert schema_manager.connection.table_exists("users") is False
        assert schema_manager.connection.table_exists("posts") is False
    
    def test_validate_schema_valid(self, schema_manager):
        """Test validating a valid schema."""
        # Define a valid schema
        schema = {
            "tables": [
                {
                    "name": "users",
                    "columns": [
                        {"name": "id", "type": "INTEGER", "primary_key": True},
                        {"name": "username", "type": "TEXT", "not_null": True}
                    ],
                    "indexes": [
                        {"name": "idx_users_username", "columns": ["username"], "unique": True}
                    ]
                }
            ]
        }
        
        # Validate the schema
        valid, errors = schema_manager.validate_schema(schema)
        
        assert valid is True
        assert len(errors) == 0
    
    def test_validate_schema_invalid(self, schema_manager):
        """Test validating an invalid schema."""
        # Define an invalid schema (missing table name)
        schema = {
            "tables": [
                {
                    "columns": [
                        {"name": "id", "type": "INTEGER", "primary_key": True},
                        {"name": "username", "type": "TEXT", "not_null": True}
                    ]
                }
            ]
        }
        
        # Validate the schema
        valid, errors = schema_manager.validate_schema(schema)
        
        assert valid is False
        assert len(errors) > 0
        assert any("does not have a name" in error for error in errors)
        
        # Define an invalid schema (duplicate table name)
        schema = {
            "tables": [
                {
                    "name": "users",
                    "columns": [
                        {"name": "id", "type": "INTEGER", "primary_key": True}
                    ]
                },
                {
                    "name": "users",
                    "columns": [
                        {"name": "id", "type": "INTEGER", "primary_key": True}
                    ]
                }
            ]
        }
        
        # Validate the schema
        valid, errors = schema_manager.validate_schema(schema)
        
        assert valid is False
        assert len(errors) > 0
        assert any("Duplicate table name" in error for error in errors)
        
        # Define an invalid schema (missing column name)
        schema = {
            "tables": [
                {
                    "name": "users",
                    "columns": [
                        {"type": "INTEGER", "primary_key": True}
                    ]
                }
            ]
        }
        
        # Validate the schema
        valid, errors = schema_manager.validate_schema(schema)
        
        assert valid is False
        assert len(errors) > 0
        assert any("does not have a name" in error for error in errors)
        
        # Define an invalid schema (duplicate column name)
        schema = {
            "tables": [
                {
                    "name": "users",
                    "columns": [
                        {"name": "id", "type": "INTEGER", "primary_key": True},
                        {"name": "id", "type": "TEXT", "not_null": True}
                    ]
                }
            ]
        }
        
        # Validate the schema
        valid, errors = schema_manager.validate_schema(schema)
        
        assert valid is False
        assert len(errors) > 0
        assert any("Duplicate column name" in error for error in errors)
        
        # Define an invalid schema (missing column type)
        schema = {
            "tables": [
                {
                    "name": "users",
                    "columns": [
                        {"name": "id", "primary_key": True}
                    ]
                }
            ]
        }
        
        # Validate the schema
        valid, errors = schema_manager.validate_schema(schema)
        
        assert valid is False
        assert len(errors) > 0
        assert any("does not have a type" in error for error in errors)
        
        # Define an invalid schema (invalid index)
        schema = {
            "tables": [
                {
                    "name": "users",
                    "columns": [
                        {"name": "id", "type": "INTEGER", "primary_key": True}
                    ],
                    "indexes": [
                        {"columns": ["username"], "unique": True}
                    ]
                }
            ]
        }
        
        # Validate the schema
        valid, errors = schema_manager.validate_schema(schema)
        
        assert valid is False
        assert len(errors) > 0
        assert any("does not have a name" in error for error in errors)
        
        # Define an invalid schema (index with non-existent column)
        schema = {
            "tables": [
                {
                    "name": "users",
                    "columns": [
                        {"name": "id", "type": "INTEGER", "primary_key": True}
                    ],
                    "indexes": [
                        {"name": "idx_users_username", "columns": ["username"], "unique": True}
                    ]
                }
            ]
        }
        
        # Validate the schema
        valid, errors = schema_manager.validate_schema(schema)
        
        assert valid is False
        assert len(errors) > 0
        assert any("does not exist in table" in error for error in errors)
    
    def test_validate_schema_no_tables(self, schema_manager):
        """Test validating a schema with no tables."""
        # Define a schema with no tables
        schema = {
            "tables": []
        }
        
        # Validate the schema
        valid, errors = schema_manager.validate_schema(schema)
        
        assert valid is False
        assert len(errors) > 0
        assert any("does not have any tables" in error for error in errors)
    
    def test_validate_schema_no_tables_key(self, schema_manager):
        """Test validating a schema with no tables key."""
        # Define a schema with no tables key
        schema = {}
        
        # Validate the schema
        valid, errors = schema_manager.validate_schema(schema)
        
        assert valid is False
        assert len(errors) > 0
        assert any("does not have tables" in error for error in errors)
    
    def test_create_schema_manager(self, db_connection):
        """Test creating a schema manager."""
        # Create a schema manager
        schema_manager = create_schema_manager(db_connection)
        
        assert schema_manager is not None
        assert isinstance(schema_manager, SchemaManager)
        assert schema_manager.connection is db_connection
