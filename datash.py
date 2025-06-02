#!/usr/bin/env python3
"""
Datash - An intelligent terminal assistant for programmers.

This module serves as the main entry point for the Datash application,
providing an interactive shell interface for interacting with the assistant.

The AI assistant has expertise in penetration testing (pentest) and security assessments,
helping users with security testing, providing guidance on secure practices, and
assisting with technical security analysis. All security testing must be performed
ethically and only on systems where you have explicit permission.

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

# Voice interaction imports
# These are wrapped in try/except to allow graceful fallback
try:
    import speech_recognition as sr
    import pyttsx3
    VOICE_SUPPORT = True
except ImportError:
    VOICE_SUPPORT = False

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
    help="Datash - Data + Shell + Intelligence: A terminal assistant for programmers with expertise in pentesting and security assessments.",
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
    "voice_enabled": False,  # Flag to enable/disable voice interaction
    "voice_engine": None,    # Will store the text-to-speech engine
    "voice_recognizer": None, # Will store the speech recognition engine
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
          /\_/\           +------------+
         ( o.o )          |  \      /  |
          > ^ <           |   \    /   |
                          |    \  /    |
                          |    /  \    |
                          |   /    \   |
                          |  /      \  |
                          +------------+
        """
        
        # Frame 2: Cat touching the web
        frame2 = r"""
                          +------------+
          /\_/\           |  \      /  |
         ( o.o )~         |   \    /   |
          > ^ <           |    \  /    |
                          |    /  \    |
                          |   /    \   |
                          |  /      \  |
                          +------------+
        """
        
        # Frame 3: Cat's paw caught in web
        frame3 = r"""
                          +------------+
          /\_/\           |  \      /  |
         ( o.o )~~~~~~~-->|   \    /   |
          > ^ <           |    \  /    |
                          |    /  \    |
                          |   /    \   |
                          |  /      \  |
                          +------------+
        """
        
        # Frame 4: Cat playing with web
        frame4 = r"""
                          +------------+
          /\_/\           |  \      /  |
         ( o~o )~~~~~~~-->|   \    /   |
          > ^ <           |    \  /    |
                          |    /  \    |
                          |   /    \   |
                          |  /      \  |
                          +------------+
        """
        
        # Frame 5: Web starting to unravel
        frame5 = r"""
                          +----------+
          /\_/\           |  \      /
         ( o~o )~~~~~~~-->|   \    /  |
          > ^ <           |    \  /   |
                          |    /  \   |
                          |   /    \  |
                          |  /      \ |
                          +----------+
        """
        
        # Frame 6: Web more unraveled
        frame6 = r"""
                          +-------+
          /\_/\           |  \     
         ( ^.^ )~~~~~~~-->|   \    |
          > ^ <           |    \   |
                          |     \  |
                          |      \ |
                          |       \|
                          +-------+
        """
        
        # Frame 7: Web mostly gone
        frame7 = r"""
                          +--+
          /\_/\           |   
         ( ^.^ )~~~~~o    |    
          > ^ <           |     
                          |      
                          |       
                          |        
                          +--+
        """
        
        # Frame 8: Cat happy with contact information
        frame8 = r"""

          /\_/\              
         ( ^.^ )  ~~o~~      
          > ^ <              
                            
    +--------------------------------+
    |     Julio Campos Machado       |
    |   Founder CTO Full Stack Dev   |
    |--------------------------------|
    | WhatsApp: +55 11 97060-3441   |
    | Email: juliocamposmachado@     |
    |        gmail.com               |
    |--------------------------------|
    | Like Look Solutions            |
    | likelook.wixsite.com/solutions|
    |--------------------------------|
    | LinkedIn: /juliocamposmachado  |
    | Social: linktr.ee/             |
    |         juliocamposmachado     |
    +--------------------------------+
        """
        
        return [frame1, frame2, frame3, frame4, frame5, frame6, frame7, frame8]
        
    def play(self, duration: float = 0.7, cycles: int = 1):
        """
        Play the animation.
        
        Args:
            duration: Time between frames in seconds
            cycles: Number of animation cycles
        """
        try:
            # Check if we're in Windows PowerShell or CMD
            is_windows = platform.system() == "Windows"
            
            # Prepare console
            self._prepare_console()
            
            # Show loading message
            self.console.print("[bold magenta]Loading Datash...[/bold magenta]")
            time.sleep(0.5)  # Brief pause before animation
            
            # For Windows, always use the fallback method which works better
            if is_windows:
                self._play_windows_friendly(duration, cycles)
            else:
                # Try to use Rich's Live display first (preferred method) on Unix systems
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
            
    def _play_windows_friendly(self, duration: float, cycles: int):
        """
        Windows-friendly animation method that works in PowerShell and CMD.
        
        Args:
            duration: Time between frames in seconds
            cycles: Number of animation cycles
        """
        # For PowerShell, we'll just print each frame individually with clearing in between
        frames_with_colors = [self._simple_colorize_frame(frame) for frame in self.frames]
        
        for cycle in range(cycles):
            for colored_frame in frames_with_colors:
                # Clear screen
                os.system("cls")
                
                # Print the colored frame
                print("\n\n")  # Add some padding
                print(colored_frame)
                print("\n")
                
                # Wait before showing next frame - longer for contact info frame
                if colored_frame == frames_with_colors[-1]:  # Last frame with contact info
                    time.sleep(duration * 4.0)  # Much longer pause for contact information
                else:
                    time.sleep(duration)
    
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
                
    def _simple_colorize_frame(self, frame: str) -> str:
        """
        Apply simple ANSI color codes to the frame for Windows compatibility.
        
        Args:
            frame: The frame to colorize
            
        Returns:
            Colorized frame with ANSI escape codes
        """
        # Define ANSI color codes
        YELLOW = "\033[33m"
        CYAN = "\033[36m"
        GREEN = "\033[32m"
        BRIGHT_WHITE = "\033[97m"
        BLUE = "\033[34m"
        MAGENTA = "\033[35m"
        RED = "\033[31m"
        RESET = "\033[0m"
        
        # Colorize the frame line by line
        colorized_lines = []
        for line in frame.split('\n'):
            # Cat face coloring
            if '/\\_/\\' in line:
                line = line.replace('/\\_/\\', f"{YELLOW}/\\_/\\{RESET}")
            if '( o.o )' in line:
                line = line.replace('( o.o )', f"{YELLOW}({RESET}{BRIGHT_WHITE} o.o {RESET}{YELLOW}){RESET}")
            if '( o~o )' in line:
                line = line.replace('( o~o )', f"{YELLOW}({RESET}{BRIGHT_WHITE} o~o {RESET}{YELLOW}){RESET}")
            if '( ^.^ )' in line:
                line = line.replace('( ^.^ )', f"{YELLOW}({RESET}{BRIGHT_WHITE} ^.^ {RESET}{YELLOW}){RESET}")
            if '> ^ <' in line:
                line = line.replace('> ^ <', f"{YELLOW}> ^ <{RESET}")
                
            # Web coloring
            if '+--' in line or '--+' in line or '|' in line:
                line = line.replace('+', f"{CYAN}+{RESET}")
                line = line.replace('-', f"{CYAN}-{RESET}")
                line = line.replace('|', f"{CYAN}|{RESET}")
                line = line.replace('\\', f"{CYAN}\\{RESET}")
                line = line.replace('/', f"{CYAN}/{RESET}")
                
            # Special elements
            if '~' in line:
                line = line.replace('~', f"{CYAN}~{RESET}")
            if 'o' in line and ('~' in line or '~~o~~' in line):
                line = line.replace('o', f"{BRIGHT_WHITE}o{RESET}")
            if 'DATASH' in line:
                line = line.replace('DATASH!', f"{GREEN}DATASH!{RESET}")
            if '*' in line:
                line = line.replace('*', f"{YELLOW}*{RESET}")
                
            # Contact information styling
            if 'Julio Campos Machado' in line:
                line = line.replace('Julio Campos Machado', f"{MAGENTA}Julio Campos Machado{RESET}")
            if 'Founder CTO Full Stack Dev' in line:
                line = line.replace('Founder CTO Full Stack Dev', f"{YELLOW}Founder CTO Full Stack Dev{RESET}")
            if 'WhatsApp:' in line:
                line = line.replace('WhatsApp:', f"{GREEN}WhatsApp:{RESET}")
                line = line.replace('+55 11 97060-3441', f"{BRIGHT_WHITE}+55 11 97060-3441{RESET}")
            if 'Email:' in line:
                line = line.replace('Email:', f"{GREEN}Email:{RESET}")
                if 'juliocamposmachado@' in line:
                    line = line.replace('juliocamposmachado@', f"{BRIGHT_WHITE}juliocamposmachado@{RESET}")
                if 'gmail.com' in line:
                    line = line.replace('gmail.com', f"{BRIGHT_WHITE}gmail.com{RESET}")
            if 'Like Look Solutions' in line:
                line = line.replace('Like Look Solutions', f"{CYAN}Like Look Solutions{RESET}")
            if 'likelook.wixsite.com/solutions' in line:
                line = line.replace('likelook.wixsite.com/solutions', f"{BRIGHT_WHITE}likelook.wixsite.com/solutions{RESET}")
            if 'LinkedIn:' in line:
                line = line.replace('LinkedIn:', f"{BLUE}LinkedIn:{RESET}")
                if '/juliocamposmachado' in line:
                    line = line.replace('/juliocamposmachado', f"{BRIGHT_WHITE}/juliocamposmachado{RESET}")
            if 'Social:' in line:
                line = line.replace('Social:', f"{CYAN}Social:{RESET}")
                if 'linktr.ee/' in line:
                    line = line.replace('linktr.ee/', f"{BRIGHT_WHITE}linktr.ee/{RESET}")
                if 'juliocamposmachado' in line:
                    line = line.replace('juliocamposmachado', f"{BRIGHT_WHITE}juliocamposmachado{RESET}")
                
            colorized_lines.append(line)
            
        return '\n'.join(colorized_lines)
    
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
            # Web styling - using basic ASCII characters now
            elif any(web_part in line for web_part in ['+', '-', '|', '\\']):
                web_line = line
                for char in ['+', '-', '|', '\\', '/', ' ']:
                    if char != ' ':  # Don't style spaces
                        web_line = web_line.replace(char, f'[bright_white]{char}[/bright_white]')
                text.append(web_line + '\n')
            # DATASH styling
            elif 'DATASH' in line:
                text.append('[bold bright_green]' + line + '[/bold bright_green]\n')
            # Stars/asterisks styling
            elif '*' in line:
                text.append('[bold bright_yellow]' + line + '[/bold bright_yellow]\n')
            # Contact information styling
            elif 'Julio Campos Machado' in line:
                text.append('[bold magenta]' + line + '[/bold magenta]\n')
            elif 'Founder CTO' in line:
                text.append('[bold yellow]' + line + '[/bold yellow]\n')
            elif 'WhatsApp:' in line or 'Email:' in line:
                text.append('[green]' + line + '[/green]\n')
            elif 'Like Look Solutions' in line:
                text.append('[bold cyan]' + line + '[/bold cyan]\n')
            elif 'likelook.wixsite.com' in line:
                text.append('[bright_blue]' + line + '[/bright_blue]\n')
            elif 'LinkedIn:' in line or 'Social:' in line:
                text.append('[blue]' + line + '[/blue]\n')
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


def initialize_voice_support(state: Dict[str, Any]) -> bool:
    """
    Initialize voice support if available and enabled.
    
    Args:
        state: The application state dictionary
        
    Returns:
        True if voice support was successfully initialized, False otherwise
    """
    if not state.get("voice_enabled", False):
        return False
        
    if not VOICE_SUPPORT:
        console.print("[warning]Voice support requested but required packages are not installed.[/warning]")
        console.print("[info]Install with: pip install SpeechRecognition pyttsx3 PyAudio[/info]")
        return False
        
    try:
        # Initialize speech recognition
        recognizer = sr.Recognizer()
        state["voice_recognizer"] = recognizer
        
        # Initialize text-to-speech engine
        engine = pyttsx3.init()
        state["voice_engine"] = engine
        
        # Configure voice properties (can be customized further)
        voices = engine.getProperty('voices')
        # Default to first available voice
        if voices:
            engine.setProperty('voice', voices[0].id)
        
        # Set speaking rate (words per minute)
        engine.setProperty('rate', 180)
        
        console.print("[success]Voice support initialized successfully[/success]")
        return True
    except Exception as e:
        console.print(f"[error]Failed to initialize voice support: {str(e)}[/error]")
        state["voice_enabled"] = False
        return False


def initialize_app_state(debug: bool = False, voice_enabled: bool = False, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Initialize the application state."""
    # Start with base state
    state = APP_STATE.copy()
    
    # Set debug mode
    state["debug"] = debug
    
    # Set voice enabled flag
    state["voice_enabled"] = voice_enabled
    
    # Initialize command history
    state["command_history"] = CommandHistory()
    
    # Initialize Gemini client
    state["gemini_client"] = GeminiClient(api_key=api_key)
    
    # Ensure working directory is set
    if not state["working_directory"]:
        state["working_directory"] = os.getcwd()
    
    # Initialize voice support if enabled
    if voice_enabled:
        initialize_voice_support(state)
    
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
        
        # Use different animation settings depending on platform
        if platform.system() == "Windows":
            # Windows needs longer duration for smoother animation
            animation.play(duration=0.8, cycles=1)
        else:
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
        "Expert in [bold red]penetration testing[/bold red] and [bold red]security assessments[/bold red].\n"
        "Assists with security testing, secure practices guidance, and technical analysis.\n"
        "[italic yellow]Note: All security testing must be ethical and performed only on systems where you have explicit permission.[/italic yellow]\n\n"
        "Type [bold]help[/bold] for a list of commands or [bold]exit[/bold] to quit.",
        title="Welcome",
        title_align="center",
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
    voice: bool = typer.Option(
        False, "--voice", "-v", help="Enable voice interaction for input and output."
    ),
):
    """
    Run a command or start an interactive session with Datash.
    """
    # Ask for voice assistance if not specified and in interactive mode
    if interactive and not command and voice is False:
        try:
            voice = Confirm.ask("Would you like to enable voice assistance?", default=False)
        except Exception:
            # If there's an error with rich's Confirm (e.g., in certain terminals), default to no
            voice = False
    
    # Ask for custom API key if not provided
    custom_api_key = api_key
    if interactive and not command and not api_key:
        try:
            use_custom_key = Confirm.ask("Would you like to use your own Gemini API key?", default=False)
            if use_custom_key:
                custom_api_key = Prompt.ask("Enter your Gemini API key", password=True)
        except Exception:
            # If there's an error with rich's Prompt, default to environment variable
            pass
    
    # Initialize application state
    state = initialize_app_state(debug, voice, custom_api_key)
    
    # Voice welcome if enabled
    if state.get("voice_enabled", False) and state.get("voice_engine") is not None:
        try:
            state["voice_engine"].say("Welcome to Datash, voice assistance is enabled.")
            state["voice_engine"].runAndWait()
        except Exception as e:
            console.print(f"[warning]Voice output error: {str(e)}[/warning]")
    
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
                
                # Check if we should use voice input
                if state.get("voice_enabled", False) and state.get("voice_recognizer") is not None:
                    # Prompt for voice input
                    console.print("[info]Listening for voice command... (Speak now)[/info]")
                    
                    try:
                        # Voice input
                        user_input = get_voice_input(state)
                        if user_input:
                            console.print(f"[bold cyan]Voice command:[/bold cyan] {user_input}")
                        else:
                            console.print("[warning]Could not understand audio. Please try again.[/warning]")
                            continue
                    except Exception as e:
                        console.print(f"[error]Voice input error: {str(e)}[/error]")
                        # Fall back to text input
                        user_input = session.prompt(
                            prompt_text,
                            rprompt=_get_rprompt(state),
                        )
                else:
                    # Regular text input
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

def get_voice_input(state: Dict[str, Any]) -> str:
    """
    Get input from the user via voice recognition.
    
    Args:
        state: The application state dictionary
        
    Returns:
        The recognized text from speech, or empty string if failed
    """
    if not VOICE_SUPPORT or not state.get("voice_recognizer"):
        return ""
        
    try:
        # Use the microphone as source
        with sr.Microphone() as source:
            # Adjust for ambient noise
            state["voice_recognizer"].adjust_for_ambient_noise(source, duration=0.5)
            
            # Listen for the user's input
            audio = state["voice_recognizer"].listen(source, timeout=5, phrase_time_limit=10)
            
            # Use Google Speech Recognition
            text = state["voice_recognizer"].recognize_google(audio)
            return text
    except sr.WaitTimeoutError:
        console.print("[warning]Listening timed out. Please try again.[/warning]")
        return ""
    except sr.UnknownValueError:
        return ""  # Speech was unintelligible
    except sr.RequestError:
        console.print("[error]Could not request results from Google Speech Recognition service.[/error]")
        return ""
    except Exception as e:
        console.print(f"[error]Voice recognition error: {str(e)}[/error]")
        return ""


def speak_text(text: str, state: Dict[str, Any]):
    """
    Convert text to speech and speak it.
    
    Args:
        text: The text to speak
        state: The application state dictionary
    """
    if not state.get("voice_enabled") or not state.get("voice_engine"):
        return
        
    try:
        # Remove markdown formatting and simplify text for speech
        text = re.sub(r'\[.*?\]', '', text)  # Remove Rich formatting tags
        text = re.sub(r'```.*?```', 'Code block omitted', text, flags=re.DOTALL)  # Replace code blocks
        text = re.sub(r'\s+', ' ', text)  # Collapse whitespace
        
        # Limit length to prevent very long outputs
        if len(text) > 1000:
            text = text[:1000] + "... Content truncated for voice output."
            
        # Convert to speech
        state["voice_engine"].say(text)
        state["voice_engine"].runAndWait()
    except Exception as e:
        console.print(f"[warning]Text-to-speech error: {str(e)}[/warning]")


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
        console.print("[info]Processing with AI security expert...[/info]")
        
        response = state["gemini_client"].get_response(
            command, 
            history=state["history"][-10:] if len(state["history"]) > 1 else []
        )
        
        # Handle and format code blocks
        formatted_response = handle_code_blocks(response, state)
        
        # Display the response
        console.print(Markdown(formatted_response))
        
        # If voice is enabled, speak the response
        if state.get("voice_enabled", False):
            speak_text(response, state)
        
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
