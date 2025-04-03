"""
Unit tests for database migration version tracking functionality.
"""
import os
import re
import tempfile
import datetime
from unittest.mock import patch, MagicMock

import pytest

from pythonweb_installer.database.connection import DatabaseConnection
from pythonweb_installer.database.migrations.version import (
    VersionManager,
    create_version_manager,
    generate_migration_version,
    parse_migration_version,
    format_migration_name
)


class TestVersionManager:
    """Tests for version manager functionality."""

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
    def version_manager(self, db_connection):
        """Create a version manager."""
        return VersionManager(db_connection)

    def test_ensure_migrations_table(self, version_manager):
        """Test ensuring the migrations table exists."""
        # Check if the migrations table exists
        assert version_manager.connection.table_exists(version_manager.migrations_table) is True

        # Execute a query to get the table info
        success, results = version_manager.connection.execute(f"PRAGMA table_info({version_manager.migrations_table})")

        assert success is True
        assert results is not None
        assert len(results) == 7

        # Check column names
        column_names = [col['name'] for col in results]
        assert 'id' in column_names
        assert 'version' in column_names
        assert 'name' in column_names
        assert 'applied_at' in column_names
        assert 'description' in column_names
        assert 'batch' in column_names
        assert 'success' in column_names

        # Get the indexes
        success, index_results = version_manager.connection.execute(f"PRAGMA index_list({version_manager.migrations_table})")

        assert success is True
        assert index_results is not None
        assert len(index_results) == 1

        # Get the index info
        index_name = index_results[0]['name']
        success, index_info = version_manager.connection.execute(f"PRAGMA index_info({index_name})")

        assert success is True
        assert index_info is not None
        assert len(index_info) == 1
        assert index_info[0]['name'] == 'version'

    def test_get_applied_migrations_empty(self, version_manager):
        """Test getting applied migrations when there are none."""
        # Get the applied migrations
        migrations = version_manager.get_applied_migrations()

        assert migrations == []

    def test_get_last_batch_number_empty(self, version_manager):
        """Test getting the last batch number when there are no migrations."""
        # Get the last batch number
        batch = version_manager.get_last_batch_number()

        assert batch == 0

    def test_get_last_migration_empty(self, version_manager):
        """Test getting the last migration when there are no migrations."""
        # Get the last migration
        migration = version_manager.get_last_migration()

        assert migration is None

    def test_is_migration_applied_empty(self, version_manager):
        """Test checking if a migration is applied when there are no migrations."""
        # Check if a migration is applied
        applied = version_manager.is_migration_applied('20220101000000')

        assert applied is False

    def test_record_migration(self, version_manager):
        """Test recording a migration."""
        # Record a migration
        success = version_manager.record_migration('20220101000000', 'test_migration', 'Test migration', 1, True)

        assert success is True

        # Check if the migration is applied
        applied = version_manager.is_migration_applied('20220101000000')

        assert applied is True

        # Get the applied migrations
        migrations = version_manager.get_applied_migrations()

        assert len(migrations) == 1
        assert migrations[0]['version'] == '20220101000000'
        assert migrations[0]['name'] == 'test_migration'
        assert migrations[0]['description'] == 'Test migration'
        assert migrations[0]['batch'] == 1
        assert migrations[0]['success'] == 1

    def test_record_migration_auto_batch(self, version_manager):
        """Test recording a migration with automatic batch number."""
        # Record a migration
        success = version_manager.record_migration('20220101000000', 'test_migration', 'Test migration')

        assert success is True

        # Get the applied migrations
        migrations = version_manager.get_applied_migrations()

        assert len(migrations) == 1
        assert migrations[0]['batch'] == 1

        # Record another migration
        success = version_manager.record_migration('20220102000000', 'test_migration_2', 'Test migration 2')

        assert success is True

        # Get the applied migrations
        migrations = version_manager.get_applied_migrations()

        assert len(migrations) == 2
        assert migrations[1]['batch'] == 2

    def test_remove_migration(self, version_manager):
        """Test removing a migration."""
        # Record a migration
        version_manager.record_migration('20220101000000', 'test_migration', 'Test migration', 1, True)

        # Remove the migration
        success = version_manager.remove_migration('20220101000000')

        assert success is True

        # Check if the migration is applied
        applied = version_manager.is_migration_applied('20220101000000')

        assert applied is False

        # Get the applied migrations
        migrations = version_manager.get_applied_migrations()

        assert len(migrations) == 0

    def test_get_migrations_in_batch(self, version_manager):
        """Test getting migrations in a batch."""
        # Record some migrations
        version_manager.record_migration('20220101000000', 'test_migration_1', 'Test migration 1', 1, True)
        version_manager.record_migration('20220102000000', 'test_migration_2', 'Test migration 2', 1, True)
        version_manager.record_migration('20220103000000', 'test_migration_3', 'Test migration 3', 2, True)

        # Get the migrations in batch 1
        migrations = version_manager.get_migrations_in_batch(1)

        assert len(migrations) == 2
        assert migrations[0]['version'] == '20220102000000'
        assert migrations[1]['version'] == '20220101000000'

        # Get the migrations in batch 2
        migrations = version_manager.get_migrations_in_batch(2)

        assert len(migrations) == 1
        assert migrations[0]['version'] == '20220103000000'

    def test_reset_migrations(self, version_manager):
        """Test resetting all migrations."""
        # Record some migrations
        version_manager.record_migration('20220101000000', 'test_migration_1', 'Test migration 1', 1, True)
        version_manager.record_migration('20220102000000', 'test_migration_2', 'Test migration 2', 1, True)

        # Reset the migrations
        success = version_manager.reset_migrations()

        assert success is True

        # Get the applied migrations
        migrations = version_manager.get_applied_migrations()

        assert len(migrations) == 0

    def test_create_version_manager(self, db_connection):
        """Test creating a version manager."""
        # Create a version manager
        version_manager = create_version_manager(db_connection)

        assert version_manager is not None
        assert isinstance(version_manager, VersionManager)
        assert version_manager.connection is db_connection

    def test_generate_migration_version(self):
        """Test generating a migration version."""
        # Generate a migration version
        version = generate_migration_version()

        assert version is not None
        assert re.match(r'^\d{14}$', version) is not None

    def test_parse_migration_version(self):
        """Test parsing a migration version."""
        # Parse a valid migration version
        version = '20220101000000'
        parsed = parse_migration_version(version)

        assert parsed is not None
        assert isinstance(parsed, datetime.datetime)
        assert parsed.year == 2022
        assert parsed.month == 1
        assert parsed.day == 1
        assert parsed.hour == 0
        assert parsed.minute == 0
        assert parsed.second == 0

        # Parse an invalid migration version
        version = 'invalid'
        parsed = parse_migration_version(version)

        assert parsed is None

    def test_format_migration_name(self):
        """Test formatting a migration name."""
        # Format a migration name
        name = 'Create Users Table'
        formatted = format_migration_name(name)

        assert formatted == 'create_users_table'

        # Format a migration name with special characters
        name = 'Create Users & Posts Table!'
        formatted = format_migration_name(name)

        assert formatted == 'create_users__posts_table'
