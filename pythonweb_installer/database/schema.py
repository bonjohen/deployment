"""
Database schema creation functionality.
"""
import os
import re
import json
import yaml
import logging
from typing import Dict, Any, List, Tuple, Optional, Union, Set

from pythonweb_installer.database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class SchemaManager:
    """
    Database schema manager.
    """
    
    def __init__(self, connection: DatabaseConnection):
        """
        Initialize the schema manager.
        
        Args:
            connection: Database connection
        """
        self.connection = connection
    
    def create_table(self, table_name: str, columns: List[Dict[str, Any]], 
                     if_not_exists: bool = True) -> Tuple[bool, str]:
        """
        Create a table.
        
        Args:
            table_name: Name of the table
            columns: List of column definitions
            if_not_exists: Whether to add IF NOT EXISTS clause
            
        Returns:
            Tuple[bool, str]: Success status and message
        """
        try:
            # Check if the table already exists
            if self.connection.table_exists(table_name) and not if_not_exists:
                return False, f"Table {table_name} already exists"
            
            # Generate the SQL for the table creation
            sql = self._generate_create_table_sql(table_name, columns, if_not_exists)
            
            # Execute the SQL
            success, _ = self.connection.execute(sql)
            
            if success:
                # Commit the transaction
                self.connection.commit()
                logger.info(f"Created table {table_name}")
                return True, f"Table {table_name} created successfully"
            else:
                # Rollback the transaction
                self.connection.rollback()
                return False, f"Failed to create table {table_name}"
        
        except Exception as e:
            # Rollback the transaction
            self.connection.rollback()
            logger.error(f"Failed to create table {table_name}: {str(e)}")
            return False, f"Failed to create table {table_name}: {str(e)}"
    
    def _generate_create_table_sql(self, table_name: str, columns: List[Dict[str, Any]], 
                                  if_not_exists: bool = True) -> str:
        """
        Generate SQL for creating a table.
        
        Args:
            table_name: Name of the table
            columns: List of column definitions
            if_not_exists: Whether to add IF NOT EXISTS clause
            
        Returns:
            str: SQL statement
        """
        # Start the SQL statement
        sql = f"CREATE TABLE "
        
        # Add IF NOT EXISTS clause if requested
        if if_not_exists:
            sql += f"IF NOT EXISTS "
        
        # Add the table name
        sql += f"{table_name} (\n"
        
        # Add the columns
        column_definitions = []
        primary_keys = []
        
        for column in columns:
            column_name = column['name']
            column_type = column['type']
            
            # Start the column definition
            column_def = f"    {column_name} {column_type}"
            
            # Add NOT NULL constraint if specified
            if column.get('not_null', False):
                column_def += " NOT NULL"
            
            # Add DEFAULT value if specified
            if 'default' in column and column['default'] is not None:
                default_value = column['default']
                
                # Format the default value based on its type
                if isinstance(default_value, str):
                    default_value = f"'{default_value}'"
                elif isinstance(default_value, bool):
                    default_value = "1" if default_value else "0"
                
                column_def += f" DEFAULT {default_value}"
            
            # Add UNIQUE constraint if specified
            if column.get('unique', False):
                column_def += " UNIQUE"
            
            # Check if this is a primary key
            if column.get('primary_key', False):
                primary_keys.append(column_name)
            
            # Add the column definition to the list
            column_definitions.append(column_def)
        
        # Add primary key constraint if specified
        if primary_keys:
            primary_key_def = f"    PRIMARY KEY ({', '.join(primary_keys)})"
            column_definitions.append(primary_key_def)
        
        # Add foreign key constraints if specified
        for column in columns:
            if 'foreign_key' in column:
                foreign_key = column['foreign_key']
                column_name = column['name']
                
                foreign_table = foreign_key['table']
                foreign_column = foreign_key.get('column', 'id')
                on_delete = foreign_key.get('on_delete', 'CASCADE')
                on_update = foreign_key.get('on_update', 'CASCADE')
                
                foreign_key_def = f"    FOREIGN KEY ({column_name}) REFERENCES {foreign_table}({foreign_column})"
                
                if on_delete:
                    foreign_key_def += f" ON DELETE {on_delete}"
                
                if on_update:
                    foreign_key_def += f" ON UPDATE {on_update}"
                
                column_definitions.append(foreign_key_def)
        
        # Join the column definitions
        sql += ",\n".join(column_definitions)
        
        # Close the SQL statement
        sql += "\n);"
        
        return sql
    
    def create_index(self, table_name: str, index_name: str, columns: List[str], 
                     unique: bool = False, if_not_exists: bool = True) -> Tuple[bool, str]:
        """
        Create an index.
        
        Args:
            table_name: Name of the table
            index_name: Name of the index
            columns: List of column names
            unique: Whether the index is unique
            if_not_exists: Whether to add IF NOT EXISTS clause
            
        Returns:
            Tuple[bool, str]: Success status and message
        """
        try:
            # Generate the SQL for the index creation
            sql = self._generate_create_index_sql(table_name, index_name, columns, unique, if_not_exists)
            
            # Execute the SQL
            success, _ = self.connection.execute(sql)
            
            if success:
                # Commit the transaction
                self.connection.commit()
                logger.info(f"Created index {index_name} on table {table_name}")
                return True, f"Index {index_name} created successfully"
            else:
                # Rollback the transaction
                self.connection.rollback()
                return False, f"Failed to create index {index_name}"
        
        except Exception as e:
            # Rollback the transaction
            self.connection.rollback()
            logger.error(f"Failed to create index {index_name}: {str(e)}")
            return False, f"Failed to create index {index_name}: {str(e)}"
    
    def _generate_create_index_sql(self, table_name: str, index_name: str, columns: List[str], 
                                  unique: bool = False, if_not_exists: bool = True) -> str:
        """
        Generate SQL for creating an index.
        
        Args:
            table_name: Name of the table
            index_name: Name of the index
            columns: List of column names
            unique: Whether the index is unique
            if_not_exists: Whether to add IF NOT EXISTS clause
            
        Returns:
            str: SQL statement
        """
        # Start the SQL statement
        sql = f"CREATE "
        
        # Add UNIQUE if specified
        if unique:
            sql += "UNIQUE "
        
        # Add INDEX
        sql += "INDEX "
        
        # Add IF NOT EXISTS clause if requested
        if if_not_exists:
            sql += f"IF NOT EXISTS "
        
        # Add the index name and table
        sql += f"{index_name} ON {table_name} "
        
        # Add the columns
        sql += f"({', '.join(columns)});"
        
        return sql
    
    def drop_table(self, table_name: str, if_exists: bool = True) -> Tuple[bool, str]:
        """
        Drop a table.
        
        Args:
            table_name: Name of the table
            if_exists: Whether to add IF EXISTS clause
            
        Returns:
            Tuple[bool, str]: Success status and message
        """
        try:
            # Check if the table exists
            if not self.connection.table_exists(table_name) and not if_exists:
                return False, f"Table {table_name} does not exist"
            
            # Generate the SQL for dropping the table
            sql = f"DROP TABLE "
            
            # Add IF EXISTS clause if requested
            if if_exists:
                sql += f"IF EXISTS "
            
            # Add the table name
            sql += f"{table_name};"
            
            # Execute the SQL
            success, _ = self.connection.execute(sql)
            
            if success:
                # Commit the transaction
                self.connection.commit()
                logger.info(f"Dropped table {table_name}")
                return True, f"Table {table_name} dropped successfully"
            else:
                # Rollback the transaction
                self.connection.rollback()
                return False, f"Failed to drop table {table_name}"
        
        except Exception as e:
            # Rollback the transaction
            self.connection.rollback()
            logger.error(f"Failed to drop table {table_name}: {str(e)}")
            return False, f"Failed to drop table {table_name}: {str(e)}"
    
    def drop_index(self, index_name: str, if_exists: bool = True) -> Tuple[bool, str]:
        """
        Drop an index.
        
        Args:
            index_name: Name of the index
            if_exists: Whether to add IF EXISTS clause
            
        Returns:
            Tuple[bool, str]: Success status and message
        """
        try:
            # Generate the SQL for dropping the index
            sql = f"DROP INDEX "
            
            # Add IF EXISTS clause if requested
            if if_exists:
                sql += f"IF EXISTS "
            
            # Add the index name
            sql += f"{index_name};"
            
            # Execute the SQL
            success, _ = self.connection.execute(sql)
            
            if success:
                # Commit the transaction
                self.connection.commit()
                logger.info(f"Dropped index {index_name}")
                return True, f"Index {index_name} dropped successfully"
            else:
                # Rollback the transaction
                self.connection.rollback()
                return False, f"Failed to drop index {index_name}"
        
        except Exception as e:
            # Rollback the transaction
            self.connection.rollback()
            logger.error(f"Failed to drop index {index_name}: {str(e)}")
            return False, f"Failed to drop index {index_name}: {str(e)}"
    
    def alter_table(self, table_name: str, alterations: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """
        Alter a table.
        
        Args:
            table_name: Name of the table
            alterations: List of alterations
            
        Returns:
            Tuple[bool, str]: Success status and message
        """
        try:
            # Check if the table exists
            if not self.connection.table_exists(table_name):
                return False, f"Table {table_name} does not exist"
            
            # Execute each alteration
            for alteration in alterations:
                # Generate the SQL for the alteration
                sql = self._generate_alter_table_sql(table_name, alteration)
                
                # Execute the SQL
                success, _ = self.connection.execute(sql)
                
                if not success:
                    # Rollback the transaction
                    self.connection.rollback()
                    return False, f"Failed to alter table {table_name}"
            
            # Commit the transaction
            self.connection.commit()
            logger.info(f"Altered table {table_name}")
            return True, f"Table {table_name} altered successfully"
        
        except Exception as e:
            # Rollback the transaction
            self.connection.rollback()
            logger.error(f"Failed to alter table {table_name}: {str(e)}")
            return False, f"Failed to alter table {table_name}: {str(e)}"
    
    def _generate_alter_table_sql(self, table_name: str, alteration: Dict[str, Any]) -> str:
        """
        Generate SQL for altering a table.
        
        Args:
            table_name: Name of the table
            alteration: Alteration definition
            
        Returns:
            str: SQL statement
            
        Raises:
            ValueError: If the alteration type is not supported
        """
        # Get the alteration type
        alteration_type = alteration.get('type')
        
        if alteration_type == 'add_column':
            # Add a column
            column_name = alteration.get('name')
            column_type = alteration.get('type')
            
            # Start the SQL statement
            sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
            
            # Add NOT NULL constraint if specified
            if alteration.get('not_null', False):
                sql += " NOT NULL"
            
            # Add DEFAULT value if specified
            if 'default' in alteration and alteration['default'] is not None:
                default_value = alteration['default']
                
                # Format the default value based on its type
                if isinstance(default_value, str):
                    default_value = f"'{default_value}'"
                elif isinstance(default_value, bool):
                    default_value = "1" if default_value else "0"
                
                sql += f" DEFAULT {default_value}"
            
            # Add UNIQUE constraint if specified
            if alteration.get('unique', False):
                sql += " UNIQUE"
            
            # Close the SQL statement
            sql += ";"
            
            return sql
        
        elif alteration_type == 'drop_column':
            # Drop a column
            column_name = alteration.get('name')
            
            # Generate the SQL
            sql = f"ALTER TABLE {table_name} DROP COLUMN {column_name};"
            
            return sql
        
        elif alteration_type == 'rename_column':
            # Rename a column
            old_name = alteration.get('old_name')
            new_name = alteration.get('new_name')
            
            # Generate the SQL
            sql = f"ALTER TABLE {table_name} RENAME COLUMN {old_name} TO {new_name};"
            
            return sql
        
        elif alteration_type == 'rename_table':
            # Rename a table
            new_name = alteration.get('new_name')
            
            # Generate the SQL
            sql = f"ALTER TABLE {table_name} RENAME TO {new_name};"
            
            return sql
        
        else:
            raise ValueError(f"Unsupported alteration type: {alteration_type}")
    
    def create_schema_from_file(self, schema_file: str) -> Tuple[bool, str]:
        """
        Create a database schema from a file.
        
        Args:
            schema_file: Path to the schema file (JSON or YAML)
            
        Returns:
            Tuple[bool, str]: Success status and message
        """
        try:
            # Check if the schema file exists
            if not os.path.exists(schema_file):
                return False, f"Schema file {schema_file} does not exist"
            
            # Load the schema from the file
            schema = self._load_schema_from_file(schema_file)
            
            # Create the schema
            return self.create_schema(schema)
        
        except Exception as e:
            logger.error(f"Failed to create schema from file {schema_file}: {str(e)}")
            return False, f"Failed to create schema from file {schema_file}: {str(e)}"
    
    def _load_schema_from_file(self, schema_file: str) -> Dict[str, Any]:
        """
        Load a schema from a file.
        
        Args:
            schema_file: Path to the schema file (JSON or YAML)
            
        Returns:
            Dict[str, Any]: Schema definition
            
        Raises:
            ValueError: If the file format is not supported
        """
        # Get the file extension
        _, ext = os.path.splitext(schema_file)
        
        # Load the schema based on the file extension
        if ext.lower() in ['.json']:
            # Load JSON file
            with open(schema_file, 'r') as f:
                return json.load(f)
        
        elif ext.lower() in ['.yaml', '.yml']:
            # Load YAML file
            with open(schema_file, 'r') as f:
                return yaml.safe_load(f)
        
        else:
            raise ValueError(f"Unsupported schema file format: {ext}")
    
    def create_schema(self, schema: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Create a database schema.
        
        Args:
            schema: Schema definition
            
        Returns:
            Tuple[bool, str]: Success status and message
        """
        try:
            # Get the tables from the schema
            tables = schema.get('tables', [])
            
            # Create each table
            for table in tables:
                table_name = table.get('name')
                columns = table.get('columns', [])
                
                # Create the table
                success, message = self.create_table(table_name, columns)
                
                if not success:
                    return False, message
                
                # Create indexes for the table
                indexes = table.get('indexes', [])
                
                for index in indexes:
                    index_name = index.get('name')
                    index_columns = index.get('columns', [])
                    unique = index.get('unique', False)
                    
                    # Create the index
                    success, message = self.create_index(table_name, index_name, index_columns, unique)
                    
                    if not success:
                        return False, message
            
            logger.info("Created database schema")
            return True, "Database schema created successfully"
        
        except Exception as e:
            logger.error(f"Failed to create schema: {str(e)}")
            return False, f"Failed to create schema: {str(e)}"
    
    def drop_schema(self, schema: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Drop a database schema.
        
        Args:
            schema: Schema definition
            
        Returns:
            Tuple[bool, str]: Success status and message
        """
        try:
            # Get the tables from the schema
            tables = schema.get('tables', [])
            
            # Drop each table in reverse order to handle dependencies
            for table in reversed(tables):
                table_name = table.get('name')
                
                # Drop the table
                success, message = self.drop_table(table_name)
                
                if not success:
                    return False, message
            
            logger.info("Dropped database schema")
            return True, "Database schema dropped successfully"
        
        except Exception as e:
            logger.error(f"Failed to drop schema: {str(e)}")
            return False, f"Failed to drop schema: {str(e)}"
    
    def validate_schema(self, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate a database schema.
        
        Args:
            schema: Schema definition
            
        Returns:
            Tuple[bool, List[str]]: Validation status and list of errors
        """
        errors = []
        
        try:
            # Check if the schema has tables
            if 'tables' not in schema:
                errors.append("Schema does not have tables")
                return False, errors
            
            # Get the tables from the schema
            tables = schema.get('tables', [])
            
            # Check if there are any tables
            if not tables:
                errors.append("Schema does not have any tables")
                return False, errors
            
            # Validate each table
            table_names = set()
            
            for table in tables:
                # Check if the table has a name
                if 'name' not in table:
                    errors.append("Table does not have a name")
                    continue
                
                table_name = table.get('name')
                
                # Check if the table name is unique
                if table_name in table_names:
                    errors.append(f"Duplicate table name: {table_name}")
                    continue
                
                table_names.add(table_name)
                
                # Check if the table has columns
                if 'columns' not in table:
                    errors.append(f"Table {table_name} does not have columns")
                    continue
                
                columns = table.get('columns', [])
                
                # Check if there are any columns
                if not columns:
                    errors.append(f"Table {table_name} does not have any columns")
                    continue
                
                # Validate each column
                column_names = set()
                
                for column in columns:
                    # Check if the column has a name
                    if 'name' not in column:
                        errors.append(f"Column in table {table_name} does not have a name")
                        continue
                    
                    column_name = column.get('name')
                    
                    # Check if the column name is unique
                    if column_name in column_names:
                        errors.append(f"Duplicate column name in table {table_name}: {column_name}")
                        continue
                    
                    column_names.add(column_name)
                    
                    # Check if the column has a type
                    if 'type' not in column:
                        errors.append(f"Column {column_name} in table {table_name} does not have a type")
                        continue
                
                # Validate each index
                indexes = table.get('indexes', [])
                index_names = set()
                
                for index in indexes:
                    # Check if the index has a name
                    if 'name' not in index:
                        errors.append(f"Index in table {table_name} does not have a name")
                        continue
                    
                    index_name = index.get('name')
                    
                    # Check if the index name is unique
                    if index_name in index_names:
                        errors.append(f"Duplicate index name in table {table_name}: {index_name}")
                        continue
                    
                    index_names.add(index_name)
                    
                    # Check if the index has columns
                    if 'columns' not in index:
                        errors.append(f"Index {index_name} in table {table_name} does not have columns")
                        continue
                    
                    index_columns = index.get('columns', [])
                    
                    # Check if there are any columns
                    if not index_columns:
                        errors.append(f"Index {index_name} in table {table_name} does not have any columns")
                        continue
                    
                    # Check if all columns exist in the table
                    for index_column in index_columns:
                        if index_column not in column_names:
                            errors.append(f"Column {index_column} in index {index_name} does not exist in table {table_name}")
            
            # Return the validation result
            return len(errors) == 0, errors
        
        except Exception as e:
            errors.append(f"Failed to validate schema: {str(e)}")
            return False, errors


def create_schema_manager(connection: DatabaseConnection) -> SchemaManager:
    """
    Create a schema manager.
    
    Args:
        connection: Database connection
        
    Returns:
        SchemaManager: Schema manager
    """
    return SchemaManager(connection)
