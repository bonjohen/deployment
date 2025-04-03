"""
Database migration version tracking functionality.
"""
import os
import re
import logging
import datetime
from typing import Dict, Any, List, Tuple, Optional, Union

from pythonweb_installer.database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class VersionManager:
    """
    Database migration version manager.
    """
    
    def __init__(self, connection: DatabaseConnection):
        """
        Initialize the version manager.
        
        Args:
            connection: Database connection
        """
        self.connection = connection
        self.migrations_table = "migrations"
        self._ensure_migrations_table()
    
    def _ensure_migrations_table(self) -> bool:
        """
        Ensure the migrations table exists.
        
        Returns:
            bool: True if the table exists or was created, False otherwise
        """
        try:
            # Check if the migrations table exists
            if self.connection.table_exists(self.migrations_table):
                return True
            
            # Create the migrations table
            sql = f"""
            CREATE TABLE {self.migrations_table} (
                id INTEGER PRIMARY KEY,
                version VARCHAR(255) NOT NULL,
                name VARCHAR(255) NOT NULL,
                applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                description TEXT,
                batch INTEGER NOT NULL,
                success BOOLEAN NOT NULL DEFAULT 1
            )
            """
            
            success, _ = self.connection.execute(sql)
            
            if success:
                # Create an index on the version column
                index_sql = f"""
                CREATE UNIQUE INDEX idx_{self.migrations_table}_version
                ON {self.migrations_table} (version)
                """
                
                success, _ = self.connection.execute(index_sql)
                
                if success:
                    self.connection.commit()
                    logger.info(f"Created migrations table: {self.migrations_table}")
                    return True
                else:
                    self.connection.rollback()
                    logger.error(f"Failed to create index on migrations table: {self.migrations_table}")
                    return False
            else:
                logger.error(f"Failed to create migrations table: {self.migrations_table}")
                return False
        
        except Exception as e:
            logger.error(f"Failed to ensure migrations table: {str(e)}")
            return False
    
    def get_applied_migrations(self) -> List[Dict[str, Any]]:
        """
        Get a list of applied migrations.
        
        Returns:
            List[Dict[str, Any]]: List of applied migrations
        """
        try:
            # Get the applied migrations
            sql = f"SELECT * FROM {self.migrations_table} ORDER BY id ASC"
            
            success, results = self.connection.execute(sql)
            
            if success and results:
                return results
            
            return []
        
        except Exception as e:
            logger.error(f"Failed to get applied migrations: {str(e)}")
            return []
    
    def get_last_batch_number(self) -> int:
        """
        Get the last batch number.
        
        Returns:
            int: Last batch number
        """
        try:
            # Get the last batch number
            sql = f"SELECT MAX(batch) AS last_batch FROM {self.migrations_table}"
            
            success, results = self.connection.execute(sql)
            
            if success and results and results[0]['last_batch'] is not None:
                return results[0]['last_batch']
            
            return 0
        
        except Exception as e:
            logger.error(f"Failed to get last batch number: {str(e)}")
            return 0
    
    def get_last_migration(self) -> Optional[Dict[str, Any]]:
        """
        Get the last applied migration.
        
        Returns:
            Optional[Dict[str, Any]]: Last applied migration or None
        """
        try:
            # Get the last applied migration
            sql = f"SELECT * FROM {self.migrations_table} ORDER BY id DESC LIMIT 1"
            
            success, results = self.connection.execute(sql)
            
            if success and results:
                return results[0]
            
            return None
        
        except Exception as e:
            logger.error(f"Failed to get last migration: {str(e)}")
            return None
    
    def is_migration_applied(self, version: str) -> bool:
        """
        Check if a migration is applied.
        
        Args:
            version: Migration version
            
        Returns:
            bool: True if the migration is applied, False otherwise
        """
        try:
            # Check if the migration is applied
            sql = f"SELECT COUNT(*) AS count FROM {self.migrations_table} WHERE version = ?"
            
            success, results = self.connection.execute(sql, [version])
            
            if success and results:
                return results[0]['count'] > 0
            
            return False
        
        except Exception as e:
            logger.error(f"Failed to check if migration is applied: {str(e)}")
            return False
    
    def record_migration(self, version: str, name: str, description: Optional[str] = None,
                        batch: Optional[int] = None, success: bool = True) -> bool:
        """
        Record a migration.
        
        Args:
            version: Migration version
            name: Migration name
            description: Migration description
            batch: Migration batch number
            success: Whether the migration was successful
            
        Returns:
            bool: True if the migration was recorded, False otherwise
        """
        try:
            # Get the batch number
            if batch is None:
                batch = self.get_last_batch_number() + 1
            
            # Record the migration
            sql = f"""
            INSERT INTO {self.migrations_table}
            (version, name, description, batch, success)
            VALUES (?, ?, ?, ?, ?)
            """
            
            success, _ = self.connection.execute(sql, [version, name, description, batch, 1 if success else 0])
            
            if success:
                self.connection.commit()
                logger.info(f"Recorded migration: {version}")
                return True
            else:
                self.connection.rollback()
                logger.error(f"Failed to record migration: {version}")
                return False
        
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Failed to record migration: {str(e)}")
            return False
    
    def remove_migration(self, version: str) -> bool:
        """
        Remove a migration.
        
        Args:
            version: Migration version
            
        Returns:
            bool: True if the migration was removed, False otherwise
        """
        try:
            # Remove the migration
            sql = f"DELETE FROM {self.migrations_table} WHERE version = ?"
            
            success, _ = self.connection.execute(sql, [version])
            
            if success:
                self.connection.commit()
                logger.info(f"Removed migration: {version}")
                return True
            else:
                self.connection.rollback()
                logger.error(f"Failed to remove migration: {version}")
                return False
        
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Failed to remove migration: {str(e)}")
            return False
    
    def get_migrations_in_batch(self, batch: int) -> List[Dict[str, Any]]:
        """
        Get migrations in a batch.
        
        Args:
            batch: Batch number
            
        Returns:
            List[Dict[str, Any]]: List of migrations in the batch
        """
        try:
            # Get the migrations in the batch
            sql = f"SELECT * FROM {self.migrations_table} WHERE batch = ? ORDER BY id DESC"
            
            success, results = self.connection.execute(sql, [batch])
            
            if success and results:
                return results
            
            return []
        
        except Exception as e:
            logger.error(f"Failed to get migrations in batch: {str(e)}")
            return []
    
    def reset_migrations(self) -> bool:
        """
        Reset all migrations.
        
        Returns:
            bool: True if the migrations were reset, False otherwise
        """
        try:
            # Reset the migrations
            sql = f"DELETE FROM {self.migrations_table}"
            
            success, _ = self.connection.execute(sql)
            
            if success:
                self.connection.commit()
                logger.info("Reset all migrations")
                return True
            else:
                self.connection.rollback()
                logger.error("Failed to reset migrations")
                return False
        
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Failed to reset migrations: {str(e)}")
            return False


def create_version_manager(connection: DatabaseConnection) -> VersionManager:
    """
    Create a version manager.
    
    Args:
        connection: Database connection
        
    Returns:
        VersionManager: Version manager
    """
    return VersionManager(connection)


def generate_migration_version() -> str:
    """
    Generate a migration version.
    
    Returns:
        str: Migration version
    """
    # Generate a timestamp-based version
    now = datetime.datetime.now()
    return now.strftime("%Y%m%d%H%M%S")


def parse_migration_version(version: str) -> Optional[datetime.datetime]:
    """
    Parse a migration version.
    
    Args:
        version: Migration version
        
    Returns:
        Optional[datetime.datetime]: Parsed version or None
    """
    try:
        # Parse the version
        if re.match(r'^\d{14}$', version):
            return datetime.datetime.strptime(version, "%Y%m%d%H%M%S")
        
        return None
    
    except Exception as e:
        logger.error(f"Failed to parse migration version: {str(e)}")
        return None


def format_migration_name(name: str) -> str:
    """
    Format a migration name.
    
    Args:
        name: Migration name
        
    Returns:
        str: Formatted name
    """
    # Convert spaces to underscores
    name = re.sub(r'\s+', '_', name.strip())
    
    # Remove special characters
    name = re.sub(r'[^a-zA-Z0-9_]', '', name)
    
    # Convert to lowercase
    name = name.lower()
    
    return name
