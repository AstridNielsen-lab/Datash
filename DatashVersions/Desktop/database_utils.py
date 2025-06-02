"""
Database utilities for Datash.

This module provides utilities for connecting to various database systems,
executing queries, and handling data import/export operations.
"""

import os
import sys
from typing import Dict, List, Optional, Any, Tuple, Union
import json
import csv
from pathlib import Path


class DatabaseConnectionError(Exception):
    """Exception raised for database connection errors."""
    pass


def check_database_connection(db_type: str, connection_params: Dict[str, Any]) -> bool:
    """
    Check if a database connection can be established.
    
    Args:
        db_type: The type of database (sqlite, mysql, postgresql, mongodb)
        connection_params: Dictionary of connection parameters
        
    Returns:
        True if connection successful, False otherwise
        
    Raises:
        DatabaseConnectionError: If the database type is not supported
    """
    db_type = db_type.lower()
    
    try:
        if db_type == "sqlite":
            return _check_sqlite_connection(connection_params)
        elif db_type == "mysql":
            return _check_mysql_connection(connection_params)
        elif db_type == "postgresql":
            return _check_postgresql_connection(connection_params)
        elif db_type == "mongodb":
            return _check_mongodb_connection(connection_params)
        else:
            raise DatabaseConnectionError(f"Unsupported database type: {db_type}")
    except Exception as e:
        raise DatabaseConnectionError(f"Error connecting to {db_type}: {str(e)}")


def execute_query(db_type: str, connection_params: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
    """
    Execute a query on the specified database.
    
    Args:
        db_type: The type of database
        connection_params: Dictionary of connection parameters
        query: The query to execute
        
    Returns:
        List of dictionaries containing the query results
        
    Raises:
        Exception: If the query execution fails
    """
    db_type = db_type.lower()
    
    if db_type == "sqlite":
        return _execute_sqlite_query(connection_params, query)
    elif db_type == "mysql":
        return _execute_mysql_query(connection_params, query)
    elif db_type == "postgresql":
        return _execute_postgresql_query(connection_params, query)
    elif db_type == "mongodb":
        return _execute_mongodb_query(connection_params, query)
    else:
        raise ValueError(f"Unsupported database type: {db_type}")


def import_file_to_db(
    file_path: str, 
    db_type: str, 
    connection_params: Dict[str, Any], 
    table_name: str
) -> str:
    """
    Import a file (CSV, JSON) into a database table.
    
    Args:
        file_path: Path to the file to import
        db_type: The type of database
        connection_params: Dictionary of connection parameters
        table_name: Name of the table to import data into
        
    Returns:
        Success message string
        
    Raises:
        Exception: If the import fails
    """
    # Check if file exists
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
        
    # Determine file type
    file_ext = os.path.splitext(file_path)[1].lower()
    
    if file_ext == '.csv':
        return _import_csv_to_db(file_path, db_type, connection_params, table_name)
    elif file_ext == '.json':
        return _import_json_to_db(file_path, db_type, connection_params, table_name)
    else:
        raise ValueError(f"Unsupported file type: {file_ext}")


def export_query_to_file(
    query_result: List[Dict[str, Any]], 
    file_path: str, 
    file_format: str = 'csv'
) -> str:
    """
    Export query results to a file.
    
    Args:
        query_result: List of dictionaries containing query results
        file_path: Path to save the file
        file_format: Format to save as (csv, json)
        
    Returns:
        Success message string
        
    Raises:
        Exception: If the export fails
    """
    file_format = file_format.lower()
    
    if file_format == 'csv':
        return _export_to_csv(query_result, file_path)
    elif file_format == 'json':
        return _export_to_json(query_result, file_path)
    else:
        raise ValueError(f"Unsupported export format: {file_format}")


# Private helper functions for database connections

def _check_sqlite_connection(connection_params: Dict[str, Any]) -> bool:
    """Check SQLite connection."""
    try:
        import sqlite3
        db_path = connection_params.get('database', ':memory:')
        conn = sqlite3.connect(db_path)
        conn.close()
        return True
    except ImportError:
        raise DatabaseConnectionError("SQLite3 module not found. Install with: pip install sqlite3")
    except Exception as e:
        raise DatabaseConnectionError(f"SQLite connection error: {str(e)}")


def _check_mysql_connection(connection_params: Dict[str, Any]) -> bool:
    """Check MySQL connection."""
    try:
        import mysql.connector
        conn = mysql.connector.connect(
            host=connection_params.get('host', 'localhost'),
            user=connection_params.get('user', 'root'),
            password=connection_params.get('password', ''),
            database=connection_params.get('database', '')
        )
        conn.close()
        return True
    except ImportError:
        raise DatabaseConnectionError("MySQL connector not found. Install with: pip install mysql-connector-python")
    except Exception as e:
        raise DatabaseConnectionError(f"MySQL connection error: {str(e)}")


def _check_postgresql_connection(connection_params: Dict[str, Any]) -> bool:
    """Check PostgreSQL connection."""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=connection_params.get('host', 'localhost'),
            user=connection_params.get('user', 'postgres'),
            password=connection_params.get('password', ''),
            dbname=connection_params.get('database', 'postgres'),
            port=connection_params.get('port', 5432)
        )
        conn.close()
        return True
    except ImportError:
        raise DatabaseConnectionError("Psycopg2 not found. Install with: pip install psycopg2-binary")
    except Exception as e:
        raise DatabaseConnectionError(f"PostgreSQL connection error: {str(e)}")


def _check_mongodb_connection(connection_params: Dict[str, Any]) -> bool:
    """Check MongoDB connection."""
    try:
        import pymongo
        client = pymongo.MongoClient(
            host=connection_params.get('host', 'localhost'),
            port=connection_params.get('port', 27017),
            username=connection_params.get('user', None),
            password=connection_params.get('password', None)
        )
        # Force connection
        client.admin.command('ping')
        client.close()
        return True
    except ImportError:
        raise DatabaseConnectionError("PyMongo not found. Install with: pip install pymongo")
    except Exception as e:
        raise DatabaseConnectionError(f"MongoDB connection error: {str(e)}")


# Private helper functions for query execution

def _execute_sqlite_query(connection_params: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
    """Execute a query on SQLite."""
    try:
        import sqlite3
        db_path = connection_params.get('database', ':memory:')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query)
        
        # If SELECT query, fetch results
        if query.strip().lower().startswith('select'):
            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return results
        
        # If not SELECT, commit and return affected row count
        conn.commit()
        affected_rows = cursor.rowcount
        conn.close()
        return [{"affected_rows": affected_rows}]
        
    except Exception as e:
        raise Exception(f"SQLite query execution error: {str(e)}")


def _execute_mysql_query(connection_params: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
    """Execute a query on MySQL."""
    try:
        import mysql.connector
        conn = mysql.connector.connect(
            host=connection_params.get('host', 'localhost'),
            user=connection_params.get('user', 'root'),
            password=connection_params.get('password', ''),
            database=connection_params.get('database', '')
        )
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        
        # If SELECT query, fetch results
        if query.strip().lower().startswith('select'):
            results = cursor.fetchall()
            conn.close()
            return results
        
        # If not SELECT, commit and return affected row count
        conn.commit()
        affected_rows = cursor.rowcount
        conn.close()
        return [{"affected_rows": affected_rows}]
        
    except Exception as e:
        raise Exception(f"MySQL query execution error: {str(e)}")


def _execute_postgresql_query(connection_params: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
    """Execute a query on PostgreSQL."""
    try:
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(
            host=connection_params.get('host', 'localhost'),
            user=connection_params.get('user', 'postgres'),
            password=connection_params.get('password', ''),
            dbname=connection_params.get('database', 'postgres'),
            port=connection_params.get('port', 5432)
        )
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(query)
        
        # If SELECT query, fetch results
        if query.strip().lower().startswith('select'):
            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return results
        
        # If not SELECT, commit and return affected row count
        conn.commit()
        affected_rows = cursor.rowcount
        conn.close()
        return [{"affected_rows": affected_rows}]
        
    except Exception as e:
        raise Exception(f"PostgreSQL query execution error: {str(e)}")


def _execute_mongodb_query(connection_params: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
    """Execute a query on MongoDB."""
    try:
        import pymongo
        import json
        
        client = pymongo.MongoClient(
            host=connection_params.get('host', 'localhost'),
            port=connection_params.get('port', 27017),
            username=connection_params.get('user', None),
            password=connection_params.get('password', None)
        )
        
        # Parse the query as a JSON object
        query_dict = json.loads(query)
        
        database = connection_params.get('database', 'test')
        collection = connection_params.get('collection', 'test')
        
        db = client[database]
        coll = db[collection]
        
        # Determine operation type
        operation = query_dict.get('operation', 'find')
        
        if operation == 'find':
            filter_dict = query_dict.get('filter', {})
            projection = query_dict.get('projection', None)
            cursor = coll.find(filter_dict, projection)
            results = list(cursor)
            # Convert ObjectId to string for JSON serialization
            for doc in results:
                if '_id' in doc and isinstance(doc['_id'], pymongo.ObjectId):
                    doc['_id'] = str(doc['_id'])
            client.close()
            return results
            
        elif operation == 'insert':
            documents = query_dict.get('documents', [])
            if isinstance(documents, list):
                result = coll.insert_many(documents)
                client.close()
                return [{"inserted_ids": [str(id) for id in result.inserted_ids]}]
            else:
                result = coll.insert_one(documents)
                client.close()
                return [{"inserted_id": str(result.inserted_id)}]
                
        elif operation == 'update':
            filter_dict = query_dict.get('filter', {})
            update_dict = query_dict.get('update', {})
            if query_dict.get('many', False):
                result = coll.update_many(filter_dict, update_dict)
                client.close()
                return [{"matched_count": result.matched_count, "modified_count": result.modified_count}]
            else:
                result = coll.update_one(filter_dict, update_dict)
                client.close()
                return [{"matched_count": result.matched_count, "modified_count": result.modified_count}]
                
        elif operation == 'delete':
            filter_dict = query_dict.get('filter', {})
            if query_dict.get('many', False):
                result = coll.delete_many(filter_dict)
                client.close()
                return [{"deleted_count": result.deleted_count}]
            else:
                result = coll.delete_one(filter_dict)
                client.close()
                return [{"deleted_count": result.deleted_count}]
                
        else:
            client.close()
            raise ValueError(f"Unsupported MongoDB operation: {operation}")
            
    except Exception as e:
        raise Exception(f"MongoDB query execution error: {str(e)}")


# Private helper functions for file import/export

def _import_csv_to_db(
    file_path: str, 
    db_type: str, 
    connection_params: Dict[str, Any], 
    table_name: str
) -> str:
    """Import a CSV file to a database table."""
    try:
        # Read CSV file to determine structure
        with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
            csv_reader = csv.reader(csvfile)
            headers = next(csv_reader)  # Get column names from first row
            
            # Create a list of dictionaries from the CSV data
            data = []
            for row in csv_reader:
                if len(row) == len(headers):  # Skip malformed rows
                    data.append(dict(zip(headers, row)))
            
        # Import based on database type
        if db_type.lower() == 'sqlite':
            return _import_to_sqlite(data, headers, connection_params, table_name)
        elif db_type.lower() == 'mysql':
            return _import_to_mysql(data, headers, connection_params, table_name)
        elif db_type.lower() == 'postgresql':
            return _import_to_postgresql(data, headers, connection_params, table_name)
        elif db_type.lower() == 'mongodb':
            return _import_to_mongodb(data, connection_params, table_name)
        else:
            raise ValueError(f"Unsupported database type for import: {db_type}")
    except Exception as e:
        raise Exception(f"Error importing CSV: {str(e)}")


def _import_json_to_db(
    file_path: str, 
    db_type: str, 
    connection_params: Dict[str, Any], 
    table_name: str
) -> str:
    """Import a JSON file to a database table."""
    try:
        # Read JSON file
        with open(file_path, 'r', encoding='utf-8') as jsonfile:
            data = json.load(jsonfile)
            
        # Ensure data is a list of dictionaries
        if isinstance(data, dict):
            data = [data]  # Convert single object to list
        
        if not data:
            return "JSON file contains no data to import"
            
        # Get headers from first item
        headers = list(data[0].keys())
        
        # Import based on database type
        if db_type.lower() == 'sqlite':
            return _import_to_sqlite(data, headers, connection_params, table_name)
        elif db_type.lower() == 'mysql':
            return _import_to_mysql(data, headers, connection_params, table_name)
        elif db_type.lower() == 'postgresql':
            return _import_to_postgresql(data, headers, connection_params, table_name)
        elif db_type.lower() == 'mongodb':
            return _import_to_mongodb(data, connection_params, table_name)
        else:
            raise ValueError(f"Unsupported database type for import: {db_type}")
    except Exception as e:
        raise Exception(f"Error importing JSON: {str(e)}")


def _import_to_sqlite(
    data: List[Dict[str, Any]], 
    headers: List[str], 
    connection_params: Dict[str, Any], 
    table_name: str
) -> str:
    """Import data to SQLite."""
    import sqlite3
    
    db_path = connection_params.get('database', ':memory:')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    columns = ', '.join([f'"{h}" TEXT' for h in headers])
    cursor.execute(f'CREATE TABLE IF NOT EXISTS "{table_name}" ({columns})')
    
    # Insert data
    placeholders = ', '.join(['?' for _ in headers])
    insert_query = f'INSERT INTO "{table_name}" ({", ".join([f"\"{h}\"" for h in headers])}) VALUES ({placeholders})'
    
    for row in data:
        values = [row.get(header, '') for header in headers]
        cursor.execute(insert_query, values)
    
    conn.commit()
    row_count = len(data)
    conn.close()
    
    return f"Successfully imported {row_count} rows into SQLite table '{table_name}'"


def _import_to_mysql(
    data: List[Dict[str, Any]], 
    headers: List[str], 
    connection_params: Dict[str, Any], 
    table_name: str
) -> str:
    """Import data to MySQL."""
    import mysql.connector
    
    conn = mysql.connector.connect(
        host=connection_params.get('host', 'localhost'),
        user=connection_params.get('user', 'root'),
        password=connection_params.get('password', ''),
        database=connection_params.get('database', '')
    )
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    columns = ', '.join([f'`{h}` TEXT' for h in headers])
    cursor.execute(f"CREATE TABLE IF NOT EXISTS `{table_name}` ({columns})")
    
    # Insert data
    placeholders = ', '.join(['%s' for _ in headers])
    insert_query = f"INSERT INTO `{table_name}` ({', '.join([f'`{h}`' for h in headers])}) VALUES ({placeholders})"
    
    for row in data:
        values = [row.get(header, '') for header in headers]
        cursor.execute(insert_query, values)
    
    conn.commit()
    row_count = len(data)
    conn.close()
    
    return f"Successfully imported {row_count} rows into MySQL table '{table_name}'"


def _import_to_postgresql(
    data: List[Dict[str, Any]], 
    headers: List[str], 
    connection_params: Dict[str, Any], 
    table_name: str
) -> str:
    """Import data to PostgreSQL."""
    import psycopg2
    
    conn = psycopg2.connect(
        host=connection_params.get('host', 'localhost'),
        user=connection_params.get('user', 'postgres'),
        password=connection_params.get('password', ''),
        dbname=connection_params.get('database', 'postgres'),
        port=connection_params.get('port', 5432)
    )
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    columns = ', '.join([f'"{h}" TEXT' for h in headers])
    cursor.execute(f'CREATE TABLE IF NOT EXISTS "{table_name}" ({columns})')
    
    # Insert data
    placeholders = ', '.join(['%s' for _ in headers])
    insert_query = f'INSERT INTO "{table_name}" ({", ".join([f"\"{h}\"" for h in headers])}) VALUES ({placeholders})'
    
    for row in data:
        values = [row.get(header, '') for header in headers]
        cursor.execute(insert_query, values)
    
    conn.commit()
    row_count = len(data)
    conn.close()
    
    return f"Successfully imported {row_count} rows into PostgreSQL table '{table_name}'"


def _import_to_mongodb(
    data: List[Dict[str, Any]], 
    connection_params: Dict[str, Any], 
    collection_name: str
) -> str:
    """Import data to MongoDB."""
    import pymongo
    
    client = pymongo.MongoClient(
        host=connection_params.get('host', 'localhost'),
        port=connection_params.get('port', 27017),
        username=connection_params.get('user', None),
        password=connection_params.get('password', None)
    )
    
    database = connection_params.get('database', 'test')
    db = client[database]
    collection = db[collection_name]
    
    # Insert data
    result = collection.insert_many(data)
    row_count = len(result.inserted_ids)
    client.close()
    
    return f"Successfully imported {row_count} documents into MongoDB collection '{collection_name}'"


def _export_to_csv(data: List[Dict[str, Any]], file_path: str) -> str:
    """Export data to a CSV file."""
    try:
        if not data:
            return "No data to export"
            
        # Ensure the directory exists
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        
        # Get headers from first row
        headers = list(data[0].keys())
        
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)
            
        return f"Successfully exported {len(data)} rows to CSV file: {file_path}"
    except Exception as e:
        raise Exception(f"Error exporting to CSV: {str(e)}")


def _export_to_json(data: List[Dict[str, Any]], file_path: str) -> str:
    """Export data to a JSON file."""
    try:
        if not data:
            return "No data to export"
            
        # Ensure the directory exists
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, indent=2)
            
        return f"Successfully exported {len(data)} records to JSON file: {file_path}"
    except Exception as e:
        raise Exception(f"Error exporting to JSON: {str(e)}")

