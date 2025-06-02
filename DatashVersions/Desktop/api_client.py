"""
API Client for Gemini interactions.

This module handles all interactions with the Google Gemini API,
including authentication, request formatting, and response parsing.
"""

import os
import requests
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
import json
import platform

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("datash.api")

# Default API key and URL
DEFAULT_API_KEY = "AIzaSyAuFi5KtPsMJI5IC8c5FjvYD5IbuBdwH_U"
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"

# Conversation history storage (in-memory only, no persistence)
MAX_HISTORY_ITEMS = 20


class ConversationContext:
    """Manages conversation context and history for the API client."""
    
    def __init__(self, max_items: int = MAX_HISTORY_ITEMS):
        """
        Initialize a new conversation context.
        
        Args:
            max_items: Maximum number of conversation items to keep in history
        """
        self.history: List[Dict[str, str]] = []
        self.max_items = max_items
        self.session_start_time = time.time()
        
    def add_interaction(self, user_input: str, assistant_response: str):
        """
        Add an interaction to the conversation history.
        
        Args:
            user_input: The user's input message
            assistant_response: The assistant's response
        """
        self.history.append({
            "user": user_input,
            "assistant": assistant_response,
            "timestamp": time.time()
        })
        
        # Trim history if needed
        if len(self.history) > self.max_items:
            self.history = self.history[-self.max_items:]
            
    def get_formatted_history(self) -> str:
        """
        Get the conversation history formatted for inclusion in prompts.
        
        Returns:
            A string containing the formatted conversation history
        """
        if not self.history:
            return ""
            
        formatted = "Previous conversation:\n"
        for item in self.history:
            formatted += f"User: {item['user']}\n"
            formatted += f"Assistant: {item['assistant']}\n\n"
            
        return formatted
        
    def clear(self):
        """Clear the conversation history."""
        self.history = []
        self.session_start_time = time.time()


class GeminiClient:
    """Client for interacting with the Google Gemini API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Gemini API client.
        
        Args:
            api_key: Optional API key. If not provided, uses environment variable 
                    GEMINI_API_KEY or falls back to the default key.
        """
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", DEFAULT_API_KEY)
        self.system_prompt = self._get_system_prompt()
        self.context = ConversationContext()
        
    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for the Gemini model.
        
        Returns:
            A string containing the system prompt.
        """
        return """
You are an intelligent assistant in a terminal for programmers. 
Your function is to help the user interact with databases, manipulate files, 
automate bash commands, utilize Git, and process data.

Your environment is primarily a terminal (Bash on Linux/Mac, PowerShell on Windows). 
You respond with commands, code snippets, and suggestions.

Rules:
- Never save data about the user.
- Be precise, useful, and objective.
- Suggest the next action based on the conversation history.
- Provide native support for Git, MySQL, SQLite, PostgreSQL, MongoDB.
- Offer support for processing files like .csv and .json.
- Return responses ready to copy and use in the terminal.
- Adapt commands for Windows when detected.

When providing code or command examples, use markdown code blocks with the 
appropriate language specifier.

Example of interaction:
User: importar csv para sqlite
Response: 
```bash
sqlite3 mydatabase.db
.mode csv
.import data.csv tablename
```

For database operations, provide complete working examples with imports and 
connection code when appropriate.
"""
    
    def get_response(self, prompt: str, history: Optional[List[str]] = None) -> str:
        """
        Get a response from the Gemini API.
        
        Args:
            prompt: The user's input prompt
            history: Optional list of previous commands for context
            
        Returns:
            The text response from the API
            
        Raises:
            Exception: If the API request fails
        """
        # Prepare headers
        headers = {
            "Content-Type": "application/json"
        }
        
        # Prepare context with conversation history
        context = self.context.get_formatted_history()
        
        # Add command history if provided separately
        if history and len(history) > 0:
            if context:
                context += "\n"
            context += "Previous commands:\n" + "\n".join(history) + "\n\n"
            
        # Add system information for context
        os_name = platform.system()
        os_version = platform.version()
        context += f"Current OS: {os_name} {os_version}\n"
        
        # Add current working directory
        context += f"Current directory: {os.getcwd()}\n\n"
            
        # Prepare the full prompt
        full_prompt = f"{self.system_prompt}\n\n{context}User input: {prompt}"
        
        logger.debug(f"Sending prompt to Gemini API: {prompt}")
        
        # Prepare the request data
        data = {
            "contents": [{
                "parts": [{
                    "text": full_prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.2,  # Lower temperature for more deterministic responses
                "topP": 0.8,
                "topK": 40,
                "maxOutputTokens": 2048,
            }
        }
        
        # Make the API request with retry logic
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    f"{API_URL}?key={self.api_key}",
                    headers=headers,
                    json=data,
                    timeout=30
                )
                
                # Check for successful response
                response.raise_for_status()
                
                # Parse and return the response text
                response_json = response.json()
                
                # Extract the text from the response
                try:
                    response_text = response_json["candidates"][0]["content"]["parts"][0]["text"]
                    
                    # Update conversation context with this interaction
                    self.context.add_interaction(prompt, response_text)
                    
                    return response_text
                    
                except (KeyError, IndexError) as e:
                    # Handle unexpected response format
                    error_msg = f"Unexpected API response format: {e}"
                    logger.error(error_msg)
                    raise Exception(error_msg)
                    
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    logger.warning(f"API request failed, retrying ({attempt+1}/{max_retries}): {str(e)}")
                    time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                else:
                    error_msg = f"API request failed after {max_retries} attempts: {str(e)}"
                    logger.error(error_msg)
                    raise Exception(error_msg)
    
    def clear_conversation(self):
        """Clear the current conversation context."""
        self.context.clear()
        logger.info("Conversation context cleared")
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current conversation.
        
        Returns:
            Dictionary with conversation statistics
        """
        return {
            "interaction_count": len(self.context.history),
            "session_duration": time.time() - self.context.session_start_time
        }
