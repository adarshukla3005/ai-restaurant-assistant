import os
import json
import time
import logging
from datetime import datetime
from typing import List, Dict, Any

# Set up basic logging
logger = logging.getLogger(__name__)

# Where we store all the chat history
HISTORY_DIR = "convo_history"
if not os.path.exists(HISTORY_DIR):
    os.makedirs(HISTORY_DIR)
HISTORY_FILE = os.path.join(HISTORY_DIR, "conversation_history.json")

# Make sure the folder exists
os.makedirs(HISTORY_DIR, exist_ok=True)

def load_conversation_history() -> Dict[str, List[Dict[str, str]]]:
    """Loads saved conversations from our JSON file"""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                history = json.load(f)
            logger.info(f"Loaded conversation history from {HISTORY_FILE}")
            return history
        except Exception as e:
            logger.error(f"Error loading conversation history: {str(e)}")
            return {}
    else:
        logger.info(f"No existing conversation history found at {HISTORY_FILE}")
        return {}

def save_conversation_history(history: Dict[str, List[Dict[str, str]]]) -> None:
    """Saves all conversations to our JSON file"""
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved conversation history to {HISTORY_FILE}")
    except Exception as e:
        logger.error(f"Error saving conversation history: {str(e)}")

def get_session_history(session_id: str, history: Dict[str, List[Dict[str, str]]]) -> List[Dict[str, str]]:
    """Gets all messages from a specific chat session"""
    return history.get(session_id, [])

def add_message_to_history(
    session_id: str, 
    role: str, 
    content: str, 
    history: Dict[str, List[Dict[str, str]]]
) -> Dict[str, List[Dict[str, str]]]:
    """Adds a new message to the chat history"""
    # Start a new chat if needed
    if session_id not in history:
        history[session_id] = []
    
    # Add the message with a timestamp
    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    }
    
    history[session_id].append(message)
    
    # Save it to file
    save_conversation_history(history)
    
    return history

def get_recent_context(session_id: str, history: Dict[str, List[Dict[str, str]]], num_messages: int = 4) -> str:
    """Gets the last few messages to help the AI remember context"""
    session_history = get_session_history(session_id, history)
    
    # Grab recent messages
    recent_messages = session_history[-num_messages:] if len(session_history) > 0 else []
    
    # Format them nicely
    if not recent_messages:
        return ""
    
    context = "Previous conversation:\n"
    for msg in recent_messages:
        role = "User" if msg["role"] == "user" else "Assistant"
        context += f"{role}: {msg['content']}\n"
    
    return context

def generate_session_id() -> str:
    """Creates a unique ID for each chat session"""
    return f"session_{int(time.time())}" 