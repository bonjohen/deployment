"""
Database data initialization functionality.
"""
import os
import csv
import json
import yaml
import logging
from typing import Dict, Any, List, Tuple, Optional, Union, Set

from pythonweb_installer.database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class DataManager:
    """
    Database data manager.
    """
    
    def __init__(self, connection: DatabaseConnection):
        """
        Initialize the data manager.
        
        Args:
            connection: Database connection
        """
        self.connection = connection
    
    def insert_data(self, table_name: str, data: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """
        Insert data into a table.
        
        Args:
            table_name: Name of the table
            data: List of data records
            
        Returns:
            Tuple[bool, str]: Success status and message
        """
        try:
            # Check if the table exists
            if not self.connection.table_exists(table_name):
                return False, f"Table {table_name} does not exist"
            
            # Check if there is any data to insert
            if not data:
                return True, "No data to insert"
            
            # Get the columns from the first record
            columns = list(data[0].keys())
            
            # Generate the SQL for the insertion
            placeholders = ", ".join(["?"] * len(columns))
            column_names = ", ".join(columns)
            
            sql = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"
            
            # Insert each record
            for record in data:
                # Extract the values in the same order as the columns
                values = [record.get(column) for column in columns]
                
                # Execute the SQL
                success, _ = self.connection.execute(sql, values)
                
                if not success:
                    # Rollback the transaction
                    self.connection.rollback()
                    return False, f"Failed to insert data into table {table_name}"
            
            # Commit the transaction
            self.connection.commit()
            logger.info(f"Inserted {len(data)} records into table {table_name}")
            return True, f"Data inserted successfully into table {table_name}"
        
        except Exception as e:
            # Rollback the transaction
            self.connection.rollback()
            logger.error(f"Failed to insert data into table {table_name}: {str(e)}")
            return False, f"Failed to insert data into table {table_name}: {str(e)}"
    
    def update_data(self, table_name: str, data: List[Dict[str, Any]], 
                   key_column: str) -> Tuple[bool, str]:
        """
        Update data in a table.
        
        Args:
            table_name: Name of the table
            data: List of data records
            key_column: Name of the column to use as the key
            
        Returns:
            Tuple[bool, str]: Success status and message
        """
        try:
            # Check if the table exists
            if not self.connection.table_exists(table_name):
                return False, f"Table {table_name} does not exist"
            
            # Check if there is any data to update
            if not data:
                return True, "No data to update"
            
            # Update each record
            for record in data:
                # Check if the key column exists in the record
                if key_column not in record:
                    logger.warning(f"Key column {key_column} not found in record, skipping")
                    continue
                
                # Get the key value
                key_value = record[key_column]
                
                # Remove the key column from the record
                update_data = {k: v for k, v in record.items() if k != key_column}
                
                # Check if there is any data to update
                if not update_data:
                    logger.warning(f"No data to update for key {key_value}, skipping")
                    continue
                
                # Generate the SQL for the update
                set_clause = ", ".join([f"{column} = ?" for column in update_data.keys()])
                
                sql = f"UPDATE {table_name} SET {set_clause} WHERE {key_column} = ?"
                
                # Extract the values
                values = list(update_data.values()) + [key_value]
                
                # Execute the SQL
                success, _ = self.connection.execute(sql, values)
                
                if not success:
                    # Rollback the transaction
                    self.connection.rollback()
                    return False, f"Failed to update data in table {table_name}"
            
            # Commit the transaction
            self.connection.commit()
            logger.info(f"Updated {len(data)} records in table {table_name}")
            return True, f"Data updated successfully in table {table_name}"
        
        except Exception as e:
            # Rollback the transaction
            self.connection.rollback()
            logger.error(f"Failed to update data in table {table_name}: {str(e)}")
            return False, f"Failed to update data in table {table_name}: {str(e)}"
    
    def delete_data(self, table_name: str, condition: Optional[Dict[str, Any]] = None) -> Tuple[bool, str]:
        """
        Delete data from a table.
        
        Args:
            table_name: Name of the table
            condition: Condition for deletion (column-value pairs)
            
        Returns:
            Tuple[bool, str]: Success status and message
        """
        try:
            # Check if the table exists
            if not self.connection.table_exists(table_name):
                return False, f"Table {table_name} does not exist"
            
            # Generate the SQL for the deletion
            sql = f"DELETE FROM {table_name}"
            
            # Add the condition if specified
            values = []
            
            if condition:
                where_clause = " AND ".join([f"{column} = ?" for column in condition.keys()])
                sql += f" WHERE {where_clause}"
                values = list(condition.values())
            
            # Execute the SQL
            success, _ = self.connection.execute(sql, values)
            
            if success:
                # Commit the transaction
                self.connection.commit()
                logger.info(f"Deleted data from table {table_name}")
                return True, f"Data deleted successfully from table {table_name}"
            else:
                # Rollback the transaction
                self.connection.rollback()
                return False, f"Failed to delete data from table {table_name}"
        
        except Exception as e:
            # Rollback the transaction
            self.connection.rollback()
            logger.error(f"Failed to delete data from table {table_name}: {str(e)}")
            return False, f"Failed to delete data from table {table_name}: {str(e)}"
    
    def load_data_from_file(self, table_name: str, data_file: str) -> Tuple[bool, str]:
        """
        Load data from a file into a table.
        
        Args:
            table_name: Name of the table
            data_file: Path to the data file (CSV, JSON, or YAML)
            
        Returns:
            Tuple[bool, str]: Success status and message
        """
        try:
            # Check if the data file exists
            if not os.path.exists(data_file):
                return False, f"Data file {data_file} does not exist"
            
            # Load the data from the file
            data = self._load_data_from_file(data_file)
            
            # Insert the data into the table
            return self.insert_data(table_name, data)
        
        except Exception as e:
            logger.error(f"Failed to load data from file {data_file}: {str(e)}")
            return False, f"Failed to load data from file {data_file}: {str(e)}"
    
    def _load_data_from_file(self, data_file: str) -> List[Dict[str, Any]]:
        """
        Load data from a file.
        
        Args:
            data_file: Path to the data file (CSV, JSON, or YAML)
            
        Returns:
            List[Dict[str, Any]]: List of data records
            
        Raises:
            ValueError: If the file format is not supported
        """
        # Get the file extension
        _, ext = os.path.splitext(data_file)
        
        # Load the data based on the file extension
        if ext.lower() == '.csv':
            # Load CSV file
            with open(data_file, 'r', newline='') as f:
                reader = csv.DictReader(f)
                return list(reader)
        
        elif ext.lower() == '.json':
            # Load JSON file
            with open(data_file, 'r') as f:
                data = json.load(f)
                
                # Check if the data is a list
                if isinstance(data, list):
                    return data
                else:
                    # Wrap the data in a list
                    return [data]
        
        elif ext.lower() in ['.yaml', '.yml']:
            # Load YAML file
            with open(data_file, 'r') as f:
                data = yaml.safe_load(f)
                
                # Check if the data is a list
                if isinstance(data, list):
                    return data
                else:
                    # Wrap the data in a list
                    return [data]
        
        else:
            raise ValueError(f"Unsupported data file format: {ext}")
    
    def export_data_to_file(self, table_name: str, data_file: str, 
                           condition: Optional[Dict[str, Any]] = None) -> Tuple[bool, str]:
        """
        Export data from a table to a file.
        
        Args:
            table_name: Name of the table
            data_file: Path to the data file (CSV, JSON, or YAML)
            condition: Condition for selection (column-value pairs)
            
        Returns:
            Tuple[bool, str]: Success status and message
        """
        try:
            # Check if the table exists
            if not self.connection.table_exists(table_name):
                return False, f"Table {table_name} does not exist"
            
            # Generate the SQL for the selection
            sql = f"SELECT * FROM {table_name}"
            
            # Add the condition if specified
            values = []
            
            if condition:
                where_clause = " AND ".join([f"{column} = ?" for column in condition.keys()])
                sql += f" WHERE {where_clause}"
                values = list(condition.values())
            
            # Execute the SQL
            success, results = self.connection.execute(sql, values)
            
            if not success or not results:
                return False, f"Failed to export data from table {table_name}"
            
            # Export the data to the file
            self._export_data_to_file(results, data_file)
            
            logger.info(f"Exported {len(results)} records from table {table_name} to {data_file}")
            return True, f"Data exported successfully from table {table_name} to {data_file}"
        
        except Exception as e:
            logger.error(f"Failed to export data from table {table_name}: {str(e)}")
            return False, f"Failed to export data from table {table_name}: {str(e)}"
    
    def _export_data_to_file(self, data: List[Dict[str, Any]], data_file: str) -> None:
        """
        Export data to a file.
        
        Args:
            data: List of data records
            data_file: Path to the data file (CSV, JSON, or YAML)
            
        Raises:
            ValueError: If the file format is not supported
        """
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(data_file)), exist_ok=True)
        
        # Get the file extension
        _, ext = os.path.splitext(data_file)
        
        # Export the data based on the file extension
        if ext.lower() == '.csv':
            # Export to CSV file
            with open(data_file, 'w', newline='') as f:
                if data:
                    writer = csv.DictWriter(f, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
        
        elif ext.lower() == '.json':
            # Export to JSON file
            with open(data_file, 'w') as f:
                json.dump(data, f, indent=2)
        
        elif ext.lower() in ['.yaml', '.yml']:
            # Export to YAML file
            with open(data_file, 'w') as f:
                yaml.dump(data, f)
        
        else:
            raise ValueError(f"Unsupported data file format: {ext}")
    
    def validate_data(self, table_name: str, data: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """
        Validate data against a table schema.
        
        Args:
            table_name: Name of the table
            data: List of data records
            
        Returns:
            Tuple[bool, List[str]]: Validation status and list of errors
        """
        errors = []
        
        try:
            # Check if the table exists
            if not self.connection.table_exists(table_name):
                errors.append(f"Table {table_name} does not exist")
                return False, errors
            
            # Check if there is any data to validate
            if not data:
                return True, errors
            
            # Get the table columns
            columns = self.connection.get_columns(table_name)
            
            # Create a map of column names to column info
            column_map = {column['name']: column for column in columns}
            
            # Validate each record
            for i, record in enumerate(data):
                # Check if all required columns are present
                for column_name, column_info in column_map.items():
                    if not column_info['nullable'] and column_name not in record:
                        errors.append(f"Record {i}: Missing required column {column_name}")
                
                # Check if all columns in the record exist in the table
                for column_name in record.keys():
                    if column_name not in column_map:
                        errors.append(f"Record {i}: Unknown column {column_name}")
                
                # Validate the data types
                for column_name, value in record.items():
                    if column_name in column_map:
                        column_info = column_map[column_name]
                        column_type = column_info['type'].lower()
                        
                        # Skip NULL values for nullable columns
                        if value is None and column_info['nullable']:
                            continue
                        
                        # Validate the data type
                        if 'int' in column_type and not isinstance(value, (int, str)) and not (isinstance(value, str) and value.isdigit()):
                            errors.append(f"Record {i}: Column {column_name} should be an integer, got {type(value).__name__}")
                        
                        elif 'float' in column_type or 'real' in column_type or 'double' in column_type:
                            try:
                                float(value)
                            except (ValueError, TypeError):
                                errors.append(f"Record {i}: Column {column_name} should be a float, got {type(value).__name__}")
                        
                        elif 'bool' in column_type and not isinstance(value, (bool, int, str)):
                            errors.append(f"Record {i}: Column {column_name} should be a boolean, got {type(value).__name__}")
                        
                        elif 'char' in column_type or 'text' in column_type or 'varchar' in column_type:
                            if not isinstance(value, str):
                                errors.append(f"Record {i}: Column {column_name} should be a string, got {type(value).__name__}")
                            
                            # Check string length for varchar
                            if 'varchar' in column_type:
                                # Extract the length from the type (e.g., varchar(255))
                                length_match = re.search(r'\((\d+)\)', column_type)
                                if length_match:
                                    max_length = int(length_match.group(1))
                                    if len(str(value)) > max_length:
                                        errors.append(f"Record {i}: Column {column_name} value exceeds maximum length of {max_length}")
                        
                        elif 'date' in column_type or 'time' in column_type:
                            # Basic date/time validation
                            if not isinstance(value, str):
                                errors.append(f"Record {i}: Column {column_name} should be a date/time string, got {type(value).__name__}")
            
            # Return the validation result
            return len(errors) == 0, errors
        
        except Exception as e:
            errors.append(f"Failed to validate data: {str(e)}")
            return False, errors
    
    def initialize_data(self, data_dir: str) -> Tuple[bool, str]:
        """
        Initialize data from a directory.
        
        Args:
            data_dir: Path to the data directory
            
        Returns:
            Tuple[bool, str]: Success status and message
        """
        try:
            # Check if the data directory exists
            if not os.path.exists(data_dir):
                return False, f"Data directory {data_dir} does not exist"
            
            # Get all data files in the directory
            data_files = []
            
            for root, _, files in os.walk(data_dir):
                for file in files:
                    # Check if the file is a data file
                    if file.endswith(('.csv', '.json', '.yaml', '.yml')):
                        data_files.append(os.path.join(root, file))
            
            # Check if there are any data files
            if not data_files:
                return True, "No data files found"
            
            # Load data from each file
            for data_file in data_files:
                # Get the table name from the file name
                table_name = os.path.splitext(os.path.basename(data_file))[0]
                
                # Load the data from the file
                success, message = self.load_data_from_file(table_name, data_file)
                
                if not success:
                    return False, message
            
            logger.info(f"Initialized data from {len(data_files)} files")
            return True, "Data initialized successfully"
        
        except Exception as e:
            logger.error(f"Failed to initialize data: {str(e)}")
            return False, f"Failed to initialize data: {str(e)}"


def create_data_manager(connection: DatabaseConnection) -> DataManager:
    """
    Create a data manager.
    
    Args:
        connection: Database connection
        
    Returns:
        DataManager: Data manager
    """
    return DataManager(connection)
