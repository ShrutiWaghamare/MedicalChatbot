"""
Conversation Memory Management for Medical Chatbot
Stores conversation history to maintain context across messages
"""
from typing import List, Dict
from datetime import datetime
import json
import os
from src.storage import insert_message, fetch_messages, delete_messages

class ConversationMemory:
    """
    Manages conversation memory using in-memory storage.
    Can be extended to use file-based or database storage.
    """
    
    def __init__(self, max_history: int = 10):
        """
        Initialize conversation memory.
        
        Args:
            max_history: Maximum number of conversation turns to keep in memory
        """
        self.memories: Dict[str, List[Dict]] = {}
        self.max_history = max_history
    
    def get_conversation_history(self, session_id: str) -> List[Dict]:
        """
        Get conversation history for a session.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            List of conversation messages
        """
        # Prefer SQLite as source of truth
        stored = fetch_messages(session_id)
        if stored:
            return stored
        return self.memories.get(session_id, [])
    
    def add_message(self, session_id: str, role: str, content: str):
        """
        Add a message to conversation history.
        
        Args:
            session_id: Unique session identifier
            role: 'user' or 'assistant'
            content: Message content
        """
        if session_id not in self.memories:
            self.memories[session_id] = []

        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        }

        self.memories[session_id].append(message)

        # Persist to SQLite
        insert_message(session_id, role, content, message['timestamp'])

        # Keep only last max_history messages in memory cache
        if len(self.memories[session_id]) > self.max_history * 2:  # *2 because user+assistant pairs
            self.memories[session_id] = self.memories[session_id][-self.max_history * 2:]
    
    def clear_conversation(self, session_id: str):
        """Clear conversation history for a session."""
        if session_id in self.memories:
            del self.memories[session_id]
        delete_messages(session_id)
    
    def get_formatted_history(self, session_id: str, max_turns: int = 3) -> str:
        """
        Get formatted conversation history as a string for LLM context.
        Limits to last max_turns exchanges for faster responses.
        
        Args:
            session_id: Unique session identifier
            max_turns: Max number of user+assistant pairs to include (default 3)
            
        Returns:
            Formatted conversation history string
        """
        history = self.get_conversation_history(session_id)
        if not history:
            return ""
        # Keep only last N messages (2 per turn)
        keep = max_turns * 2
        history = history[-keep:] if len(history) > keep else history
        formatted = []
        for msg in history:
            role = "Human" if msg['role'] == 'user' else "Assistant"
            formatted.append(f"{role}: {msg['content']}")
        return "\n".join(formatted)


# Global memory instance
conversation_memory = ConversationMemory(max_history=10)
