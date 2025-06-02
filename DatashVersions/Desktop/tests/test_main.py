"""
Tests for the main Datash application functionality.
"""

import os
import json
import pytest
from unittest.mock import patch, MagicMock

from main import DatashConfig, GeminiAPI, CommandHandler, DatashCLI

# Configuration Tests
class TestDatashConfig:
    """Tests for the DatashConfig class."""
    
    def test_init_loads_default_config(self, mock_env_vars):
        """Test that the default configuration is loaded on initialization."""
        config = DatashConfig()
        assert config.config["api_url"].endswith("generateContent")
        assert config.config["max_history"] == 100
        assert config.config["display_suggestions"] is True
    
    def test_api_key_from_env(self, mock_env_vars):
        """Test that the API key is loaded from environment variables."""
        config = DatashConfig()
        assert config.api_key == "test_api_key_123"
    
    def test_get_config_value(self, config_with_api_key):
        """Test retrieving configuration values."""
        assert config_with_api_key.get("api_url") is not None
        assert config_with_api_key.get("nonexistent_key", "default") == "default"
    
    def test_set_config_value(self, config_with_api_key):
        """Test setting configuration values."""
        config_with_api_key.set("test_key", "test_value")
        assert config_with_api_key.get("test_key") == "test_value"
    
    def test_validate_with_api_key(self, config_with_api_key):
        """Test validation passes with API key."""
        assert config_with_api_key.validate() is True
    
    def test_validate_without_api_key(self, monkeypatch):
        """Test validation fails without API key."""
        monkeypatch.delenv("DATASH_API_KEY", raising=False)
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        
        with patch('main.logger.error'):  # Suppress error logs in test output
            config = DatashConfig()
            assert config.validate() is False
    
    def test_save_config(self, config_with_api_key, tmp_path):
        """Test saving configuration to file."""
        # Create a temporary path for the config
        test_config_path = tmp_path / "test_config.json"
        
        # Mock expanduser to return our test path
        with patch('os.path.expanduser', return_value=str(test_config_path)):
            config_with_api_key.set("test_key", "test_value")
            config_with_api_key.save()
            
            # Check if file was created and contains our test value
            assert os.path.exists(test_config_path)
            with open(test_config_path, 'r') as f:
                saved_config = json.load(f)
                assert saved_config["test_key"] == "test_value"

# Gemini API Tests
class TestGeminiAPI:
    """Tests for the GeminiAPI class."""
    
    def test_init(self, config_with_api_key):
        """Test initialization of the GeminiAPI class."""
        api = GeminiAPI(config_with_api_key)
        assert api.api_key == "test_api_key_123"
        assert api.history == []
    
    def test_call_gemini(self, mock_gemini_api):
        """Test calling the Gemini API."""
        response = mock_gemini_api.call_gemini("Test prompt")
        assert response == "This is a mocked response from the Gemini API."
        assert len(mock_gemini_api.history) == 1
        assert mock_gemini_api.history[0]["user"] == "Test prompt"
    
    def test_suggest_next_action(self, mock_gemini_api):
        """Test generating suggestions."""
        with patch.object(GeminiAPI, 'call_gemini', return_value="Suggested next action"):
            suggestion = mock_gemini_api.suggest_next_action("context")
            assert suggestion == "Suggested next action"
    
    def test_api_error_handling(self, config_with_api_key):
        """Test handling of API errors."""
        api = GeminiAPI(config_with_api_key)
        
        # Mock a failed API request
        with patch('requests.post') as mock_post:
            mock_post.side_effect = Exception("API connection error")
            result = api.call_gemini("Test prompt")
            assert result is None

# Command Handler Tests
class TestCommandHandler:
    """Tests for the CommandHandler class."""
    
    def test_init(self, config_with_api_key, mock_gemini_api):
        """Test initialization of CommandHandler."""
        handler = CommandHandler(config_with_api_key, mock_gemini_api)
        assert handler.config == config_with_api_key
        assert handler.api == mock_gemini_api
    
    def test_execute_shell_command(self, mock_command_handler, mock_subprocess_run):
        """Test executing shell commands."""
        result = mock_command_handler.execute_shell_command("ls -la")
        assert "Command executed successfully" in result
        mock_subprocess_run.assert_called_once()
    
    def test_process_command_builtin(self, mock_command_handler):
        """Test processing built-in commands."""
        with patch.object(CommandHandler, 'handle_builtin_command', return_value="Help text"):
            result = mock_command_handler.process_command("!help")
            assert result == "Help text"
    
    def test_process_command_shell(self, mock_command_handler):
        """Test processing shell commands."""
        with patch.object(CommandHandler, 'execute_shell_command', return_value="Shell output"):
            result = mock_command_handler.process_command("$ ls")
            assert result == "Shell output"
    
    def test_process_command_api(self, mock_command_handler):
        """Test processing regular commands via API."""
        with patch.object(GeminiAPI, 'call_gemini', return_value="API response"):
            result = mock_command_handler.process_command("regular command")
            assert result == "API response"
    
    def test_handle_builtin_command_help(self, mock_command_handler):
        """Test the help command."""
        with patch.object(CommandHandler, 'show_help', return_value="Help text"):
            result = mock_command_handler.handle_builtin_command("help")
            assert result == "Help text"
    
    def test_handle_builtin_command_unknown(self, mock_command_handler):
        """Test handling unknown built-in commands."""
        result = mock_command_handler.handle_builtin_command("unknown_command")
        assert "Unknown command" in result
    
    def test_handle_config_command(self, mock_command_handler):
        """Test the config command."""
        # Test show config
        result = mock_command_handler.handle_config_command([])
        assert "Current configuration" in result
        
        # Test set config
        with patch.object(DatashConfig, 'set') as mock_set:
            with patch.object(DatashConfig, 'save') as mock_save:
                result = mock_command_handler.handle_config_command(["set", "test_key", "test_value"])
                assert "Configuration updated" in result
                mock_set.assert_called_once_with("test_key", "test_value")
                mock_save.assert_called_once()

# CLI Tests
class TestDatashCLI:
    """Tests for the DatashCLI class."""
    
    def test_init(self):
        """Test CLI initialization."""
        with patch.object(DatashConfig, 'validate', return_value=True):
            cli = DatashCLI()
            assert cli.config is not None
            assert cli.api is not None
            assert cli.command_handler is not None
    
    def test_parse_args(self, mock_cli):
        """Test argument parsing."""
        args = mock_cli.parse_args()
        assert args.debug is True
    
    def test_run_single_command(self):
        """Test running a single command."""
        with patch('sys.argv', ['datash', '--execute', 'test command']):
            with patch.object(DatashConfig, 'validate', return_value=True):
                with patch.object(CommandHandler, 'process_command', return_value="Command result"):
                    with patch('builtins.print') as mock_print:
                        cli = DatashCLI()
                        cli.run()
                        mock_print.assert_called_with("Command result")
    
    def test_run_interactive_mode(self, mock_cli):
        """Test running in interactive mode."""
        with patch.object(CommandHandler, 'process_command', return_value="Command result"):
            with patch('builtins.print') as mock_print:
                with patch.object(GeminiAPI, 'suggest_next_action', return_value="Try this next"):
                    mock_cli.run()
                    # Check that the command result was printed
                    mock_print.assert_any_call("Command result")

# Integration-Style Tests
def test_end_to_end_command_flow():
    """Test the full command processing flow."""
    # Mock dependencies to simulate a full command flow
    with patch.object(DatashConfig, 'validate', return_value=True):
        config = DatashConfig()
        
        # Mock API response
        with patch.object(GeminiAPI, 'call_gemini', return_value="API response for command"):
            api = GeminiAPI(config)
            handler = CommandHandler(config, api)
            
            # Process a regular command
            result = handler.process_command("how to connect to PostgreSQL")
            assert result == "API response for command"
            
            # Process a shell command
            with patch('subprocess.run') as mock_run:
                mock_process = MagicMock()
                mock_process.stdout = "Shell command output"
                mock_process.stderr = ""
                mock_run.return_value = mock_process
                
                result = handler.process_command("$ ls -la")
                assert result == "Shell command output"
            
            # Process a built-in command
            with patch.object(CommandHandler, 'show_help', return_value="Help information"):
                result = handler.process_command("!help")
                assert result == "Help information"

