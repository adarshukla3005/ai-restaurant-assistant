import os
import streamlit as st
from dotenv import load_dotenv

# Import components from modular structure
from src.config.llm_config import configure_llm
from src.database.vector_db import setup_chromadb
from src.models.query_processor import process_query, session_id

# Load environment variables
load_dotenv()

# Configure LLM
configure_llm()

# Set page config
st.set_page_config(
    page_title="Restaurant Assistant",
    page_icon="🥂",
    layout="wide",
    initial_sidebar_state="expanded"
)
# st.title("🥂 Restaurant Assistant")

# Custom CSS for better UI
st.markdown("""
<style>
    .stApp {
        max-width: 1800px;
        margin: 0 auto;
    }
    .restaurant-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #FF5722;
        margin-bottom: 0;
    }
    .restaurant-subheader {
        font-size: 1.2rem;
        color: #555;
        margin-top: 0;
    }
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .stMarkdown a {
        color: #FF5722;
        text-decoration: none;
    }
    .stMarkdown a:hover {
        text-decoration: underline;
    }
</style>
""", unsafe_allow_html=True)

# Disable automatic file watcher to prevent PyTorch conflict
if not os.environ.get('STREAMLIT_SERVER_FILE_WATCHER_TYPE'):
    os.environ['STREAMLIT_SERVER_FILE_WATCHER_TYPE'] = 'none'

# Main Streamlit UI
def main():
    st.markdown('<p class="restaurant-header" style="font-size: 2.5rem;">֎🇦🇮 Restaurant Assistant</p>', unsafe_allow_html=True)
    st.markdown('<p class="restaurant-subheader">Your intelligent guide to delicious dining options</p>', unsafe_allow_html=True)
    
    # Initialize session state for messages if it doesn't exist
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Hi! I'm your restaurant assistant. Ask me about restaurants in Delhi and Mumbai, specific cuisines, dishes, or any dining recommendations you need!"}]
    
    # Initialize or get the ChromaDB collection
    collection = setup_chromadb()
    
    # Display sidebar information
    with st.sidebar:
        st.title("About")
        st.info(
            "This is an agentic chatbot based on Google Gemini."
            "It can answer questions about restaurants in our database from Delhi and Mumbai "
            "as well as general knowledge questions."
        )
        
        st.sidebar.divider()
        st.sidebar.caption(f"Session ID: {session_id}")
        st.sidebar.caption("Your conversation is saved automatically")
    
    # Chat interface
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # User input
    if user_query := st.chat_input("Ask about restaurants, cuisines, or dishes..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)
        
        # Display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Finding the best answers for you..."):
                response = process_query(user_query, collection)
                st.markdown(response)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main() 