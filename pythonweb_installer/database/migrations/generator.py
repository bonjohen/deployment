"""
Database migration script generation functionality.
"""
import os
import re
import logging
from typing import Dict, Any, List, Tuple, Optional, Union

from pythonweb_installer.database.migrations.version import (
    generate_migration_version,
    format_migration_name
)

logger = logging.getLogger(__name__)


class MigrationGenerator:
    """
    Database migration generator.
    """
    
    def __init__(self, migrations_dir: str):
        """
        Initialize the migration generator.
        
        Args:
            migrations_dir: Migrations directory
        """
        self.migrations_dir = migrations_dir
    
    def generate_migration(self, name: str, description: Optional[str] = None,
                          template: str = "default") -> Tuple[bool, str, Optional[str]]:
        """
        Generate a migration script.
        
        Args:
            name: Migration name
            description: Migration description
            template: Migration template
            
        Returns:
            Tuple[bool, str, Optional[str]]: Success status, message, and migration path
        """
        try:
            # Create the migrations directory if it doesn't exist
            os.makedirs(self.migrations_dir, exist_ok=True)
            
            # Generate the migration version
            version = generate_migration_version()
            
            # Format the migration name
            formatted_name = format_migration_name(name)
            
            # Generate the migration filename
            filename = f"{version}_{formatted_name}.py"
            
            # Generate the migration path
            migration_path = os.path.join(self.migrations_dir, filename)
            
            # Check if the migration already exists
            if os.path.exists(migration_path):
                return False, f"Migration already exists: {filename}", None
            
            # Generate the migration content
            content = self._generate_migration_content(version, name, description, template)
            
            # Write the migration file
            with open(migration_path, 'w') as f:
                f.write(content)
            
            logger.info(f"Generated migration: {filename}")
            return True, f"Generated migration: {filename}", migration_path
        
        except Exception as e:
            logger.error(f"Failed to generate migration: {str(e)}")
            return False, f"Failed to generate migration: {str(e)}", None
    
    def _generate_migration_content(self, version: str, name: str, description: Optional[str] = None,
                                   template: str = "default") -> str:
        """
        Generate migration content.
        
        Args:
            version: Migration version
            name: Migration name
            description: Migration description
            template: Migration template
            
        Returns:
            str: Migration content
        """
        # Get the template content
        template_content = self._get_template_content(template)
        
        # Replace placeholders
        content = template_content.replace("{{version}}", version)
        content = content.replace("{{name}}", name)
        content = content.replace("{{description}}", description or "")
        
        return content
    
    def _get_template_content(self, template: str) -> str:
        """
        Get template content.
        
        Args:
            template: Template name
            
        Returns:
            str: Template content
        """
        if template == "default":
            return self._get_default_template()
        elif template == "create_table":
            return self._get_create_table_template()
        elif template == "alter_table":
            return self._get_alter_table_template()
        elif template == "data_migration":
            return self._get_data_migration_template()
        else:
            return self._get_default_template()
    
    def _get_default_template(self) -> str:
        """
        Get the default template.
        
        Returns:
            str: Template content
        """
        return '''"""
Migration: {{name}}
Version: {{version}}
Description: {{description}}
"""
from typing import Dict, Any, List, Tuple, Optional

from pythonweb_installer.database.connection import DatabaseConnection


def up(connection: DatabaseConnection) -> Tuple[bool, str]:
    """
    Apply the migration.
    
    Args:
        connection: Database connection
        
    Returns:
        Tuple[bool, str]: Success status and message
    """
    try:
        # TODO: Implement the migration
        
        # Commit the transaction
        connection.commit()
        return True, "Migration applied successfully"
    
    except Exception as e:
        # Rollback the transaction
        connection.rollback()
        return False, f"Failed to apply migration: {str(e)}"


def down(connection: DatabaseConnection) -> Tuple[bool, str]:
    """
    Revert the migration.
    
    Args:
        connection: Database connection
        
    Returns:
        Tuple[bool, str]: Success status and message
    """
    try:
        # TODO: Implement the migration reversion
        
        # Commit the transaction
        connection.commit()
        return True, "Migration reverted successfully"
    
    except Exception as e:
        # Rollback the transaction
        connection.rollback()
        return False, f"Failed to revert migration: {str(e)}"
'''
    
    def _get_create_table_template(self) -> str:
        """
        Get the create table template.
        
        Returns:
            str: Template content
        """
        return '''"""
Migration: {{name}}
Version: {{version}}
Description: {{description}}
"""
from typing import Dict, Any, List, Tuple, Optional

from pythonweb_installer.database.connection import DatabaseConnection


def up(connection: DatabaseConnection) -> Tuple[bool, str]:
    """
    Apply the migration.
    
    Args:
        connection: Database connection
        
    Returns:
        Tuple[bool, str]: Success status and message
    """
    try:
        # Create the table
        sql = """
        CREATE TABLE table_name (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        success, _ = connection.execute(sql)
        
        if not success:
            connection.rollback()
            return False, "Failed to create table"
        
        # Create indexes
        index_sql = """
        CREATE INDEX idx_table_name_name ON table_name (name)
        """
        
        success, _ = connection.execute(index_sql)
        
        if not success:
            connection.rollback()
            return False, "Failed to create index"
        
        # Commit the transaction
        connection.commit()
        return True, "Table created successfully"
    
    except Exception as e:
        # Rollback the transaction
        connection.rollback()
        return False, f"Failed to create table: {str(e)}"


def down(connection: DatabaseConnection) -> Tuple[bool, str]:
    """
    Revert the migration.
    
    Args:
        connection: Database connection
        
    Returns:
        Tuple[bool, str]: Success status and message
    """
    try:
        # Drop the table
        sql = "DROP TABLE IF EXISTS table_name"
        
        success, _ = connection.execute(sql)
        
        if not success:
            connection.rollback()
            return False, "Failed to drop table"
        
        # Commit the transaction
        connection.commit()
        return True, "Table dropped successfully"
    
    except Exception as e:
        # Rollback the transaction
        connection.rollback()
        return False, f"Failed to drop table: {str(e)}"
'''
    
    def _get_alter_table_template(self) -> str:
        """
        Get the alter table template.
        
        Returns:
            str: Template content
        """
        return '''"""
Migration: {{name}}
Version: {{version}}
Description: {{description}}
"""
from typing import Dict, Any, List, Tuple, Optional

from pythonweb_installer.database.connection import DatabaseConnection


def up(connection: DatabaseConnection) -> Tuple[bool, str]:
    """
    Apply the migration.
    
    Args:
        connection: Database connection
        
    Returns:
        Tuple[bool, str]: Success status and message
    """
    try:
        # Add a column
        add_column_sql = """
        ALTER TABLE table_name ADD COLUMN new_column TEXT
        """
        
        success, _ = connection.execute(add_column_sql)
        
        if not success:
            connection.rollback()
            return False, "Failed to add column"
        
        # Create an index on the new column
        index_sql = """
        CREATE INDEX idx_table_name_new_column ON table_name (new_column)
        """
        
        success, _ = connection.execute(index_sql)
        
        if not success:
            connection.rollback()
            return False, "Failed to create index"
        
        # Commit the transaction
        connection.commit()
        return True, "Table altered successfully"
    
    except Exception as e:
        # Rollback the transaction
        connection.rollback()
        return False, f"Failed to alter table: {str(e)}"


def down(connection: DatabaseConnection) -> Tuple[bool, str]:
    """
    Revert the migration.
    
    Args:
        connection: Database connection
        
    Returns:
        Tuple[bool, str]: Success status and message
    """
    try:
        # Drop the index
        drop_index_sql = """
        DROP INDEX IF EXISTS idx_table_name_new_column
        """
        
        success, _ = connection.execute(drop_index_sql)
        
        if not success:
            connection.rollback()
            return False, "Failed to drop index"
        
        # Drop the column
        drop_column_sql = """
        ALTER TABLE table_name DROP COLUMN new_column
        """
        
        success, _ = connection.execute(drop_column_sql)
        
        if not success:
            connection.rollback()
            return False, "Failed to drop column"
        
        # Commit the transaction
        connection.commit()
        return True, "Table alteration reverted successfully"
    
    except Exception as e:
        # Rollback the transaction
        connection.rollback()
        return False, f"Failed to revert table alteration: {str(e)}"
'''
    
    def _get_data_migration_template(self) -> str:
        """
        Get the data migration template.
        
        Returns:
            str: Template content
        """
        return '''"""
Migration: {{name}}
Version: {{version}}
Description: {{description}}
"""
from typing import Dict, Any, List, Tuple, Optional

from pythonweb_installer.database.connection import DatabaseConnection


def up(connection: DatabaseConnection) -> Tuple[bool, str]:
    """
    Apply the migration.
    
    Args:
        connection: Database connection
        
    Returns:
        Tuple[bool, str]: Success status and message
    """
    try:
        # Get the data to migrate
        select_sql = """
        SELECT * FROM source_table
        """
        
        success, results = connection.execute(select_sql)
        
        if not success or not results:
            connection.rollback()
            return False, "Failed to get data to migrate"
        
        # Migrate the data
        for row in results:
            # Transform the data
            transformed_data = {
                'id': row['id'],
                'name': row['name'],
                'description': row['description'] or '',
                'status': 'active'
            }
            
            # Insert the transformed data
            insert_sql = """
            INSERT INTO target_table (id, name, description, status)
            VALUES (?, ?, ?, ?)
            """
            
            success, _ = connection.execute(
                insert_sql,
                [
                    transformed_data['id'],
                    transformed_data['name'],
                    transformed_data['description'],
                    transformed_data['status']
                ]
            )
            
            if not success:
                connection.rollback()
                return False, "Failed to insert transformed data"
        
        # Commit the transaction
        connection.commit()
        return True, "Data migrated successfully"
    
    except Exception as e:
        # Rollback the transaction
        connection.rollback()
        return False, f"Failed to migrate data: {str(e)}"


def down(connection: DatabaseConnection) -> Tuple[bool, str]:
    """
    Revert the migration.
    
    Args:
        connection: Database connection
        
    Returns:
        Tuple[bool, str]: Success status and message
    """
    try:
        # Delete the migrated data
        delete_sql = """
        DELETE FROM target_table
        """
        
        success, _ = connection.execute(delete_sql)
        
        if not success:
            connection.rollback()
            return False, "Failed to delete migrated data"
        
        # Commit the transaction
        connection.commit()
        return True, "Data migration reverted successfully"
    
    except Exception as e:
        # Rollback the transaction
        connection.rollback()
        return False, f"Failed to revert data migration: {str(e)}"
'''


def create_migration_generator(migrations_dir: str) -> MigrationGenerator:
    """
    Create a migration generator.
    
    Args:
        migrations_dir: Migrations directory
        
    Returns:
        MigrationGenerator: Migration generator
    """
    return MigrationGenerator(migrations_dir)


def generate_migration(migrations_dir: str, name: str, description: Optional[str] = None,
                      template: str = "default") -> Tuple[bool, str, Optional[str]]:
    """
    Generate a migration script.
    
    Args:
        migrations_dir: Migrations directory
        name: Migration name
        description: Migration description
        template: Migration template
        
    Returns:
        Tuple[bool, str, Optional[str]]: Success status, message, and migration path
    """
    generator = create_migration_generator(migrations_dir)
    return generator.generate_migration(name, description, template)
