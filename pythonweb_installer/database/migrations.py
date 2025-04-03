"""
Database migrations for PythonWeb Installer.

This module provides high-level functions for database migrations.
"""
import os
import logging
from typing import Dict, Any, List, Tuple, Optional, Union

from pythonweb_installer.database.connection import DatabaseConnection
from pythonweb_installer.database.migrations.version import (
    VersionManager,
    create_version_manager,
    generate_migration_version,
    parse_migration_version,
    format_migration_name
)
from pythonweb_installer.database.migrations.generator import (
    MigrationGenerator,
    create_migration_generator,
    generate_migration
)
from pythonweb_installer.database.migrations.executor import (
    MigrationExecutor,
    create_migration_executor,
    migrate as execute_migrate,
    rollback as execute_rollback,
    reset as execute_reset,
    refresh as execute_refresh
)

logger = logging.getLogger(__name__)


def init_migrations(connection: DatabaseConnection) -> Tuple[bool, str, Optional[VersionManager]]:
    """
    Initialize migrations.
    
    Args:
        connection: Database connection
        
    Returns:
        Tuple[bool, str, Optional[VersionManager]]: Success status, message, and version manager
    """
    try:
        # Create a version manager
        version_manager = create_version_manager(connection)
        
        return True, "Migrations initialized successfully", version_manager
    
    except Exception as e:
        logger.error(f"Failed to initialize migrations: {str(e)}")
        return False, f"Failed to initialize migrations: {str(e)}", None


def create_migration(migrations_dir: str, name: str, description: Optional[str] = None,
                    template: str = "default") -> Tuple[bool, str, Optional[str]]:
    """
    Create a migration.
    
    Args:
        migrations_dir: Migrations directory
        name: Migration name
        description: Migration description
        template: Migration template
        
    Returns:
        Tuple[bool, str, Optional[str]]: Success status, message, and migration path
    """
    return generate_migration(migrations_dir, name, description, template)


def get_migrations(connection: DatabaseConnection, migrations_dir: str) -> List[Dict[str, Any]]:
    """
    Get a list of migrations.
    
    Args:
        connection: Database connection
        migrations_dir: Migrations directory
        
    Returns:
        List[Dict[str, Any]]: List of migrations
    """
    try:
        # Create a migration executor
        executor = create_migration_executor(connection, migrations_dir)
        
        # Get the available migrations
        migrations = executor.get_available_migrations()
        
        return migrations
    
    except Exception as e:
        logger.error(f"Failed to get migrations: {str(e)}")
        return []


def get_pending_migrations(connection: DatabaseConnection, migrations_dir: str) -> List[Dict[str, Any]]:
    """
    Get a list of pending migrations.
    
    Args:
        connection: Database connection
        migrations_dir: Migrations directory
        
    Returns:
        List[Dict[str, Any]]: List of pending migrations
    """
    try:
        # Create a migration executor
        executor = create_migration_executor(connection, migrations_dir)
        
        # Get the pending migrations
        migrations = executor.get_pending_migrations()
        
        return migrations
    
    except Exception as e:
        logger.error(f"Failed to get pending migrations: {str(e)}")
        return []


def get_applied_migrations(connection: DatabaseConnection, migrations_dir: str) -> List[Dict[str, Any]]:
    """
    Get a list of applied migrations.
    
    Args:
        connection: Database connection
        migrations_dir: Migrations directory
        
    Returns:
        List[Dict[str, Any]]: List of applied migrations
    """
    try:
        # Create a migration executor
        executor = create_migration_executor(connection, migrations_dir)
        
        # Get the applied migrations
        migrations = executor.get_applied_migrations()
        
        return migrations
    
    except Exception as e:
        logger.error(f"Failed to get applied migrations: {str(e)}")
        return []


def migrate(connection: DatabaseConnection, migrations_dir: str,
           steps: Optional[int] = None) -> Tuple[bool, str, List[Dict[str, Any]]]:
    """
    Apply pending migrations.
    
    Args:
        connection: Database connection
        migrations_dir: Migrations directory
        steps: Number of migrations to apply
        
    Returns:
        Tuple[bool, str, List[Dict[str, Any]]]: Success status, message, and applied migrations
    """
    return execute_migrate(connection, migrations_dir, steps)


def rollback(connection: DatabaseConnection, migrations_dir: str,
            steps: Optional[int] = None) -> Tuple[bool, str, List[Dict[str, Any]]]:
    """
    Rollback applied migrations.
    
    Args:
        connection: Database connection
        migrations_dir: Migrations directory
        steps: Number of batches to rollback
        
    Returns:
        Tuple[bool, str, List[Dict[str, Any]]]: Success status, message, and reverted migrations
    """
    return execute_rollback(connection, migrations_dir, steps)


def reset(connection: DatabaseConnection, migrations_dir: str) -> Tuple[bool, str, List[Dict[str, Any]]]:
    """
    Reset all migrations.
    
    Args:
        connection: Database connection
        migrations_dir: Migrations directory
        
    Returns:
        Tuple[bool, str, List[Dict[str, Any]]]: Success status, message, and reverted migrations
    """
    return execute_reset(connection, migrations_dir)


def refresh(connection: DatabaseConnection, migrations_dir: str) -> Tuple[bool, str, List[Dict[str, Any]]]:
    """
    Refresh all migrations.
    
    Args:
        connection: Database connection
        migrations_dir: Migrations directory
        
    Returns:
        Tuple[bool, str, List[Dict[str, Any]]]: Success status, message, and applied migrations
    """
    return execute_refresh(connection, migrations_dir)


def create_migration_table(connection: DatabaseConnection) -> Tuple[bool, str]:
    """
    Create the migrations table.
    
    Args:
        connection: Database connection
        
    Returns:
        Tuple[bool, str]: Success status and message
    """
    try:
        # Create a version manager
        version_manager = create_version_manager(connection)
        
        # Check if the migrations table exists
        if version_manager._ensure_migrations_table():
            return True, "Migrations table created successfully"
        else:
            return False, "Failed to create migrations table"
    
    except Exception as e:
        logger.error(f"Failed to create migrations table: {str(e)}")
        return False, f"Failed to create migrations table: {str(e)}"
