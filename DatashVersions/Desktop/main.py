#!/usr/bin/env python3
"""
Datash - Data + Shell + Intelligence

A terminal-based assistant for programmers that helps with data processing,
database operations, Git commands, and more. Powered by Google's Gemini API.

This file serves as the main entry point for the Datash application.
"""

import os
import sys
import json
import argparse
import requests
import logging
import readline
import subprocess
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from colorama import init, Fore, Style

# Initialize colorama for cross-platform colored terminal text
init()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("datash.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("datash")

# Default configuration
DEFAULT_CONFIG = {
    "api_url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent",
    "history_file": os.path.expanduser("~/.datash_history"),
    "max_history": 100,
    "display_suggestions": True,
}

class DatashConfig:
    """Configuration manager for Datash application."""
    
    def __init__(self):
        """Initialize configuration with environment variables and defaults."""
        # Load environment variables from .env file if it exists
        load_dotenv()
        
        self.config = DEFAULT_CONFIG.copy()
        self.api_key = os.environ.get("DATASH_API_KEY") or os.environ.get("GEMINI_API_KEY")
        
        # Load config file if it exists
        config_path = os.path.expanduser("~/.datash_config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    self.config.update(user_config)
            except Exception as e:
                logger.warning(f"Failed to load config file: {e}")
    
    def get(self, key: str, default=None) -> Any:
        """Get a configuration value."""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self.config[key] = value
    
    def save(self) -> None:
        """Save configuration to file."""
        config_path = os.path.expanduser("~/.datash_config.json")
        try:
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Configuration saved to {config_path}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def validate(self) -> bool:
        """Validate configuration."""
        if not self.api_key:
            logger.error("API key not found. Please set DATASH_API_KEY environment variable.")
            print(f"{Fore.RED}Error: API key not found.{Style.RESET_ALL}")
            print("Please set the DATASH_API_KEY environment variable or add it to your .env file.")
            return False
        return True

class GeminiAPI:
    """Client for interacting with Google's Gemini API."""
    
    def __init__(self, config: DatashConfig):
        """Initialize the Gemini API client with configuration."""
        self.config = config
        self.api_url = config.get("api_url")
        self.api_key = config.api_key
        self.history = []
    
    def call_gemini(self, prompt: str) -> Optional[str]:
        """
        Call the Gemini API with the given prompt.
        
        Args:
            prompt: The prompt to send to the API
            
        Returns:
            The response text from the API or None if the call failed
        """
        try:
            headers = {
                "Content-Type": "application/json"
            }
            
            # Prepare context for the API
            context = "You are Datash, a terminal assistant for programmers. "
            context += "Help with database operations, data processing, Git commands, and shell scripts. "
            context += "Keep responses concise, focused on practical commands and code snippets."
            
            # Build prompt with context and conversation history
            full_prompt = context
            if self.history:
                full_prompt += "\n\nPrevious interactions:\n"
                for entry in self.history[-5:]:  # Include last 5 interactions for context
                    full_prompt += f"User: {entry['user']}\nAssistant: {entry['assistant']}\n"
            
            full_prompt += f"\nUser: {prompt}\nAssistant:"
            
            data = {
                "contents": [{
                    "parts": [{
                        "text": full_prompt
                    }]
                }]
            }
            
            response = requests.post(
                f"{self.api_url}?key={self.api_key}",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(f"API error: {response.status_code} - {response.text}")
                return None
                
            result = response.json()
            text_response = result["candidates"][0]["content"]["parts"][0]["text"]
            
            # Store the interaction in history
            self.history.append({
                "user": prompt,
                "assistant": text_response
            })
            
            return text_response
            
        except Exception as e:
            logger.error(f"API call failed: {e}")
            return None
    
    def suggest_next_action(self, context: str) -> Optional[str]:
        """Generate a suggestion for the next action based on context."""
        try:
            # Simplified suggestion request to minimize token usage
            prompt = f"Based on this command context: {context}\nSuggest ONE next possible action (one line only):"
            
            headers = {"Content-Type": "application/json"}
            data = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }]
            }
            
            response = requests.post(
                f"{self.api_url}?key={self.api_key}",
                headers=headers,
                json=data,
                timeout=10  # Shorter timeout for suggestions
            )
            
            if response.status_code != 200:
                return None
                
            result = response.json()
            suggestion = result["candidates"][0]["content"]["parts"][0]["text"]
            
            # Clean up the suggestion to keep it short
            suggestion = suggestion.strip().split('\n')[0]
            if len(suggestion) > 80:
                suggestion = suggestion[:77] + "..."
                
            return suggestion
            
        except Exception as e:
            logger.debug(f"Suggestion generation failed: {e}")
            return None

class CommandHandler:
    """Handles command execution and processing."""
    
    def __init__(self, config: DatashConfig, api: GeminiAPI):
        """Initialize with configuration and API client."""
        self.config = config
        self.api = api
        
    def execute_shell_command(self, command: str) -> str:
        """Execute a shell command and return the output."""
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                text=True, 
                capture_output=True,
                timeout=30
            )
            return result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return "Command execution timed out."
        except Exception as e:
            return f"Error executing command: {e}"
    
    def process_command(self, user_input: str) -> str:
        """Process user input and generate appropriate response."""
        # Check for built-in commands
        if user_input.startswith("!"):
            return self.handle_builtin_command(user_input[1:])
            
        # If it starts with $, treat as a shell command to execute
        if user_input.startswith("$"):
            return self.execute_shell_command(user_input[1:].strip())
            
        # Otherwise, send to Gemini API
        response = self.api.call_gemini(user_input)
        if response:
            return response
        else:
            return f"{Fore.RED}Failed to get response from API. Please check your connection and API key.{Style.RESET_ALL}"
    
    def handle_builtin_command(self, command: str) -> str:
        """Handle built-in Datash commands."""
        cmd_parts = command.strip().split()
        cmd = cmd_parts[0].lower() if cmd_parts else ""
        
        if cmd == "help":
            return self.show_help()
        elif cmd == "exit" or cmd == "quit":
            print("Exiting Datash. Goodbye!")
            sys.exit(0)
        elif cmd == "clear":
            os.system('cls' if os.name == 'nt' else 'clear')
            return ""
        elif cmd == "config":
            return self.handle_config_command(cmd_parts[1:])
        elif cmd == "version":
            return "Datash v0.1.0"
        elif cmd == "history":
            return self.show_history()
        else:
            return f"Unknown command: {cmd}. Type !help for available commands."
    
    def handle_config_command(self, args: List[str]) -> str:
        """Handle configuration-related commands."""
        if not args:
            # Show current configuration
            config_str = json.dumps(self.config.config, indent=2)
            return f"Current configuration:\n{config_str}"
        
        if args[0] == "set" and len(args) >= 3:
            key, value = args[1], args[2]
            try:
                # Try to convert to appropriate type
                if value.lower() == "true":
                    value = True
                elif value.lower() == "false":
                    value = False
                elif value.isdigit():
                    value = int(value)
                    
                self.config.set(key, value)
                self.config.save()
                return f"Configuration updated: {key} = {value}"
            except Exception as e:
                return f"Error updating configuration: {e}"
        
        return "Usage: !config [set KEY VALUE]"
    
    def show_help(self) -> str:
        """Display help information."""
        help_text = f"""
{Fore.GREEN}Datash - Terminal Assistant for Programmers{Style.RESET_ALL}

{Fore.YELLOW}Built-in commands:{Style.RESET_ALL}
  !help                 Show this help message
  !exit, !quit          Exit the application
  !clear                Clear the terminal screen
  !config               Show current configuration
  !config set KEY VALUE Update configuration
  !version              Show version information
  !history              Show command history

{Fore.YELLOW}Special syntax:{Style.RESET_ALL}
  $ command             Execute shell command directly
  
{Fore.YELLOW}Examples:{Style.RESET_ALL}
  Import CSV to SQLite:    import csv to sqlite database
  Git operations:          how to squash my last 3 commits
  Database query:          write a query to find duplicate records
  $ ls -la                 Execute 'ls -la' command

{Fore.YELLOW}Tips:{Style.RESET_ALL}
  - Be specific in your requests for better results
  - Use the shell execution prefix ($) for direct command execution
  - Configure your API key using environment variable DATASH_API_KEY
"""
        return help_text
    
    def show_history(self) -> str:
        """Show command history."""
        if not self.api.history:
            return "No command history available."
            
        history_text = f"{Fore.YELLOW}Command History:{Style.RESET_ALL}\n"
        for i, entry in enumerate(self.api.history, 1):
            history_text += f"{i}. User: {entry['user']}\n"
        
        return history_text

class DatashCLI:
    """Command-line interface for Datash."""
    
    def __init__(self):
        """Initialize the CLI with configuration and handlers."""
        self.config = DatashConfig()
        if not self.config.validate():
            sys.exit(1)
            
        self.api = GeminiAPI(self.config)
        self.command_handler = CommandHandler(self.config, self.api)
        
        # Set up readline for command history
        try:
            history_file = os.path.expanduser(self.config.get("history_file"))
            if os.path.exists(history_file):
                readline.read_history_file(history_file)
            readline.set_history_length(self.config.get("max_history"))
        except Exception as e:
            logger.warning(f"Could not set up command history: {e}")
    
    def parse_args(self) -> argparse.Namespace:
        """Parse command line arguments."""
        parser = argparse.ArgumentParser(
            description="Datash - A terminal assistant for programmers"
        )
        parser.add_argument(
            "--no-color", 
            action="store_true", 
            help="Disable colored output"
        )
        parser.add_argument(
            "--debug", 
            action="store_true", 
            help="Enable debug logging"
        )
        parser.add_argument(
            "--execute", "-e",
            help="Execute a single command and exit"
        )
        
        return parser.parse_args()
    
    def run(self):
        """Run the CLI interface."""
        args = self.parse_args()
        
        if args.debug:
            logging.getLogger().setLevel(logging.DEBUG)
        
        if args.no_color:
            # Disable colorama colors
            init(strip=True)
        
        print(f"{Fore.GREEN}Datash - Terminal Assistant for Programmers{Style.RESET_ALL}")
        print(f"Type {Fore.YELLOW}!help{Style.RESET_ALL} for available commands or {Fore.YELLOW}!exit{Style.RESET_ALL} to quit\n")
        
        # Handle single command execution
        if args.execute:
            result = self.command_handler.process_command(args.execute)
            print(result)
            return
        
        # Interactive mode
        while True:
            try:
                user_input = input(f"{Fore.CYAN}datash> {Style.RESET_ALL}")
                
                # Skip empty input
                if not user_input.strip():
                    continue
                    
                # Add to readline history
                readline.add_history(user_input)
                
                # Process the command
                result = self.command_handler.process_command(user_input)
                print(result)
                
                # Show suggestion if enabled
                if self.config.get("display_suggestions") and not user_input.startswith("!"):
                    suggestion = self.api.suggest_next_action(user_input)
                    if suggestion:
                        print(f"\n{Fore.BLUE}Suggestion: {suggestion}{Style.RESET_ALL}")
                
            except KeyboardInterrupt:
                print("\nUse !exit to quit")
            except EOFError:
                print("\nExiting Datash. Goodbye!")
                break
            except Exception as e:
                logger.error(f"Error: {e}")
                print(f"{Fore.RED}An error occurred: {e}{Style.RESET_ALL}")
        
        # Save readline history
        try:
            history_file = os.path.expanduser(self.config.get("history_file"))
            readline.write_history_file(history_file)
        except Exception as e:
            logger.warning(f"Could not save command history: {e}")

def main():
    """Main entry point for the application."""
    try:
        cli = DatashCLI()
        cli.run()
    except Exception as e:
        logger.critical(f"Application failed: {e}")
        print(f"{Fore.RED}Datash encountered a critical error and must exit.{Style.RESET_ALL}")
        print(f"Error details: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

