"""
Command processor for Datash.

This module handles command processing, local command execution,
intelligent autocompletion, and suggestion generation based on user input and history.
"""

import os
import sys
import re
import subprocess
import shlex
import json
import logging
from typing import Dict, List, Optional, Any, Tuple, Callable, Set, Union, Iterable
import platform
from pathlib import Path
import glob
import io
from contextlib import redirect_stdout, redirect_stderr

# For autocompletion and interactive shell
from prompt_toolkit.completion import Completer, Completion, PathCompleter, WordCompleter
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.document import Document

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("datash.command")

# Constants
GIT_COMMANDS = [
    "add", "am", "archive", "bisect", "branch", "bundle", "checkout", "cherry-pick",
    "citool", "clean", "clone", "commit", "describe", "diff", "fetch", "format-patch",
    "gc", "gitk", "grep", "gui", "init", "log", "merge", "mv", "notes", "pull", "push",
    "range-diff", "rebase", "reset", "restore", "revert", "rm", "shortlog", "show",
    "sparse-checkout", "stash", "status", "submodule", "switch", "tag", "worktree"
]

DATABASE_COMMANDS = [
    # SQL commands
    "SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "ALTER", "DROP", "TRUNCATE",
    "GRANT", "REVOKE", "COMMIT", "ROLLBACK", "SAVEPOINT", "TRANSACTION", "JOIN",
    "UNION", "INDEX", "VIEW", "PROCEDURE", "FUNCTION", "TRIGGER",
    # Database connection commands
    "connect", "disconnect", "show tables", "describe", "show databases",
    # SQLite specific
    "sqlite3", ".tables", ".schema", ".mode", ".import", ".dump", ".backup",
    # MySQL specific
    "mysql", "mysqldump", "SHOW TABLES", "SHOW DATABASES", "DESCRIBE",
    # PostgreSQL specific
    "psql", "pg_dump", "\\c", "\\d", "\\dt", "\\l", "\\du",
    # MongoDB specific
    "mongo", "mongodump", "mongorestore", "db.collection.find", "db.collection.insert",
    "db.collection.update", "db.collection.remove", "use", "show dbs", "show collections"
]

FILE_COMMANDS = [
    "cat", "head", "tail", "less", "more", "grep", "find", "ls", "dir", "cd", 
    "mkdir", "rm", "cp", "mv", "touch", "chmod", "chown", "wc", "sort", "uniq",
    "awk", "sed", "cut", "paste", "join", "split", "tar", "zip", "unzip", "gzip",
    "bzip2", "import", "export", "load", "save", "convert", "transform", "format",
    "upload", "download", "open", "close", "read", "write"
]

SYSTEM_COMMANDS = [
    "echo", "env", "set", "export", "alias", "unalias", "history", "exit", "quit",
    "clear", "cls", "pwd", "date", "time", "whoami", "hostname", "uname", "df",
    "du", "top", "ps", "kill", "sleep", "wait", "which", "type", "man", "help"
]

# Command categories
COMMAND_CATEGORIES = {
    "git": GIT_COMMANDS,
    "database": DATABASE_COMMANDS,
    "file": FILE_COMMANDS,
    "system": SYSTEM_COMMANDS
}

# File extensions for data files
DATA_FILE_EXTENSIONS = ['.csv', '.json', '.xml', '.yaml', '.yml', '.txt', '.sql', '.db', '.sqlite', '.xls', '.xlsx']


class CommandHistory:
    """Class to manage command history with search and suggestion capabilities."""
    
    def __init__(self, max_history: int = 1000):
        """
        Initialize command history.
        
        Args:
            max_history: Maximum number of commands to store in history
        """
        self.history = InMemoryHistory()
        self.max_history = max_history
        self.command_frequencies: Dict[str, int] = {}  # Track command frequency for better suggestions
        
    def add_command(self, command: str):
        """
        Add a command to history.
        
        Args:
            command: The command to add
        """
        if not command.strip():
            return
            
        # Add to prompt_toolkit history
        self.history.append_string(command)
        
        # Update frequency counter
        self.command_frequencies[command] = self.command_frequencies.get(command, 0) + 1
        
    def search(self, prefix: str) -> List[str]:
        """
        Search history for commands starting with the given prefix.
        
        Args:
            prefix: The prefix to search for
            
        Returns:
            List of matching commands, most frequent first
        """
        if not prefix:
            return []
            
        # Find all matches
        matches = [cmd for cmd in self.command_frequencies.keys() 
                  if cmd.lower().startswith(prefix.lower())]
        
        # Sort by frequency (most frequent first)
        matches.sort(key=lambda cmd: self.command_frequencies[cmd], reverse=True)
        
        return matches[:10]  # Limit to top 10 results
        
    def get_most_common(self, n: int = 10) -> List[str]:
        """
        Get the most commonly used commands.
        
        Args:
            n: Number of commands to return
            
        Returns:
            List of most common commands
        """
        return sorted(self.command_frequencies.keys(), 
                     key=lambda cmd: self.command_frequencies[cmd], 
                     reverse=True)[:n]
                     
    def get_recent(self, n: int = 10) -> List[str]:
        """
        Get the most recent commands.
        
        Args:
            n: Number of recent commands to return
            
        Returns:
            List of recent commands
        """
        result = []
        for cmd in reversed(list(self.history.get_strings())):
            if cmd not in result:
                result.append(cmd)
                if len(result) >= n:
                    break
        return result


class DatashCompleter(Completer):
    """Custom completer for Datash commands."""
    
    def __init__(self, state: Dict[str, Any]):
        """
        Initialize the completer.
        
        Args:
            state: Application state dictionary
        """
        self.state = state
        self.path_completer = PathCompleter(expanduser=True)
        self.git_completer = WordCompleter(GIT_COMMANDS)
        self.db_completer = WordCompleter(DATABASE_COMMANDS)
        self.file_completer = WordCompleter(FILE_COMMANDS)
        self.system_completer = WordCompleter(SYSTEM_COMMANDS)
        
    def get_completions(self, document: Document, complete_event):
        """
        Get completion suggestions for the current input.
        
        Args:
            document: The current document (text input)
            complete_event: The completion event
            
        Yields:
            Completion objects for suggestions
        """
        text = document.text_before_cursor.lstrip()
        
        # Empty input - suggest common commands
        if not text:
            for category, commands in COMMAND_CATEGORIES.items():
                for cmd in commands[:3]:  # Show top 3 from each category
                    yield Completion(cmd, start_position=0, 
                                    display=f"{cmd} ({category})")
            return
            
        # History-based completion
        if self.state.get("command_history"):
            history_matches = self.state["command_history"].search(text)
            for cmd in history_matches:
                yield Completion(cmd, start_position=-len(text),
                                display=f"{cmd} (history)")
        
        # Git command completion
        if text.startswith("git "):
            subcommand = text[4:].lstrip()
            for completion in self.git_completer.get_completions(
                Document(subcommand, cursor_position=len(subcommand)),
                complete_event
            ):
                yield Completion(f"git {completion.text}", 
                                start_position=-len(text),
                                display=completion.display)
            return
            
        # Path completion for commands that expect a path
        path_command_prefixes = ["cd ", "ls ", "cat ", "open ", "import "]
        for prefix in path_command_prefixes:
            if text.startswith(prefix):
                path = text[len(prefix):]
                for completion in self.path_completer.get_completions(
                    Document(path, cursor_position=len(path)),
                    complete_event
                ):
                    yield Completion(f"{prefix}{completion.text}", 
                                    start_position=-len(text),
                                    display=completion.display)
                return
                
        # Category-based completion
        lower_text = text.lower()
        
        # Database commands
        if any(kw in lower_text for kw in ["sql", "database", "table", "query", "select"]):
            for cmd in DATABASE_COMMANDS:
                if cmd.lower().startswith(lower_text) or lower_text in cmd.lower():
                    yield Completion(cmd, start_position=-len(text),
                                    display=f"{cmd} (database)")
            return
            
        # Git commands
        if any(kw in lower_text for kw in ["git", "commit", "push", "pull", "clone"]):
            for cmd in GIT_COMMANDS:
                full_cmd = f"git {cmd}"
                if full_cmd.lower().startswith(lower_text) or lower_text in full_cmd.lower():
                    yield Completion(full_cmd, start_position=-len(text),
                                   display=f"{full_cmd} (git)")
            return
            
        # File commands
        if any(ext in lower_text for ext in [".csv", ".json", ".sql", ".txt"]):
            for cmd in FILE_COMMANDS:
                if cmd.lower().startswith(lower_text) or lower_text in cmd.lower():
                    yield Completion(cmd, start_position=-len(text),
                                   display=f"{cmd} (file)")
            return
            
        # Fall back to general command completion
        all_commands = []
        for commands in COMMAND_CATEGORIES.values():
            all_commands.extend(commands)
            
        for cmd in all_commands:
            if cmd.lower().startswith(lower_text):
                yield Completion(cmd, start_position=-len(text),
                               display=cmd)


def process_command(command: str, state: Dict[str, Any]) -> Optional[str]:
    """
    Process a command locally if it's a built-in command.
    
    Args:
        command: The command to process
        state: The application state dictionary
        
    Returns:
        Result string if command was processed locally, None otherwise
    """
    # Strip whitespace
    command = command.strip()
    
    if not command:
        return None
        
    # Update command history if available
    if "command_history" in state and isinstance(state["command_history"], CommandHistory):
        state["command_history"].add_command(command)
    
    # Handle built-in commands
    if command.lower() == "help":
        return _get_help_text()
        
    if command.lower() == "history":
        return _show_history(state)
        
    if command.lower().startswith("cd "):
        return _change_directory(command[3:], state)
        
    if command.lower() == "pwd":
        return f"Current directory: {state['working_directory']}"
        
    if command.lower() == "clear" or command.lower() == "cls":
        if platform.system() == "Windows":
            os.system("cls")
        else:
            os.system("clear")
        return None  # No output needed
        
    if command.lower().startswith("shell ") or command.lower().startswith("!"):
        # Execute shell commands directly
        if command.lower().startswith("shell "):
            shell_cmd = command[6:]
        else:
            shell_cmd = command[1:]
        return _execute_shell_command(shell_cmd, state)
        
    # Check for database commands
    if _is_database_command(command):
        return _process_database_command(command, state)
        
    # Check for git commands
    if command.lower().startswith("git "):
        return _process_git_command(command[4:], state)
        
    # Check for file operations
    if _is_file_operation(command):
        return _process_file_operation(command, state)
        
    # If we got here, it's not a built-in command
    return None


def _is_database_command(command: str) -> bool:
    """
    Check if a command is a database-related command.
    
    Args:
        command: The command to check
        
    Returns:
        True if it's a database command, False otherwise
    """
    command_lower = command.lower()
    db_keywords = [
        "select ", "insert ", "update ", "delete ", "create table", "alter table",
        "drop table", "truncate", "join ", "where ", "database", "sqlite", "mysql",
        "postgresql", "mongodb", "sql", "query", "connect", "show tables", 
        "describe table", ".tables", ".schema", "\\dt", "db."
    ]
    
    return any(keyword in command_lower for keyword in db_keywords)


def _process_database_command(command: str, state: Dict[str, Any]) -> str:
    """
    Process a database-related command.
    
    Args:
        command: The database command to process
        state: The application state
        
    Returns:
        Result of the database operation
    """
    # Check if it's an SQLite command
    if command.lower().startswith("sqlite3 ") or command.lower().startswith("."):
        return _execute_sqlite_command(command, state)
        
    # Check if it's a MySQL command
    if command.lower().startswith("mysql "):
        return _execute_mysql_command(command, state)
        
    # Check if it's a PostgreSQL command
    if command.lower().startswith("psql ") or command.lower().startswith("\\"):
        return _execute_postgresql_command(command, state)
        
    # Check if it's a MongoDB command
    if command.lower().startswith("mongo ") or command.lower().startswith("db."):
        return _execute_mongodb_command(command, state)
        
    # For direct SQL queries
    if command.lower().startswith(("select ", "insert ", "update ", "delete ", "create ", "alter ")):
        # Use the current database connection if available
        if state.get("current_db"):
            db_type = state.get("current_db_type", "sqlite")  # Default to SQLite
            return f"Executing SQL on {db_type} database:\n{command}\n\nUse database_utils.execute_query() to run this query."
            
        return "No active database connection. Connect to a database first with 'connect to [database_type]'."
        
    # For database connection commands
    if command.lower().startswith("connect to "):
        db_type = command.lower().replace("connect to ", "").strip()
        state["current_db_type"] = db_type
        state["current_db"] = f"{db_type}_connection"  # Placeholder
        return f"Connected to {db_type} database (simulated)."
        
    # If we got here, it's a database command we don't directly handle
    return f"Database command recognized: {command}\n\nThis would be processed using the appropriate database driver."


def _is_file_operation(command: str) -> bool:
    """
    Check if a command is a file operation.
    
    Args:
        command: The command to check
        
    Returns:
        True if it's a file operation, False otherwise
    """
    command_lower = command.lower()
    file_keywords = [
        "import ", "export ", "load ", "save ", "read ", "write ",
        "csv", "json", "xml", "yaml", "txt", "file", "open ", 
        "convert ", "transform "
    ]
    
    # Check for data file extensions
    has_data_ext = any(ext in command_lower for ext in DATA_FILE_EXTENSIONS)
    
    # Check for file operation keywords
    has_file_keyword = any(keyword in command_lower for keyword in file_keywords)
    
    return has_data_ext or has_file_keyword


def _process_file_operation(command: str, state: Dict[str, Any]) -> str:
    """
    Process a file operation command.
    
    Args:
        command: The file operation command to process
        state: The application state
        
    Returns:
        Result of the file operation
    """
    command_lower = command.lower()
    
    # Import data from file
    if command_lower.startswith("import "):
        parts = command.split()
        if len(parts) < 2:
            return "Invalid import command. Usage: import <file_path> [to <destination>]"
            
        file_path = parts[1]
        
        # Check if file exists
        if not os.path.isfile(file_path) and not os.path.isfile(os.path.join(state["working_directory"], file_path)):
            return f"File not found: {file_path}"
            
        # Check for destination (database, etc.)
        if len(parts) > 2 and "to" in command_lower:
            to_index = command_lower.index("to")
            destination = " ".join(parts[to_index+1:])
            return f"Importing data from {file_path} to {destination}...\n\nUse database_utils.import_file_to_db() to perform this operation."
            
        return f"File {file_path} ready for import.\n\nUse appropriate functions to process the data."
        
    # Export data to file
    if command_lower.startswith("export ") or command_lower.startswith("save "):
        parts = command.split()
        if len(parts) < 3:
            return "Invalid export command. Usage: export <data> to <file_path>"
            
        if "to" in command_lower:
            to_index = command_lower.index("to")
            data_source = " ".join(parts[1:to_index])
            file_path = " ".join(parts[to_index+1:])
            return f"Exporting {data_source} to {file_path}...\n\nUse database_utils.export_query_to_file() to perform this operation."
            
        return "Invalid export command. Please specify destination with 'to'."
        
    # File analysis/conversion
    if any(x in command_lower for x in ["analyze ", "convert ", "transform "]):
        for ext in DATA_FILE_EXTENSIONS:
            if ext in command_lower:
                file_parts = [p for p in command.split() if ext in p.lower()]
                if file_parts:
                    file_path = file_parts[0]
                    return f"Analyzing file: {file_path}\n\nThis would process the file according to its type and the requested operation."
                    
        return "Please specify a valid data file to process."
        
    # Generic file operation
    return f"File operation: {command}\n\nThis would be processed using appropriate file handling functions."


def _process_git_command(git_command: str, state: Dict[str, Any]) -> str:
    """
    Process a git command.
    
    Args:
        git_command: The git command to process (without the 'git ' prefix)
        state: The application state
        
    Returns:
        Result of the git command
    """
    # Check if git is installed
    try:
        result = subprocess.run(
            ["git", "--version"], 
            capture_output=True, 
            text=True,
            check=False
        )
        if result.returncode != 0:
            return "Git does not appear to be installed or is not in the PATH."
    except Exception:
        return "Error checking git installation."
        
    # Execute the git command
    try:
        result = subprocess.run(
            ["git"] + shlex.split(git_command),
            cwd=state["working_directory"],
            capture_output=True,
            text=True,
            check=False
        )
        
        output = result.stdout
        if result.stderr:
            if output:
                output += "\n" + result.stderr
            else:
                output = result.stderr
                
        if not output:
            output = f"Git command executed successfully. Exit code: {result.returncode}"
            
        return output
        
    except Exception as e:
        return f"Error executing git command: {str(e)}"


def parse_code_blocks(response: str) -> List[Dict[str, str]]:
    """
    Parse code blocks from a markdown response.
    
    Args:
        response: The markdown text to parse
        
    Returns:
        List of dictionaries with 'language' and 'code' keys
    """
    # Regular expression to match code blocks with language specification
    pattern = r"```(\w*)\n(.*?)```"
    matches = re.finditer(pattern, response, re.DOTALL)
    
    blocks = []
    for match in matches:
        language = match.group(1) or "text"
        code = match.group(2).strip()
        blocks.append({
            "language": language,
            "code": code
        })
        
    return blocks


def execute_code_block(code_block: Dict[str, str], state: Dict[str, Any]) -> str:
    """
    Execute a code block based on its language.
    
    Args:
        code_block: Dictionary with 'language' and 'code' keys
        state: The application state
        
    Returns:
        Result of executing the code block
    """
    language = code_block["language"].lower()
    code = code_block["code"]
    
    # Shell commands (bash, shell, sh, zsh, cmd, powershell, ps)
    if language in ["bash", "shell", "sh", "zsh", "cmd", "powershell", "ps", ""]:
        return _execute_shell_command(code, state)
        
    # SQL commands
    if language in ["sql", "mysql", "postgresql", "sqlite"]:
        return f"SQL code:\n{code}\n\nWould execute using database_utils.execute_query()"
        
    # Python code
    if language in ["python", "py"]:
        return f"Python code:\n{code}\n\nWould execute in a controlled environment using exec()"
        
    # Other languages - just show the code
    return f"Code block ({language}):\n{code}\n\nExecute this code using an appropriate interpreter or environment."


def suggest_next_action(command: str, response: str, state: Dict[str, Any]) -> Optional[str]:
    """
    Generate a suggestion for the next action based on the current command and response.
    
    Args:
        command: The current command
        response: The response from the AI
        state: The application state
        
    Returns:
        A suggestion string or None
    """
    # Extract code blocks - if there are code blocks, suggest executing them
    code_blocks = parse_code_blocks(response)
    if code_blocks:
        if len(code_blocks) == 1:
            language = code_blocks[0]["language"] or "shell"
            return f"execute this {language} code"
        else:
            return f"execute one of these {len(code_blocks)} code blocks"
    
    # Command category-based suggestions
    command_lower = command.lower()
    
    # Database-related suggestions
    if any(kw in command_lower for kw in ["select", "query", "sql", "database"]):
        if "export" not in command_lower and "save" not in command_lower:
            return "export results to a CSV file"
        else:
            return "analyze the exported data"
        
    if "import" in command_lower and any(fmt in command_lower for fmt in ["csv", "json", "excel"]):
        return "analyze the imported data"
        
    # Git-related suggestions
    if "git clone" in command_lower:
        # Try to extract repository name for a better suggestion
        parts = command.split()
        if len(parts) > 2:
            repo_url = parts[2]
            repo_name = repo_url.split("/")[-1].replace(".git", "")
            return f"cd into the {repo_name} repository"
        return "cd into the cloned repository"
        
    if "git commit" in command_lower:
        return "push changes to remote"
        
    if "git push" in command_lower:
        return "check status with 'git status'"
        
    if "git pull" in command_lower:
        return "check the changes with 'git log'"
        
    # File-related suggestions
    if any(kw in command_lower for kw in ["list", "ls", "dir"]):
        return "examine a specific file"
        
    if any(kw in command_lower for kw in ["import", "load"]):
        return "query or analyze the imported data"
        
    # Look for suggestions in the AI response
    suggestion_patterns = [
        r"Next, you (can|could|might) ([^\.\n]+)",
        r"You (can|could|might) now ([^\.\n]+)",
        r"Try ([^\.\n]+) next",
        r"Now ([^\.\n]+)"
    ]
    
    for pattern in suggestion_patterns:
        matches = re.search(pattern, response)
        if matches:
            return matches.group(matches.lastindex)  # Get the suggestion part
    
    # If there's command history, suggest based on common patterns
    if "command_history" in state and hasattr(state["command_history"], "get_most_common"):
        common_commands = state["command_history"].get_most_common(5)
        if common_commands:
            for cmd in common_commands:
                # Don't suggest the command that was just executed
                if cmd != command and not command.startswith(cmd):
                    return cmd
    
    # No specific suggestion
    return None


def _execute_sqlite_command(command: str, state: Dict[str, Any]) -> str:
    """
    Execute an SQLite command.
    
    Args:
        command: The SQLite command to execute
        state: The application state
        
    Returns:
        Result of the SQLite command execution
    """
    # Check if it's a dot command (.tables, .schema, etc.)
    if command.startswith("."):
        return f"SQLite dot command: {command}\n\nWould execute using sqlite3 CLI."
        
    # If it starts with sqlite3, treat as shell command to SQLite CLI
    if command.startswith("sqlite3 "):
        return _execute_shell_command(command, state)
        
    # Otherwise, it's likely a SQL query
    return f"SQLite query: {command}\n\nWould execute using database_utils.execute_query()."


def _execute_mysql_command(command: str, state: Dict[str, Any]) -> str:
    """
    Execute a MySQL command.
    
    Args:
        command: The MySQL command to execute
        state: The application state
        
    Returns:
        Result of the MySQL command execution
    """
    # If it starts with mysql, treat as shell command to MySQL CLI
    if command.startswith("mysql "):
        return _execute_shell_command(command, state)
        
    # Otherwise, it's likely a SQL query
    return f"MySQL query: {command}\n\nWould execute using database_utils.execute_query()."


def _execute_postgresql_command(command: str, state: Dict[str, Any]) -> str:
    """
    Execute a PostgreSQL command.
    
    Args:
        command: The PostgreSQL command to execute
        state: The application state
        
    Returns:
        Result of the PostgreSQL command execution
    """
    # Check if it's a backslash command (\d, \l, etc.)
    if command.startswith("\\"):
        return f"PostgreSQL meta-command: {command}\n\nWould execute using psql CLI."
        
    # If it starts with psql, treat as shell command to PostgreSQL CLI
    if command.startswith("psql "):
        return _execute_shell_command(command, state)
        
    # Otherwise, it's likely a SQL query
    return f"PostgreSQL query: {command}\n\nWould execute using database_utils.execute_query()."


def _execute_mongodb_command(command: str, state: Dict[str, Any]) -> str:
    """
    Execute a MongoDB command.
    
    Args:
        command: The MongoDB command to execute
        state: The application state
        
    Returns:
        Result of the MongoDB command execution
    """
    # If it starts with mongo, treat as shell command to MongoDB CLI
    if command.startswith("mongo "):
        return _execute_shell_command(command, state)
        
    # Check if it's a db.<collection> command
    if command.startswith("db."):
        return f"MongoDB command: {command}\n\nWould execute using PyMongo."
        
    # Otherwise, it's likely a MongoDB query
    return f"MongoDB query: {command}\n\nWould execute using database_utils.execute_query()."


def _get_help_text() -> str:
    """Return the help text for Datash."""
    return """
Datash - Data + Shell + Intelligence

Built-in commands:
- help                   : Display this help message
- history                : Show command history
- cd <directory>         : Change working directory
- pwd                    : Print working directory
- clear, cls             : Clear the terminal screen
- shell <command> or !<command> : Execute a shell command directly

Database commands:
- connect to <database_type> : Connect to a database (sqlite, mysql, postgresql, mongodb)
- Any SQL command (SELECT, INSERT, UPDATE, etc.)
- Database-specific commands (.tables, \\dt, db.collection.find(), etc.)

Git commands:
- git <subcommand> <args> : Execute Git commands

File operations:
- import <file> to <destination> : Import data from a file
- export <data> to <file>       : Export data to a file
- analyze <file>                : Analyze file contents

For all other inputs, Datash will use AI to:
- Provide command suggestions
- Help with database queries
- Assist with file operations
- Support Git operations
- Offer data processing assistance

Examples:
- "import users.csv to sqlite database"
- "how to connect to PostgreSQL from Python"
- "git command to undo last commit"
- "analyze this JSON data structure"
"""


def _show_history(state: Dict[str, Any]) -> str:
    """Show command history."""
    # Check for command_history instance first
    if "command_history" in state and isinstance(state["command_history"], CommandHistory):
        history_strings = list(state["command_history"].history.get_strings())
        if not history_strings:
            return "No command history yet."
        return "\n".join([f"{i+1}: {cmd}" for i, cmd in enumerate(history_strings)])
    
    # Fall back to regular history list
    if not state.get("history", []):
        return "No command history yet."
        
    history = state["history"]
    return "\n".join([f"{i+1}: {cmd}" for i, cmd in enumerate(history)])


def _change_directory(path: str, state: Dict[str, Any]) -> str:
    """Change the working directory."""
    try:
        # Handle '~' for home directory
        if path.startswith("~"):
            home = os.path.expanduser("~")
            path = os.path.join(home, path[1:].lstrip("/\\"))
            
        # Handle relative paths
        if not os.path.isabs(path):
            path = os.path.join(state["working_directory"], path)
            
        # Normalize path
        path = os.path.normpath(path)
        
        # Check if directory exists
        if not os.path.isdir(path):
            return f"Directory not found: {path}"
            
        # Change directory
        os.chdir(path)
        state["working_directory"] = path
        return f"Changed directory to: {path}"
        
    except Exception as e:
        return f"Error changing directory: {str(e)}"


def _execute_shell_command(command: str, state: Dict[str, Any]) -> str:
    """
    Execute a shell command directly.
    
    Args:
        command: The shell command to execute
        state: The application state
        
    Returns:
        Output of the command
    """
    # Log the command for security auditing
    logger.info(f"Executing shell command: {command}")
    
    try:
        # Split multi-line commands and execute them sequentially
        if "\n" in command:
            lines = command.strip().split("\n")
            outputs = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith("#"):  # Skip empty lines and comments
                    result = _execute_single_shell_command(line, state)
                    outputs.append(f"$ {line}\n{result}")
            return "\n\n".join(outputs)
        else:
            return _execute_single_shell_command(command, state)
    except Exception as e:
        logger.error(f"Error in shell command execution: {str(e)}")
        return f"Error executing command: {str(e)}"


def _execute_single_shell_command(command: str, state: Dict[str, Any]) -> str:
    """
    Execute a single-line shell command.
    
    Args:
        command: The shell command to execute
        state: The application state
        
    Returns:
        Output of the command
    """
    try:
        # Determine the shell to use based on the platform
        shell = True
        
        # Execute the command
        process = subprocess.run(
            command, 
            shell=shell, 
            cwd=state["working_directory"],
            capture_output=True,
            text=True
        )
            
        # Combine stdout and stderr
        output = process.stdout
        if process.stderr:
            if output:
                output += "\n" + process.stderr
            else:
                output = process.stderr
                
        # Return the output or a success message
        if output:
            return output
        else:
            return f"Command executed successfully. Exit code: {process.returncode}"
            
    except Exception as e:
        return f"Error executing command: {str(e)}"


# Utility functions for command processing

def get_command_category(command: str) -> Optional[str]:
    """
    Determine the category of a command.
    
    Args:
        command: The command to categorize
        
    Returns:
        Category name or None if unknown
    """
    command_lower = command.lower()
    
    # Check for git commands
    if command_lower.startswith("git "):
        return "git"
        
    # Check for database commands
    if _is_database_command(command):
        return "database"
        
    # Check for file operations
    if _is_file_operation(command):
        return "file"
        
    # Check for system commands
    for system_cmd in SYSTEM_COMMANDS:
        if command_lower.startswith(f"{system_cmd} ") or command_lower == system_cmd:
            return "system"
            
    # Unknown category
    return None
