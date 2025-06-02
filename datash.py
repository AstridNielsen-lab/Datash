#!/usr/bin/env python3
"""
Datash - An intelligent terminal assistant for programmers.

This module serves as the main entry point for the Datash application,
providing an interactive shell interface for interacting with the assistant.
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
from rich.live import Live
from rich.text import Text
from rich.align import Align
from rich.style import Style as RichStyle
from rich.color import Color
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


class AnimatedCatSpiderWeb:
    """Class to display an animated ASCII art of a cat playing with spider webs."""
    
    def __init__(self, console: Console):
        """
        Initialize the animation.
        
        Args:
            console: The Rich console to display on
        """
        self.console = console
        self.frames = self._get_animation_frames()
        
    def _get_animation_frames(self) -> List[str]:
        """
        Get the animation frames.
        
        Returns:
            List of animation frames as strings
        """
        # Frame 1: Cat approaching the spider web
        frame1 = r"""
          /\_/\           ╭─────────╮
         ( o.o )          │ ╲     / │
          > ^ <           │  ╲   /  │
                          │   ╲ /   │
                          │   / ╲   │
                          │  /   ╲  │
                          │ /     ╲ │
                          ╰─────────╯
        """
        
        # Frame 2: Cat touching the web
        frame2 = r"""
                          ╭─────────╮
          /\_/\           │ ╲     / │
         ( o.o )~         │  ╲   /  │
          > ^ <           │   ╲ /   │
                          │   / ╲   │
                          │  /   ╲  │
                          │ /     ╲ │
                          ╰─────────╯
        """
        
        # Frame 3: Cat's paw caught in web
        frame3 = r"""
                          ╭─────────╮
          /\_/\           │ ╲     / │
         ( o.o )~~~~~~~~~>│  ╲   /  │
          > ^ <           │   ╲ /   │
                          │   / ╲   │
                          │  /   ╲  │
                          │ /     ╲ │
                          ╰─────────╯
        """
        
        # Frame 4: Cat playing with web
        frame4 = r"""
                          ╭─────────╮
          /\_/\           │ ╲     / │
         ( o~o )~~~~~~~~~>│  ╲   /  │
          > ^ <           │   ╲ /   │
                          │   / ╲   │
                          │  /   ╲  │
                          │ /     ╲ │
                          ╰─────────╯
        """
        
        # Frame 5: Web starting to unravel
        frame5 = r"""
                          ╭────────╮
          /\_/\           │ ╲     /
         ( o~o )~~~~~~~~~>│  ╲   / │
          > ^ <           │   ╲ /  │
                          │   / ╲  │
                          │  /   ╲ │
                          │ /     ╲│
                          ╰────────╯
        """
        
        # Frame 6: Web more unraveled
        frame6 = r"""
                          ╭───────
          /\_/\           │ ╲     
         ( ^.^ )~~~~~~~~~>│  ╲    │
          > ^ <           │   ╲   │
                          │    ╲  │
                          │     ╲ │
                          │      ╲│
                          ╰───────╯
        """
        
        # Frame 7: Web mostly gone
        frame7 = r"""
                          ╭──
          /\_/\           │   
         ( ^.^ )~~~~~o    │    
          > ^ <           │     
                          │      
                          │       
                          │        
                          ╰──
        """
        
        # Frame 8: Cat happy with the ball of web
        frame8 = r"""
        
          /\_/\              
         ( ^.^ )  ~~o~~      
          > ^ <              
                            
        ★ ★ ★  DATASH!  ★ ★ ★
                            
        """
        
        return [frame1, frame2, frame3, frame4, frame5, frame6, frame7, frame8]
        
    def play(self, duration: float = 0.6, cycles: int = 1):
        """
        Play the animation.
        
        Args:
            duration: Time between frames in seconds
            cycles: Number of animation cycles
        """
        try:
            # Prepare console
            self._prepare_console()
            
            # Show loading message
            self.console.print("[bold magenta]Loading Datash...[/bold magenta]")
            time.sleep(0.5)  # Brief pause before animation
            
            # Try to use Rich's Live display first (preferred method)
            try:
                with Live(self._render_frame(0), console=self.console, refresh_per_second=4, screen=True) as live:
                    for cycle in range(cycles):
                        for i, frame in enumerate(self.frames):
                            live.update(self._render_frame(i))
                            time.sleep(duration)
                    
                    # Pause on the last frame for a moment
                    time.sleep(0.7)
            except Exception as inner_e:
                # Fallback to simpler animation method
                logger.warning(f"Using fallback animation method: {str(inner_e)}")
                self._play_fallback(duration, cycles)
                
        except Exception as e:
            # Log the error but continue execution
            logger.error(f"Animation error: {str(e)}", exc_info=True if logger.level <= logging.DEBUG else False)
            # Don't let animation errors prevent the app from starting
            pass
    
    def _prepare_console(self):
        """Prepare the console for animation display."""
        # Clear the console first
        try:
            self.console.clear()
        except Exception:
            # Fallback to os.system clear if console.clear() fails
            if platform.system() == "Windows":
                os.system("cls")
            else:
                os.system("clear")
        
        # Windows specific console mode
        if platform.system() == "Windows":
            try:
                # Try to enable VT100 sequences on Windows
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            except Exception:
                # If it fails, continue anyway
                pass
    
    def _play_fallback(self, duration: float, cycles: int):
        """Fallback animation method for terminals that don't support Rich's Live display."""
        for cycle in range(cycles):
            for i, frame in enumerate(self.frames):
                # Clear screen before each frame
                try:
                    self.console.clear()
                except Exception:
                    # Fallback clear
                    if platform.system() == "Windows":
                        os.system("cls")
                    else:
                        os.system("clear")
                        
                # Print the frame
                panel = self._render_frame(i)
                self.console.print(panel)
                time.sleep(duration)
    
    def _render_frame(self, frame_index: int) -> Panel:
        """
        Render a specific animation frame.
        
        Args:
            frame_index: Index of the frame to render
            
        Returns:
            Panel containing the rendered frame
        """
        frame = self.frames[frame_index]
        
        # Style the cat, web, and text differently
        styled_frame = frame
        
        # Create a richly styled text object
        text = Text()
        
        # Apply different styles to different parts of the frame
        for line in styled_frame.split('\n'):
            # Cat styling - using hardcoded pattern matching to avoid escape sequence issues
            if '/\\' in line or '(' in line or ')' in line or '>' in line:
                # Cat face patterns
                cat_line = line
                if '/\\_/\\' in line:
                    cat_line = cat_line.replace('/\\_/\\', '[bold yellow]/\\_/\\[/bold yellow]')
                cat_line = cat_line.replace('( o.o )', '[bold yellow]([/bold yellow][bright_white] o.o [/bright_white][bold yellow])[/bold yellow]')
                cat_line = cat_line.replace('( o~o )', '[bold yellow]([/bold yellow][bright_white] o~o [/bright_white][bold yellow])[/bold yellow]')
                cat_line = cat_line.replace('( ^.^ )', '[bold yellow]([/bold yellow][bright_white] ^.^ [/bright_white][bold yellow])[/bold yellow]')
                cat_line = cat_line.replace('> ^ <', '[bold yellow]> ^ <[/bold yellow]')
                cat_line = cat_line.replace('~', '[bright_cyan]~[/bright_cyan]')
                cat_line = cat_line.replace('~~o~~', '[bright_cyan]~~[/bright_cyan][bright_white]o[/bright_white][bright_cyan]~~[/bright_cyan]')
                text.append(cat_line + '\n')
            # Web styling
            elif any(web_part in line for web_part in ['╭', '╮', '│', '╯', '╰', '/']):
                web_line = line
                for char in ['╭', '╮', '│', '╯', '╰', '\\', '/', '─', '╲', '╱']:
                    web_line = web_line.replace(char, f'[bright_white]{char}[/bright_white]')
                text.append(web_line + '\n')
            # DATASH styling
            elif 'DATASH' in line:
                text.append('[bold bright_green]' + line + '[/bold bright_green]\n')
            # Stars styling
            elif '★' in line:
                text.append('[bold bright_yellow]' + line + '[/bold bright_yellow]\n')
            # Default styling
            else:
                text.append(line + '\n')
        
        return Panel(
            Align.center(text),
            title="[bold bright_magenta]Cat vs Spider Web[/bold bright_magenta]",
            title_align="center",
            border_style="bright_blue",
            padding=(1, 2),
            width=60
        )


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


def display_welcome_animation():
    """Display the welcome animation of a cat playing with spider webs."""
    try:
        # Clear the console first for a clean animation
        try:
            console.clear()
        except Exception:
            # Fallback to os.system clear
            if platform.system() == "Windows":
                os.system("cls")
            else:
                os.system("clear")
        
        # Create and play the animation
        animation = AnimatedCatSpiderWeb(console)
        animation.play(duration=0.6, cycles=1)
        
        # Wait a moment before clearing
        time.sleep(0.3)
        
        # Clear the screen before showing the welcome message
        try:
            console.clear()
        except Exception:
            # Fallback to os.system clear
            if platform.system() == "Windows":
                os.system("cls")
            else:
                os.system("clear")
        
    except Exception as e:
        # Log the error but continue without the animation
        logger.error(f"Animation error: {str(e)}")
        # Clear any partial animation
        if platform.system() == "Windows":
            os.system("cls")
        else:
            os.system("clear")


def display_welcome_message():
    """Display the welcome message for Datash."""
    try:
        # Show the welcome animation first
        display_welcome_animation()
    except Exception as e:
        # If animation fails, just clear the screen
        logger.error(f"Welcome animation failed: {str(e)}")
        console.clear()
    
    # Display the main welcome panel
    console.print(Panel.fit(
        "[bold blue]Datash[/bold blue] - [italic]Data + Shell + Intelligence[/italic]\n\n"
        "An intelligent terminal assistant for programmers.\n"
        "Type [bold]help[/bold] for a list of commands or [bold]exit[/bold] to quit.",
        title="Welcome",
        title_align="center",
        border_style="blue",
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
        
        # Display welcome message with animation
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
