#!/usr/bin/env python3
"""
Datash - An intelligent terminal assistant for programmers.

This module serves as the main entry point for the Datash application,
providing an interactive shell interface for interacting with the assistant.

Developer: Dev Full Stack Julio Campos Machado
Company: Like Look Solutions
Website: https://likelook.wixsite.com/solutions
Phone: +55 11 3680-8030
"""

import os
import sys
import signal
import logging
import platform
import re
import time
import traceback
from typing import Optional, List, Dict, Any, Union
from pathlib import Path

# CLI framework
import typer

# Rich text formatting
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.prompt import Prompt, Confirm
from rich.highlighter import ReprHighlighter
from rich.theme import Theme
from rich import box

# Prompt toolkit for interactive shell
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.shortcuts import clear
from prompt_toolkit.completion import Completer, Completion

# Local modules
from api_client import GeminiClient
from command_processor import (
    process_command, suggest_next_action, CommandHistory, DatashCompleter,
    parse_code_blocks, execute_code_block, get_command_category
)
from database_utils import check_database_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("datash.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("datash")

# Initialize Typer app for CLI arguments
app = typer.Typer(
    help="Datash - Data + Shell + Intelligence: A terminal assistant for programmers.",
    add_completion=True,
)

# Initialize Rich console for pretty output
DATASH_THEME = Theme({
    "info": "dim cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "green",
    "command": "bold blue",
    "suggestion": "italic cyan",
    "code": "bold green",
    "path": "underline cyan",
})
console = Console(theme=DATASH_THEME, highlight=True)

# Application state
APP_STATE = {
    "history": [],
    "command_history": None,  # Will be initialized with CommandHistory
    "current_db": None,
    "current_db_type": None,
    "working_directory": os.getcwd(),
    "debug": False,
    "gemini_client": None,
    "session_start_time": time.time(),
    "command_count": 0,
}


# Style configurations for prompt-toolkit
DATASH_STYLE = Style.from_dict({
    'prompt': 'bold green',
    'continuation': 'bold gray',
    'suggestion': '#888888',
    'error': 'bold red',
})

# Key bindings for prompt-toolkit
kb = KeyBindings()

@kb.add('c-c')
def _(event):
    """Ctrl+C: Cancel current editing or exit."""
    event.app.exit(exception=KeyboardInterrupt())

@kb.add('c-d')
def _(event):
    """Ctrl+D: Exit the application."""
    event.app.exit()


def setup_history_file() -> Path:
    """Set up the history file path and ensure the directory exists."""
    home_dir = Path.home()
    datash_dir = home_dir / ".datash"
    datash_dir.mkdir(exist_ok=True)
    
    history_file = datash_dir / "history"
    return history_file


def initialize_app_state(debug: bool = False) -> Dict[str, Any]:
    """Initialize the application state."""
    # Start with base state
    state = APP_STATE.copy()
    
    # Set debug mode
    state["debug"] = debug
    
    # Initialize command history
    state["command_history"] = CommandHistory()
    
    # Initialize Gemini client
    state["gemini_client"] = GeminiClient()
    
    # Ensure working directory is set
    if not state["working_directory"]:
        state["working_directory"] = os.getcwd()
    
    return state


def display_welcome_message():
    """Display the welcome message for Datash."""
    console.print(Panel.fit(
        "[bold blue]Datash[/bold blue] - [italic]Data + Shell + Intelligence[/italic]\n\n"
        "An intelligent terminal assistant for programmers.\n"
        "Type [bold]help[/bold] for a list of commands or [bold]exit[/bold] to quit.",
        title="Welcome",
        border_style="blue",
        box=box.ROUNDED,
        padding=(1, 2),
    ))
    
    # Display developer and company information
    console.print(Panel.fit(
        "[bold]Developer:[/bold] Dev Full Stack Julio Campos Machado\n"
        "[bold]•[/bold] [bold]Company:[/bold] Like Look Solutions\n"
        "[bold]•[/bold] [bold]Website:[/bold] https://likelook.wixsite.com/solutions\n"
        "[bold]•[/bold] [bold]Phone:[/bold] +55 11 3680-8030",
        title="Developer Information",
        border_style="green",
        box=box.ROUNDED,
        padding=(1, 2),
    ))
    
    # Print system info
    console.print(f"[info]System: {platform.system()} {platform.version()}[/info]")
    console.print(f"[info]Python: {platform.python_version()}[/info]")
    console.print(f"[info]Working directory: {os.getcwd()}[/info]")
    console.print()


def handle_code_blocks(response: str, state: Dict[str, Any]) -> str:
    """
    Process and format code blocks in the response.
    
    Args:
        response: The text response containing code blocks
        state: The application state dictionary
        
    Returns:
        Formatted response with highlighted code blocks
    """
    # Parse code blocks
    code_blocks = parse_code_blocks(response)
    
    if not code_blocks:
        return response
        
    # Replace code blocks with Rich syntax highlighted versions
    result = response
    for i, block in enumerate(code_blocks):
        language = block["language"] or "text"
        code = block["code"]
        
        # Format for displaying
        code_display = f"\n```{language}\n{code}\n```\n"
        
        # Add execution info
        if state.get("debug", False):
            console.print(f"[info]Code Block {i+1} ({language}):[/info]")
            console.print(Syntax(code, language, theme="monokai", line_numbers=True))
            
            # Ask if user wants to execute the code
            if Confirm.ask(f"Execute this {language} code block?"):
                exec_result = execute_code_block(block, state)
                console.print("\n[bold]Execution Result:[/bold]")
                console.print(exec_result)
    
    return result


@app.command()
def run(
    command: List[str] = typer.Argument(
        None,
        help="Command to execute. If not provided, interactive mode is started.",
    ),
    interactive: bool = typer.Option(
        True, "--interactive", "-i", help="Start in interactive mode."
    ),
    debug: bool = typer.Option(
        False, "--debug", "-d", help="Enable debug mode with verbose output."
    ),
    api_key: Optional[str] = typer.Option(
        None, "--api-key", "-k", help="Gemini API key (overrides environment variable)."
    ),
):
    """
    Run a command or start an interactive session with Datash.
    """
    # Initialize application state
    state = initialize_app_state(debug)
    
    # Set API key if provided
    if api_key:
        state["gemini_client"] = GeminiClient(api_key=api_key)
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, lambda sig, frame: _handle_exit(state))
    
    if debug:
        console.print("[warning]Debug mode enabled[/warning]")
        logging.getLogger().setLevel(logging.DEBUG)
    
    if command and not interactive:
        # Non-interactive mode: execute the command and exit
        cmd_str = " ".join(command)
        _handle_command(cmd_str, state)
        return
    
    # Interactive mode with prompt_toolkit
    _start_interactive_shell(state)


def _start_interactive_shell(state: Dict[str, Any]):
    """
    Start the interactive shell session with prompt_toolkit.
    
    Args:
        state: The application state dictionary
    """
    # Set up history file
    history_file = setup_history_file()
    
    try:
        # Create prompt session with history and auto-suggestion
        session = PromptSession(
            history=FileHistory(str(history_file)),
            auto_suggest=AutoSuggestFromHistory(),
            key_bindings=kb,
            style=DATASH_STYLE,
            completer=DatashCompleter(state),
            complete_in_thread=True,
            complete_while_typing=True,
        )
        
        # Display welcome message
        display_welcome_message()
        
        # Main interaction loop
        while True:
            try:
                # Get input from user with formatted prompt
                cwd = os.path.basename(state["working_directory"])
                prompt_text = HTML(f'<prompt>{cwd} datash></prompt> ')
                
                user_input = session.prompt(
                    prompt_text,
                    rprompt=_get_rprompt(state),
                )
                
                # Skip empty input
                if not user_input.strip():
                    continue
                    
                # Check for exit command
                if user_input.lower() in ("exit", "quit"):
                    _handle_exit(state)
                    break
                    
                # Process the command
                _handle_command(user_input, state)
                
                # Increment command count
                state["command_count"] += 1
                
            except KeyboardInterrupt:
                console.print("\n[warning]Interrupted. Use 'exit' to quit.[/warning]")
            except EOFError:
                _handle_exit(state)
                break
            except Exception as e:
                _handle_error(e, state)
                
    except Exception as e:
        console.print(f"[error]Error in interactive shell: {str(e)}[/error]")
        if state.get("debug", False):
            console.print(traceback.format_exc())
        return


def _get_rprompt(state: Dict[str, Any]) -> Optional[HTML]:
    """
    Get the right-side prompt text based on state.
    
    Args:
        state: The application state
        
    Returns:
        HTML formatted text for right prompt or None
    """
    if state.get("current_db_type"):
        return HTML(f'<ansired>{state["current_db_type"]}</ansired>')
    return None


def _handle_exit(state: Dict[str, Any]):
    """
    Handle application exit with cleanup.
    
    Args:
        state: The application state
    """
    # Calculate session duration
    duration = time.time() - state["session_start_time"]
    minutes, seconds = divmod(int(duration), 60)
    hours, minutes = divmod(minutes, 60)
    
    # Display goodbye message with stats
    console.print("\n[warning]Exiting Datash...[/warning]")
    console.print(f"Session duration: {hours:02d}:{minutes:02d}:{seconds:02d}")
    console.print(f"Commands executed: {state['command_count']}")
    console.print("[success]Goodbye![/success]")


def _handle_error(error: Exception, state: Dict[str, Any]):
    """
    Handle and display errors appropriately.
    
    Args:
        error: The exception that occurred
        state: The application state
    """
    if state.get("debug", False):
        console.print(f"[error]Error: {str(error)}[/error]")
        console.print(traceback.format_exc())
    else:
        console.print(f"[error]Error: {str(error)}[/error]")
        
    logger.error(f"Error: {str(error)}", exc_info=True)


def _handle_command(command: str, state: Dict[str, Any]):
    """
    Process a command and display the result.
    
    Args:
        command: The command to process
        state: The application state
    """
    if not command.strip():
        return
        
    # Log the command
    logger.info(f"Command: {command}")
    
    # Add command to history
    state["history"].append(command)
    
    # Get command category for better handling
    category = get_command_category(command)
    if category:
        console.print(f"[dim][Category: {category}][/dim]")
    
    try:
        # Start timing the command execution
        start_time = time.time()
        
        # First, try to process command locally if it's a built-in command
        result = process_command(command, state)
        
        if result:
            console.print(result)
            # Calculate execution time
            exec_time = time.time() - start_time
            if state.get("debug", False):
                console.print(f"[dim]Execution time: {exec_time:.3f}s[/dim]")
            return
            
        # If not a built-in command, send to Gemini API
        console.print("[info]Processing with AI...[/info]")
        
        response = state["gemini_client"].get_response(
            command, 
            history=state["history"][-10:] if len(state["history"]) > 1 else []
        )
        
        # Handle and format code blocks
        formatted_response = handle_code_blocks(response, state)
        
        # Display the response
        console.print(Markdown(formatted_response))
        
        # Calculate execution time
        exec_time = time.time() - start_time
        if state.get("debug", False):
            console.print(f"[dim]Execution time: {exec_time:.3f}s[/dim]")
        
        # Suggest next action
        suggestion = suggest_next_action(command, response, state)
        if suggestion:
            console.print(f"\n[suggestion]Suggestion: {suggestion}[/suggestion]")
        
    except KeyboardInterrupt:
        console.print("\n[warning]Command interrupted[/warning]")
    except Exception as e:
        _handle_error(e, state)


def execute_cli_command(command: List[str], state: Dict[str, Any]) -> None:
    """
    Execute a CLI command (non-interactive mode).
    
    Args:
        command: List of command arguments
        state: The application state
    """
    # Join command parts
    cmd_str = " ".join(command)
    
    # Process the command
    _handle_command(cmd_str, state)


if __name__ == "__main__":
    # Ensure Python 3.7+
    if sys.version_info < (3, 7):
        console.print("[error]Error: Python 3.7 or higher is required.[/error]")
        sys.exit(1)
    
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[warning]Interrupted. Exiting...[/warning]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[error]Unhandled error: {str(e)}[/error]")
        logger.error("Unhandled error", exc_info=True)
        sys.exit(1)
