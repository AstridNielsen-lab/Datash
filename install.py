#!/usr/bin/env python3
"""
Datash Installation Script

This script automates the installation and initial setup of Datash.
It performs the following tasks:
1. Check Python version
2. Install dependencies
3. Set up configuration
4. Guide users through API key setup
5. Run basic verification tests

Usage:
    python install.py [--dev] [--no-color] [--skip-tests]

Options:
    --dev         Install development dependencies
    --no-color    Disable colored output
    --skip-tests  Skip verification tests
"""

import os
import sys
import subprocess
import argparse
import platform
import re
import shutil
import json
from pathlib import Path
import importlib.util

# Minimum required Python version
MIN_PYTHON_VERSION = (3, 8)

# Try to import colorama for cross-platform colored output
try:
    from colorama import init, Fore, Style
    init()
    HAS_COLORS = True
except ImportError:
    # Define dummy color constants if colorama is not available
    class Dummy:
        def __getattr__(self, name):
            return ""
    Fore = Dummy()
    Style = Dummy()
    HAS_COLORS = False


def print_header(text):
    """Print a formatted header."""
    print(f"\n{Fore.CYAN}=== {text} ==={Style.RESET_ALL}")


def print_success(text):
    """Print a success message."""
    print(f"{Fore.GREEN}✓ {text}{Style.RESET_ALL}")


def print_error(text):
    """Print an error message."""
    print(f"{Fore.RED}✗ {text}{Style.RESET_ALL}")


def print_warning(text):
    """Print a warning message."""
    print(f"{Fore.YELLOW}! {text}{Style.RESET_ALL}")


def print_info(text):
    """Print an information message."""
    print(f"{Fore.BLUE}ℹ {text}{Style.RESET_ALL}")


def run_command(cmd, check=True, capture_output=False):
    """Run a shell command and handle errors."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=check,
            text=True,
            capture_output=capture_output
        )
        return result
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {cmd}")
        print(f"Error output: {e.stderr}")
        if check:
            sys.exit(1)
        return e


def check_python_version():
    """Check if the current Python version meets the minimum requirement."""
    print_header("Checking Python Version")
    
    current_version = sys.version_info[:2]
    version_str = ".".join(map(str, current_version))
    
    if current_version >= MIN_PYTHON_VERSION:
        print_success(f"Python version {version_str} is compatible")
        return True
    else:
        min_version_str = ".".join(map(str, MIN_PYTHON_VERSION))
        print_error(f"Python version {version_str} is not supported")
        print_info(f"Datash requires Python {min_version_str} or higher")
        return False


def check_pip():
    """Check if pip is installed and working."""
    print_header("Checking pip")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            check=True,
            text=True,
            capture_output=True
        )
        print_success(f"pip is installed: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_error("pip is not installed or not working")
        print_info("Please install pip: https://pip.pypa.io/en/stable/installation/")
        return False


def install_dependencies(dev=False):
    """Install Datash dependencies."""
    print_header("Installing Dependencies")
    
    # First, upgrade pip, setuptools, and wheel
    print_info("Upgrading pip, setuptools, and wheel...")
    run_command(f"{sys.executable} -m pip install --upgrade pip setuptools wheel")
    
    # Install main dependencies from requirements.txt
    print_info("Installing required packages...")
    req_result = run_command(f"{sys.executable} -m pip install -r requirements.txt", check=False)
    
    if req_result.returncode != 0:
        print_warning("Could not install from requirements.txt, trying core dependencies directly...")
        run_command(f"{sys.executable} -m pip install requests python-dotenv colorama")
    else:
        print_success("Successfully installed required packages")
    
    # Install platform-specific packages
    if platform.system() == "Windows":
        print_info("Installing Windows-specific packages...")
        run_command(f"{sys.executable} -m pip install pyreadline3")
    
    # Install development dependencies if requested
    if dev:
        print_info("Installing development packages...")
        dev_packages = "pytest pytest-cov black mypy responses"
        run_command(f"{sys.executable} -m pip install {dev_packages}")
        print_success("Successfully installed development packages")


def setup_config():
    """Set up Datash configuration."""
    print_header("Setting Up Configuration")
    
    # Create .env file from template if it doesn't exist
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print_info(".env file already exists, skipping creation")
    elif env_example.exists():
        print_info("Creating .env file from template...")
        with open(env_example, "r") as example, open(env_file, "w") as env:
            env.write(example.read())
        print_success("Created .env file")
    else:
        print_warning(".env.example file not found, creating minimal .env file...")
        with open(env_file, "w") as env:
            env.write("# Datash Environment Configuration\n\n# Gemini API Key (Required)\nDATASH_API_KEY=\n")
        print_success("Created minimal .env file")
    
    # Check if API key is already configured
    api_key = os.environ.get("DATASH_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if api_key:
        print_success("API key found in environment variables")
    else:
        # Try to read from .env file
        try:
            with open(env_file, "r") as f:
                content = f.read()
                match = re.search(r"DATASH_API_KEY\s*=\s*([^\s#]+)", content)
                if match and match.group(1):
                    print_success("API key found in .env file")
                    api_key = match.group(1)
                else:
                    print_warning("API key not found in .env file")
        except Exception as e:
            print_error(f"Error reading .env file: {e}")
    
    if not api_key:
        print_info("\nTo set up your API key:")
        print_info("1. Get a Gemini API key from https://ai.google.dev/")
        print_info("2. Add it to your .env file: DATASH_API_KEY=your_key_here")
        print_info("  or set it as an environment variable:")
        if platform.system() == "Windows":
            print_info("    - PowerShell: $env:DATASH_API_KEY=\"your_key_here\"")
            print_info("    - Command Prompt: set DATASH_API_KEY=your_key_here")
        else:
            print_info("    - Bash/Zsh: export DATASH_API_KEY=your_key_here")
        
        # Prompt user to enter API key now
        try:
            key = input(f"{Fore.YELLOW}Would you like to enter your API key now? (y/n) {Style.RESET_ALL}")
            if key.lower() == 'y':
                api_key = input(f"{Fore.YELLOW}Enter your Gemini API key: {Style.RESET_ALL}")
                if api_key:
                    # Update the .env file
                    with open(env_file, "r") as f:
                        content = f.read()
                    
                    content = re.sub(
                        r"DATASH_API_KEY\s*=.*",
                        f"DATASH_API_KEY={api_key}",
                        content
                    )
                    
                    with open(env_file, "w") as f:
                        f.write(content)
                    
                    print_success("API key saved to .env file")
        except KeyboardInterrupt:
            print("\nSkipped API key entry")


def run_verification_tests():
    """Run basic verification tests."""
    print_header("Running Verification Tests")
    
    # Check if main.py exists
    if not os.path.exists("main.py"):
        print_error("main.py not found in the current directory")
        return False
    
    # Test importing main modules
    print_info("Testing module imports...")
    missing_modules = []
    for module in ["requests", "dotenv", "colorama"]:
        if importlib.util.find_spec(module) is None:
            missing_modules.append(module)
    
    if missing_modules:
        print_error(f"The following modules are missing: {', '.join(missing_modules)}")
        print_info("Try running the installation again or install them manually")
        return False
    else:
        print_success("All required modules are installed")
    
    # Check if we can import the main application modules
    try:
        print_info("Testing application imports...")
        # Use a separate process to avoid affecting the current one
        result = subprocess.run(
            [sys.executable, "-c", "from main import DatashConfig, GeminiAPI, CommandHandler"],
            check=False,
            text=True,
            capture_output=True
        )
        if result.returncode == 0:
            print_success("Application imports successful")
        else:
            print_error(f"Application import failed: {result.stderr}")
            return False
    except Exception as e:
        print_error(f"Error testing application imports: {e}")
        return False
    
    # If pytest is available, run basic tests
    if importlib.util.find_spec("pytest") is not None:
        print_info("Running basic tests...")
        if os.path.exists("tests"):
            result = run_command(
                f"{sys.executable} -m pytest tests/test_main.py::TestDatashConfig::test_init_loads_default_config -v",
                check=False,
                capture_output=True
            )
            if result.returncode == 0:
                print_success("Basic tests passed")
            else:
                print_warning("Some tests failed, but installation can continue")
                print_info("You can run tests later with: python -m pytest")
        else:
            print_info("Tests directory not found, skipping tests")
    
    return True


def setup_platform_specifics():
    """Configure platform-specific settings."""
    print_header("Platform-Specific Setup")
    
    system = platform.system()
    print_info(f"Detected operating system: {system}")
    
    if system == "Windows":
        # Windows-specific setup
        print_info("Configuring for Windows...")
        
        # Check for PowerShell
        powershell_path = shutil.which("powershell")
        if powershell_path:
            print_success("PowerShell is available")
            # Create a PowerShell launch script
            with open("run_datash.ps1", "w") as f:
                f.write("""
# Datash PowerShell launcher
if (Test-Path -Path ".env") {
    Get-Content .env | ForEach-Object {
        if ($_ -match '^([^#][^=]+)=(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
}
python main.py $args
""")
            print_success("Created PowerShell launcher: run_datash.ps1")
        else:
            print_info("PowerShell not found, skipping PowerShell launcher creation")
        
        # Create a batch file launcher
        with open("run_datash.bat", "w") as f:
            f.write("""
@echo off
python main.py %*
""")
        print_success("Created batch launcher: run_datash.bat")
        
    elif system == "Linux" or system == "Darwin":  # Darwin is macOS
        # Unix-specific setup
        print_info(f"Configuring for {system}...")
        
        # Create a shell script launcher
        with open("run_datash.sh", "w") as f:
            f.write("""#!/bin/bash
# Datash shell launcher
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi
python main.py "$@"
""")
        # Make the script executable
        os.chmod("run_datash.sh", 0o755)
        print_success("Created shell launcher: run_datash.sh")
    
    else:
        print_warning(f"Unknown operating system: {system}")
        print_info("No platform-specific setup performed")


def print_final_instructions():
    """Print final instructions for using Datash."""
    system = platform.system()
    
    print_header("Installation Complete!")
    print_info("To start Datash, run:")
    
    if system == "Windows":
        print(f"{Fore.GREEN}  .\\run_datash.bat{Style.RESET_ALL}")
        print(f"{Fore.GREEN}  # Or with PowerShell: .\\run_datash.ps1{Style.RESET_ALL}")
    else:
        print(f"{Fore.GREEN}  ./run_datash.sh{Style.RESET_ALL}")
    
    print_info("Or directly with Python:")
    print(f"{Fore.GREEN}  python main.py{Style.RESET_ALL}")
    
    print_info("\nFor more information and usage examples, see the README.md file")
    print(f"\n{Fore.CYAN}Thank you for installing Datash!{Style.RESET_ALL}")


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Install and set up Datash")
    parser.add_argument("--dev", action="store_true", help="Install development dependencies")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    parser.add_argument("--skip-tests", action="store_true", help="Skip verification tests")
    return parser.parse_args()


def main():
    """Main installation function."""
    # Parse command-line arguments
    args = parse_args()
    
    # Disable colors if requested
    global HAS_COLORS
    if args.no_color:
        HAS_COLORS = False
    
    # Print welcome message
    print(f"\n{Fore.GREEN}===================================={Style.RESET_ALL}")
    print(f"{Fore.GREEN}  Datash Installation Assistant{Style.RESET_ALL}")
    print(f"{Fore.GREEN}===================================={Style.RESET_ALL}")
    
    # Perform installation steps
    if not check_python_version():
        sys.exit(1)
    
    if not check_pip():
        sys.exit(1)
    
    install_dependencies(dev=args.dev)
    setup_config()
    
    if not args.skip_tests:
        run_verification_tests()
    
    setup_platform_specifics()
    print_final_instructions()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInstallation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Installation failed: {e}")
        sys.exit(1)

