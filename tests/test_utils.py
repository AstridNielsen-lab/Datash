"""
Utility functions and classes for Datash testing.
"""

import os
import json
import tempfile
from contextlib import contextmanager
from unittest.mock import patch, MagicMock

@contextmanager
def temp_env_var(key, value):
    """
    Context manager to temporarily set an environment variable.
    
    Args:
        key: The environment variable name
        value: The value to set
        
    Yields:
        None
    """
    original = os.environ.get(key)
    os.environ[key] = value
    try:
        yield
    finally:
        if original is None:
            del os.environ[key]
        else:
            os.environ[key] = original

@contextmanager
def temp_config_file(config_data):
    """
    Context manager to create a temporary config file.
    
    Args:
        config_data: Dictionary of configuration data
        
    Yields:
        str: Path to the temporary config file
    """
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as tmp:
        json.dump(config_data, tmp)
        tmp_name = tmp.name
    
    try:
        yield tmp_name
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)

def create_mock_response(status_code=200, json_data=None, text=None):
    """
    Create a mock response object for API testing.
    
    Args:
        status_code: HTTP status code
        json_data: Dictionary to return as JSON
        text: Text to return
        
    Returns:
        MagicMock: A mock response object
    """
    mock_response = MagicMock()
    mock_response.status_code = status_code
    
    if json_data:
        mock_response.json.return_value = json_data
    
    if text:
        mock_response.text = text
    else:
        mock_response.text = "Mock response text"
    
    return mock_response

def create_gemini_response_data(text="Mocked Gemini response"):
    """
    Create a mock Gemini API response data structure.
    
    Args:
        text: The response text
        
    Returns:
        dict: A dictionary representing a Gemini API response
    """
    return {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": text
                        }
                    ]
                }
            }
        ]
    }

def capture_stdout():
    """
    Context manager to capture stdout for testing.
    
    Returns:
        contextmanager: A context manager that yields the captured output
    """
    from io import StringIO
    import sys
    
    @contextmanager
    def _capture_stdout():
        stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            yield sys.stdout
        finally:
            sys.stdout = stdout
    
    return _capture_stdout()

class MockKeyboardInterrupt:
    """Utility to mock a keyboard interrupt after N calls."""
    
    def __init__(self, interrupt_on_call=2):
        """
        Initialize the mock with the call count for interruption.
        
        Args:
            interrupt_on_call: Which call number should raise KeyboardInterrupt
        """
        self.calls = 0
        self.interrupt_on_call = interrupt_on_call
    
    def __call__(self, *args, **kwargs):
        """Callable that raises KeyboardInterrupt after N calls."""
        self.calls += 1
        if self.calls >= self.interrupt_on_call:
            raise KeyboardInterrupt()
        return "mock input"

