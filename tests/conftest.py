"""
pytest configuration and fixtures for Datash tests.
"""

import os
import json
import pytest
import tempfile
import responses
from unittest.mock import patch, MagicMock

# Import Datash classes
from main import DatashConfig, GeminiAPI, CommandHandler, DatashCLI

@pytest.fixture
def mock_env_vars(monkeypatch):
    """Fixture to set up mock environment variables."""
    monkeypatch.setenv("DATASH_API_KEY", "test_api_key_123")
    
@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing."""
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as tmp:
        config = {
            "api_url": "https://test-api-url.example.com",
            "history_file": "~/.test_history",
            "max_history": 50,
            "display_suggestions": False
        }
        json.dump(config, tmp)
        tmp_name = tmp.name
    
    yield tmp_name
    
    # Cleanup
    if os.path.exists(tmp_name):
        os.unlink(tmp_name)

@pytest.fixture
def config_with_api_key(mock_env_vars):
    """Fixture to create a config object with API key."""
    return DatashConfig()

@pytest.fixture
def mock_gemini_api_response():
    """Fixture to mock Gemini API responses."""
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.POST,
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent",
            json={
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": "This is a mocked response from the Gemini API."
                                }
                            ]
                        }
                    }
                ]
            },
            status=200,
        )
        yield rsps

@pytest.fixture
def mock_gemini_api(config_with_api_key, mock_gemini_api_response):
    """Fixture to create a mocked GeminiAPI instance."""
    return GeminiAPI(config_with_api_key)

@pytest.fixture
def mock_command_handler(config_with_api_key, mock_gemini_api):
    """Fixture to create a CommandHandler with mocked dependencies."""
    return CommandHandler(config_with_api_key, mock_gemini_api)

@pytest.fixture
def mock_subprocess_run():
    """Fixture to mock subprocess.run for shell command execution."""
    with patch('subprocess.run') as mock_run:
        mock_process = MagicMock()
        mock_process.stdout = "Command executed successfully"
        mock_process.stderr = ""
        mock_run.return_value = mock_process
        yield mock_run

@pytest.fixture
def cli_args():
    """Fixture for CLI argument parsing tests."""
    return ["--debug"]

@pytest.fixture
def mock_cli(monkeypatch, cli_args):
    """Fixture to create a CLI with mocked arguments."""
    monkeypatch.setattr('sys.argv', ['datash'] + cli_args)
    
    # Mock config validation to always pass
    with patch.object(DatashConfig, 'validate', return_value=True):
        # Mock the input function
        with patch('builtins.input', side_effect=["test command", "!exit"]):
            yield DatashCLI()

