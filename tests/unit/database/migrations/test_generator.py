"""
Unit tests for database migration generator functionality.
"""
import os
import re
import tempfile
from unittest.mock import patch, MagicMock

import pytest

from pythonweb_installer.database.migrations.generator import (
    MigrationGenerator,
    create_migration_generator,
    generate_migration
)


class TestMigrationGenerator:
    """Tests for migration generator functionality."""
    
    @pytest.fixture
    def temp_migrations_dir(self):
        """Create a temporary migrations directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        
        # Clean up
        import shutil
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def migration_generator(self, temp_migrations_dir):
        """Create a migration generator."""
        return MigrationGenerator(temp_migrations_dir)
    
    def test_generate_migration(self, migration_generator):
        """Test generating a migration."""
        # Generate a migration
        success, message, migration_path = migration_generator.generate_migration(
            'Create Users Table',
            'Create the users table'
        )
        
        assert success is True
        assert "Generated migration" in message
        assert migration_path is not None
        assert os.path.exists(migration_path)
        
        # Check the migration file
        with open(migration_path, 'r') as f:
            content = f.read()
        
        assert "Migration: Create Users Table" in content
        assert "Version: " in content
        assert "Description: Create the users table" in content
        assert "def up(connection: DatabaseConnection)" in content
        assert "def down(connection: DatabaseConnection)" in content
    
    def test_generate_migration_existing(self, migration_generator):
        """Test generating a migration that already exists."""
        # Generate a migration
        success, message, migration_path = migration_generator.generate_migration(
            'Create Users Table',
            'Create the users table'
        )
        
        assert success is True
        
        # Generate the same migration again
        with patch('pythonweb_installer.database.migrations.version.generate_migration_version') as mock_generate:
            # Mock the version to be the same as the first migration
            version = os.path.basename(migration_path).split('_')[0]
            mock_generate.return_value = version
            
            success, message, migration_path = migration_generator.generate_migration(
                'Create Users Table',
                'Create the users table'
            )
            
            assert success is False
            assert "already exists" in message
            assert migration_path is None
    
    def test_generate_migration_create_table_template(self, migration_generator):
        """Test generating a migration with the create table template."""
        # Generate a migration
        success, message, migration_path = migration_generator.generate_migration(
            'Create Users Table',
            'Create the users table',
            'create_table'
        )
        
        assert success is True
        assert "Generated migration" in message
        assert migration_path is not None
        assert os.path.exists(migration_path)
        
        # Check the migration file
        with open(migration_path, 'r') as f:
            content = f.read()
        
        assert "CREATE TABLE table_name" in content
        assert "CREATE INDEX idx_table_name_name" in content
        assert "DROP TABLE IF EXISTS table_name" in content
    
    def test_generate_migration_alter_table_template(self, migration_generator):
        """Test generating a migration with the alter table template."""
        # Generate a migration
        success, message, migration_path = migration_generator.generate_migration(
            'Add Email To Users',
            'Add email column to users table',
            'alter_table'
        )
        
        assert success is True
        assert "Generated migration" in message
        assert migration_path is not None
        assert os.path.exists(migration_path)
        
        # Check the migration file
        with open(migration_path, 'r') as f:
            content = f.read()
        
        assert "ALTER TABLE table_name ADD COLUMN new_column" in content
        assert "CREATE INDEX idx_table_name_new_column" in content
        assert "DROP INDEX IF EXISTS idx_table_name_new_column" in content
        assert "ALTER TABLE table_name DROP COLUMN new_column" in content
    
    def test_generate_migration_data_migration_template(self, migration_generator):
        """Test generating a migration with the data migration template."""
        # Generate a migration
        success, message, migration_path = migration_generator.generate_migration(
            'Migrate User Data',
            'Migrate user data to new format',
            'data_migration'
        )
        
        assert success is True
        assert "Generated migration" in message
        assert migration_path is not None
        assert os.path.exists(migration_path)
        
        # Check the migration file
        with open(migration_path, 'r') as f:
            content = f.read()
        
        assert "SELECT * FROM source_table" in content
        assert "INSERT INTO target_table" in content
        assert "DELETE FROM target_table" in content
    
    def test_create_migration_generator(self, temp_migrations_dir):
        """Test creating a migration generator."""
        # Create a migration generator
        generator = create_migration_generator(temp_migrations_dir)
        
        assert generator is not None
        assert isinstance(generator, MigrationGenerator)
        assert generator.migrations_dir == temp_migrations_dir
    
    def test_generate_migration_function(self, temp_migrations_dir):
        """Test the generate_migration function."""
        # Generate a migration
        success, message, migration_path = generate_migration(
            temp_migrations_dir,
            'Create Users Table',
            'Create the users table'
        )
        
        assert success is True
        assert "Generated migration" in message
        assert migration_path is not None
        assert os.path.exists(migration_path)
        
        # Check the migration file
        with open(migration_path, 'r') as f:
            content = f.read()
        
        assert "Migration: Create Users Table" in content
        assert "Version: " in content
        assert "Description: Create the users table" in content
