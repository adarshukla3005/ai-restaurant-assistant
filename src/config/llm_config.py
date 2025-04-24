import os
import google.generativeai as genai
from dotenv import load_dotenv
import streamlit as st

# Load environment variables
load_dotenv()

# Configure Google gen AI with API key from .env file.
def configure_llm():

    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY environment variable is not set")
    
    genai.configure(api_key=GOOGLE_API_KEY)

# Initialize and return the Gemini model.
# Caches the model to avoid reloading.
@st.cache_resource
def get_gemini_model():
    return genai.GenerativeModel('gemini-2.0-flash')

def generate_response(prompt):
    model = get_gemini_model()
    response = model.generate_content(prompt)
    return response.text 