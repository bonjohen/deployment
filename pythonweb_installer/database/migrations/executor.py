"""
Database migration execution functionality.
"""
import os
import re
import sys
import importlib.util
import logging
from typing import Dict, Any, List, Tuple, Optional, Union, Callable

from pythonweb_installer.database.connection import DatabaseConnection
from pythonweb_installer.database.migrations.version import (
    VersionManager,
    create_version_manager,
    parse_migration_version
)

logger = logging.getLogger(__name__)


class MigrationExecutor:
    """
    Database migration executor.
    """
    
    def __init__(self, connection: DatabaseConnection, migrations_dir: str):
        """
        Initialize the migration executor.
        
        Args:
            connection: Database connection
            migrations_dir: Migrations directory
        """
        self.connection = connection
        self.migrations_dir = migrations_dir
        self.version_manager = create_version_manager(connection)
    
    def get_available_migrations(self) -> List[Dict[str, Any]]:
        """
        Get a list of available migrations.
        
        Returns:
            List[Dict[str, Any]]: List of available migrations
        """
        try:
            # Check if the migrations directory exists
            if not os.path.exists(self.migrations_dir):
                return []
            
            # Get the migration files
            migrations = []
            
            for filename in os.listdir(self.migrations_dir):
                # Check if the file is a Python file
                if not filename.endswith('.py'):
                    continue
                
                # Check if the file is a migration file
                match = re.match(r'^(\d{14})_(.+)\.py$', filename)
                
                if not match:
                    continue
                
                # Extract the version and name
                version = match.group(1)
                name = match.group(2)
                
                # Get the migration path
                migration_path = os.path.join(self.migrations_dir, filename)
                
                # Get the migration description
                description = self._get_migration_description(migration_path)
                
                # Check if the migration is applied
                applied = self.version_manager.is_migration_applied(version)
                
                # Add the migration to the list
                migrations.append({
                    'version': version,
                    'name': name,
                    'path': migration_path,
                    'description': description,
                    'applied': applied
                })
            
            # Sort the migrations by version
            migrations.sort(key=lambda m: m['version'])
            
            return migrations
        
        except Exception as e:
            logger.error(f"Failed to get available migrations: {str(e)}")
            return []
    
    def _get_migration_description(self, migration_path: str) -> Optional[str]:
        """
        Get the migration description.
        
        Args:
            migration_path: Migration path
            
        Returns:
            Optional[str]: Migration description or None
        """
        try:
            # Read the migration file
            with open(migration_path, 'r') as f:
                content = f.read()
            
            # Extract the description
            match = re.search(r'Description:\s*(.+)', content)
            
            if match:
                return match.group(1).strip()
            
            return None
        
        except Exception as e:
            logger.error(f"Failed to get migration description: {str(e)}")
            return None
    
    def get_pending_migrations(self) -> List[Dict[str, Any]]:
        """
        Get a list of pending migrations.
        
        Returns:
            List[Dict[str, Any]]: List of pending migrations
        """
        try:
            # Get the available migrations
            migrations = self.get_available_migrations()
            
            # Filter out applied migrations
            pending_migrations = [m for m in migrations if not m['applied']]
            
            return pending_migrations
        
        except Exception as e:
            logger.error(f"Failed to get pending migrations: {str(e)}")
            return []
    
    def get_applied_migrations(self) -> List[Dict[str, Any]]:
        """
        Get a list of applied migrations.
        
        Returns:
            List[Dict[str, Any]]: List of applied migrations
        """
        try:
            # Get the applied migrations from the version manager
            applied_migrations = self.version_manager.get_applied_migrations()
            
            # Get the available migrations
            available_migrations = self.get_available_migrations()
            
            # Create a map of version to migration
            migration_map = {m['version']: m for m in available_migrations}
            
            # Add the migration path to the applied migrations
            for migration in applied_migrations:
                version = migration['version']
                
                if version in migration_map:
                    migration['path'] = migration_map[version]['path']
                else:
                    migration['path'] = None
            
            return applied_migrations
        
        except Exception as e:
            logger.error(f"Failed to get applied migrations: {str(e)}")
            return []
    
    def load_migration_module(self, migration_path: str) -> Optional[Any]:
        """
        Load a migration module.
        
        Args:
            migration_path: Migration path
            
        Returns:
            Optional[Any]: Migration module or None
        """
        try:
            # Get the module name
            module_name = os.path.basename(migration_path).replace('.py', '')
            
            # Load the module
            spec = importlib.util.spec_from_file_location(module_name, migration_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            return module
        
        except Exception as e:
            logger.error(f"Failed to load migration module: {str(e)}")
            return None
    
    def apply_migration(self, migration: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Apply a migration.
        
        Args:
            migration: Migration
            
        Returns:
            Tuple[bool, str]: Success status and message
        """
        try:
            # Check if the migration is already applied
            if migration['applied']:
                return True, f"Migration already applied: {migration['version']}"
            
            # Load the migration module
            module = self.load_migration_module(migration['path'])
            
            if not module:
                return False, f"Failed to load migration module: {migration['path']}"
            
            # Check if the module has an up function
            if not hasattr(module, 'up') or not callable(module.up):
                return False, f"Migration module does not have an up function: {migration['path']}"
            
            # Apply the migration
            success, message = module.up(self.connection)
            
            if success:
                # Record the migration
                batch = self.version_manager.get_last_batch_number() + 1
                self.version_manager.record_migration(
                    migration['version'],
                    migration['name'],
                    migration['description'],
                    batch,
                    True
                )
                
                logger.info(f"Applied migration: {migration['version']}")
                return True, f"Applied migration: {migration['version']}"
            else:
                logger.error(f"Failed to apply migration: {migration['version']} - {message}")
                return False, f"Failed to apply migration: {migration['version']} - {message}"
        
        except Exception as e:
            logger.error(f"Failed to apply migration: {str(e)}")
            return False, f"Failed to apply migration: {str(e)}"
    
    def revert_migration(self, migration: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Revert a migration.
        
        Args:
            migration: Migration
            
        Returns:
            Tuple[bool, str]: Success status and message
        """
        try:
            # Check if the migration is applied
            if not migration['applied']:
                return True, f"Migration not applied: {migration['version']}"
            
            # Load the migration module
            module = self.load_migration_module(migration['path'])
            
            if not module:
                return False, f"Failed to load migration module: {migration['path']}"
            
            # Check if the module has a down function
            if not hasattr(module, 'down') or not callable(module.down):
                return False, f"Migration module does not have a down function: {migration['path']}"
            
            # Revert the migration
            success, message = module.down(self.connection)
            
            if success:
                # Remove the migration
                self.version_manager.remove_migration(migration['version'])
                
                logger.info(f"Reverted migration: {migration['version']}")
                return True, f"Reverted migration: {migration['version']}"
            else:
                logger.error(f"Failed to revert migration: {migration['version']} - {message}")
                return False, f"Failed to revert migration: {migration['version']} - {message}"
        
        except Exception as e:
            logger.error(f"Failed to revert migration: {str(e)}")
            return False, f"Failed to revert migration: {str(e)}"
    
    def migrate(self, steps: Optional[int] = None) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """
        Apply pending migrations.
        
        Args:
            steps: Number of migrations to apply
            
        Returns:
            Tuple[bool, str, List[Dict[str, Any]]]: Success status, message, and applied migrations
        """
        try:
            # Get the pending migrations
            pending_migrations = self.get_pending_migrations()
            
            if not pending_migrations:
                return True, "No pending migrations", []
            
            # Limit the number of migrations to apply
            if steps is not None and steps > 0:
                pending_migrations = pending_migrations[:steps]
            
            # Apply the migrations
            applied_migrations = []
            batch = self.version_manager.get_last_batch_number() + 1
            
            for migration in pending_migrations:
                # Apply the migration
                success, message = self.apply_migration(migration)
                
                if success:
                    # Add the migration to the list of applied migrations
                    applied_migrations.append(migration)
                else:
                    # Return the error
                    return False, message, applied_migrations
            
            return True, f"Applied {len(applied_migrations)} migrations", applied_migrations
        
        except Exception as e:
            logger.error(f"Failed to apply migrations: {str(e)}")
            return False, f"Failed to apply migrations: {str(e)}", []
    
    def rollback(self, steps: Optional[int] = None) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """
        Rollback applied migrations.
        
        Args:
            steps: Number of batches to rollback
            
        Returns:
            Tuple[bool, str, List[Dict[str, Any]]]: Success status, message, and reverted migrations
        """
        try:
            # Get the last batch number
            last_batch = self.version_manager.get_last_batch_number()
            
            if last_batch == 0:
                return True, "No migrations to rollback", []
            
            # Determine the batches to rollback
            batches_to_rollback = [last_batch]
            
            if steps is not None and steps > 1:
                for i in range(1, steps):
                    batch = last_batch - i
                    
                    if batch > 0:
                        batches_to_rollback.append(batch)
            
            # Get the migrations to rollback
            migrations_to_rollback = []
            
            for batch in batches_to_rollback:
                batch_migrations = self.version_manager.get_migrations_in_batch(batch)
                migrations_to_rollback.extend(batch_migrations)
            
            if not migrations_to_rollback:
                return True, "No migrations to rollback", []
            
            # Get the available migrations
            available_migrations = self.get_available_migrations()
            
            # Create a map of version to migration
            migration_map = {m['version']: m for m in available_migrations}
            
            # Rollback the migrations
            reverted_migrations = []
            
            for migration in migrations_to_rollback:
                version = migration['version']
                
                # Check if the migration exists
                if version not in migration_map:
                    return False, f"Migration not found: {version}", reverted_migrations
                
                # Get the migration
                migration_to_revert = migration_map[version]
                migration_to_revert['applied'] = True
                
                # Revert the migration
                success, message = self.revert_migration(migration_to_revert)
                
                if success:
                    # Add the migration to the list of reverted migrations
                    reverted_migrations.append(migration_to_revert)
                else:
                    # Return the error
                    return False, message, reverted_migrations
            
            return True, f"Reverted {len(reverted_migrations)} migrations", reverted_migrations
        
        except Exception as e:
            logger.error(f"Failed to rollback migrations: {str(e)}")
            return False, f"Failed to rollback migrations: {str(e)}", []
    
    def reset(self) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """
        Reset all migrations.
        
        Returns:
            Tuple[bool, str, List[Dict[str, Any]]]: Success status, message, and reverted migrations
        """
        try:
            # Get the applied migrations
            applied_migrations = self.get_applied_migrations()
            
            if not applied_migrations:
                return True, "No migrations to reset", []
            
            # Get the available migrations
            available_migrations = self.get_available_migrations()
            
            # Create a map of version to migration
            migration_map = {m['version']: m for m in available_migrations}
            
            # Rollback the migrations in reverse order
            reverted_migrations = []
            
            for migration in reversed(applied_migrations):
                version = migration['version']
                
                # Check if the migration exists
                if version not in migration_map:
                    logger.warning(f"Migration not found: {version}")
                    continue
                
                # Get the migration
                migration_to_revert = migration_map[version]
                migration_to_revert['applied'] = True
                
                # Revert the migration
                success, message = self.revert_migration(migration_to_revert)
                
                if success:
                    # Add the migration to the list of reverted migrations
                    reverted_migrations.append(migration_to_revert)
                else:
                    # Return the error
                    return False, message, reverted_migrations
            
            return True, f"Reset {len(reverted_migrations)} migrations", reverted_migrations
        
        except Exception as e:
            logger.error(f"Failed to reset migrations: {str(e)}")
            return False, f"Failed to reset migrations: {str(e)}", []
    
    def refresh(self) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """
        Refresh all migrations.
        
        Returns:
            Tuple[bool, str, List[Dict[str, Any]]]: Success status, message, and applied migrations
        """
        try:
            # Reset all migrations
            reset_success, reset_message, reverted_migrations = self.reset()
            
            if not reset_success:
                return False, reset_message, []
            
            # Apply all migrations
            migrate_success, migrate_message, applied_migrations = self.migrate()
            
            if not migrate_success:
                return False, migrate_message, []
            
            return True, f"Refreshed {len(applied_migrations)} migrations", applied_migrations
        
        except Exception as e:
            logger.error(f"Failed to refresh migrations: {str(e)}")
            return False, f"Failed to refresh migrations: {str(e)}", []


def create_migration_executor(connection: DatabaseConnection, migrations_dir: str) -> MigrationExecutor:
    """
    Create a migration executor.
    
    Args:
        connection: Database connection
        migrations_dir: Migrations directory
        
    Returns:
        MigrationExecutor: Migration executor
    """
    return MigrationExecutor(connection, migrations_dir)


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
    executor = create_migration_executor(connection, migrations_dir)
    return executor.migrate(steps)


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
    executor = create_migration_executor(connection, migrations_dir)
    return executor.rollback(steps)


def reset(connection: DatabaseConnection, migrations_dir: str) -> Tuple[bool, str, List[Dict[str, Any]]]:
    """
    Reset all migrations.
    
    Args:
        connection: Database connection
        migrations_dir: Migrations directory
        
    Returns:
        Tuple[bool, str, List[Dict[str, Any]]]: Success status, message, and reverted migrations
    """
    executor = create_migration_executor(connection, migrations_dir)
    return executor.reset()


def refresh(connection: DatabaseConnection, migrations_dir: str) -> Tuple[bool, str, List[Dict[str, Any]]]:
    """
    Refresh all migrations.
    
    Args:
        connection: Database connection
        migrations_dir: Migrations directory
        
    Returns:
        Tuple[bool, str, List[Dict[str, Any]]]: Success status, message, and applied migrations
    """
    executor = create_migration_executor(connection, migrations_dir)
    return executor.refresh()
