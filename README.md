# Agentic Restaurant Assistant Chatbot

An intelligent chatbot that can answer both restaurant-specific queries using a vector database and general knowledge questions using Gemini-2.0-flash.

For Demo: [Watch Now](https://drive.google.com/file/d/1jm_bgHZta1msYVTk5KXRXwB7vzKGCfwu/view?usp=sharing)

![image](https://github.com/user-attachments/assets/e0a40923-122d-4743-9a70-b208bf8992f7)


## Features

- **Restaurant Database**: Search and retrieve information about restaurants, menus, prices, and more
- **Vector Search**: Uses ChromaDB with sentence-transformers for semantic search
- **Dual-Purpose**: Handles both domain-specific and general queries
- **Modern UI**: Built with Streamlit for an intuitive user experience
- **Modular Architecture**: Clean separation of concerns with independent modules
- **Web Scraping**: Automated collection of restaurant data using Selenium and BeautifulSoup

## Technologies Used

- **LLM**: Google's Gemini-2.0-flash for natural language generation
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2 for high-quality vector embeddings
- **Vector Database**: ChromaDB for efficient similarity search with preference ordering based on features
- **Web Interface**: Streamlit for the user interface
- **Web Scraping**: Selenium and BeautifulSoup4 for restaurant data collection
- **Data Processing**: JSON processing and structured data extraction

## Setup and Installation

1. Clone the repository:
   ```
   git clone <https://github.com/adarshukla3005/ai-restaurant-assistant.git>
   cd <ai-restaurant-assistant>
   ```

2. Create a virtual environment (optional but recommended):
   ```
   python -m venv myenv
   # On Windows
   myenv\Scripts\activate
   ```

3. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up your API keys:
   - Get a Google API key for the Gemini model from [Google AI Studio](https://makersuite.google.com/)
   - Add your API key to the `.env` file:
     ```
     GOOGLE_API_KEY=your_api_key_here
     ```

## Running the Application

1. Start the Streamlit app:
   ```
   streamlit run app.py
   ```

2. Open your web browser and navigate to:
   ```
   http://localhost:8501
   ```

## Usage Examples

- **Restaurant Queries**:
  - "What are some vegetarian restaurants in Mumbai?"
  - "Tell me about the menu at Bombay Taco Co."
  - "What's the price range at KFC?"
  - "Recommend some good pizza places with budget non-veg options"

- **General Queries**:
  - "What's the weather like today?"
  - "Tell me about the history of Indian cuisine"
  - "How do I make pasta at home?"

## Web Scraper

The project includes a web scraper to collect restaurant data:

- **Data Collection**: Scrapes restaurant details from popular food platforms like Zomato and Magicpin
- **Comprehensive Data**: Extracts names, menus, prices, locations, ratings, photos, and more
- **Ethical Scraping**: Respects robots.txt and implements rate limiting
- **Data Processing**: Cleans and structures data for the vector database
- **Scalable**: Can be configured to scrape multiple restaurants in a batch

To run the web scraper:
```
python webscraper.py  # For general restaurant scraping
python utils/zomato_scraper.py  # For Zomato-specific scraping
```

## Project Structure

The project has been restructured with a modular architecture:

```
.
├── app.py                  # Main Streamlit application
├── data/                   # Restaurant data in JSON format
├── chroma_db/              # Generated vector database (created on first run)
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables for API keys
├── webscraper.py           # Main web scraping script for the data from Magicpin website and storing in data folder
|── utils/                  # contains utility function for specific uses
└── src/                    # Source code directory
    ├── config/             # Configuration modules
    │   └── llm_config.py   # LLM configuration
    ├── database/           # Database modules
    │   └── vector_db.py    # Vector database operations
    ├── models/             # Model modules
    │   ├── embeddings.py   # Embedding model configuration
    │   └── query_processor.py # Query processing
    └── prompts/            # Prompt templates
        └── prompts.py      # Prompts for LLM
```

## Backend

The application uses the following backend components:

1. **ChromaDB** - An open-source embedding database for storing and querying vector embeddings
   - Persisted locally in the `chroma_db` directory
   - No external server required

2. **Hugging Face Sentence Transformers** - For generating high-quality text embeddings
   - Uses the all-MiniLM-L6-v2 model from HuggingFace
   - Runs locally, no external API needed

3. **Google Generative AI** - For LLM functionality
   - Uses Gemini-2.0-flash model
   - Requires a Google API key

## Frontend
   **Streamlit** - For web UI
   - Runs a local development server

   **Web Scraping** - For data collection
   - Selenium for browser automation
   - BeautifulSoup4 for HTML parsing
   - Handles JavaScript-rendered content and dynamic pages

No additional backend server setup is required as all components are either self-contained or make API calls to external services.

## Customization

- To add more restaurants, add JSON files to the `data/` directory or run the web scraper with new URLs
- To change the embedding model, update the `EMBEDDING_MODEL_NAME` in `src/models/embeddings.py`
- To modify prompts, edit the templates in `src/prompts/prompts.py`
- To customize scraping targets, edit the URL lists in the web scraper scripts change the element class

## Acknowledgements

- This project uses restaurant data collected from various sources (eg. Magicpin and Zomato)
- Built with open-source libraries and tools
  
## Future Enhancements
- Can use Flask/FastAPI for backend purposes if we want to integrate it on server
- We can also integrate Voice Input/Output in the Chatbot for STT and TTS to enhance user engagements
- We can use any Vision Transformer models to get a good description of Restaurant Menu and Facilities through the images.
