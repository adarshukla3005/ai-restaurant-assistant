# Agentic Restaurant Assistant Chatbot - Technical Documentation

## 1. System Architecture

### 1.1 High-Level Overview

The Restaurant Assistant Chatbot is a dual-purpose intelligent chatbot system designed to:
1. Answer restaurant-specific queries using a vector database of restaurant information
2. Handle general knowledge questions using Google's Gemini LLM

The system follows a modular architecture with clear separation of concerns:

```
https://miro.medium.com/v2/resize:fit:1400/1*_zIYIh8BwufEnQngii8lfA.png
```

### 1.2 Key Components

#### 1.2.1 Frontend Layer
- **Streamlit Application**: Provides the user interface with chat functionality and session management
- **Conversation History Management**: Tracks user interactions across sessions

#### 1.2.2 Application Layer
- **Query Processor**: Routes queries to the appropriate system (restaurant DB or general LLM)
- **LLM Integration**: Connects to Google's Gemini model for generating responses
- **Context Builder**: Assembles relevant context from vector search results

#### 1.2.3 Data Layer
- **Vector Database (ChromaDB)**: Stores embeddings of restaurant information for semantic search
- **Embedding Model**: Generates semantic embeddings using Sentence Transformers
- **Data Web Scraper**: Collects restaurant data from food platforms

#### 1.2.4 Utilities and Support
- **Prompt Templates**: Structured prompts for guiding LLM responses
- **Data Schemas**: Standardized format for restaurant information
- **Text Processing**: NLP utilities for preprocessing text inputs

## 2. Implementation Details & Design Decisions

### 2.1 Vector Search Implementation

The system uses ChromaDB as a vector database with the following design choices:

1. **Document Structure**: Restaurant data is split into multiple document types:
   - Restaurant overview documents
   - Menu section documents (grouped by food type)
   - Individual menu item documents
   - Cuisine-specific documents
   - Location documents

2. **Embedding Strategy**: 
   - Uses `sentence-transformers/all-MiniLM-L6-v2` for generating embeddings
   - Applies text preprocessing including stopword removal and lemmatization

3. **Query Results Organization**:
   - Results are structured by document type
   - Restaurants are ranked by relevance and rating
   - Duplicate restaurant information is eliminated
   - Context is assembled with clear section headers

### 2.2 Query Routing Logic

The system implements an intelligent query router:

```
User Query
    │
    ▼
Is food/restaurant related? ──No──► General LLM Response
    │
    Yes
    │
    ▼
Vector Search Restaurant DB
    │
    ▼
Build Enhanced Context
    │
    ▼
Generate Focused LLM Response
```

Design decisions:
- Uses keyword matching to identify food/restaurant queries
- Searches the vector DB with higher-than-needed result count (n=20) to ensure comprehensive coverage
- Builds context by grouping results by type (restaurant info, menu items, etc.)

### 2.3 Web Scraper Architecture

The webscraper component implements:

1. **Ethical Scraping**:
   - Respects robots.txt with a RobotFileParser implementation
   - Implements adaptive rate limiting with randomized delays
   - Sets appropriate user agent headers

2. **Robust Data Extraction**:
   - Uses a combination of Selenium for JavaScript-rendered content and BeautifulSoup for parsing
   - Implements multiple fallback selectors for each data element
   - Handles pagination and progressive loading

3. **Data Processing Pipeline**:
   - Extracts structured data according to restaurant schema
   - Performs validation and cleaning operations
   - Handles currency symbols and formatting

### 2.4 LLM Integration

The system uses Google Gemini with the following integration approach:

1. **Prompt Engineering**:
   - Separate prompts for restaurant vs. general queries
   - Structured output formatting guidelines in the prompts
   - Context injection for restaurant-specific knowledge

2. **Model Configuration**:
   - Uses Gemini-2.0-flash model for balance of performance and cost
   - API key management through environment variables

## 3. Challenges Faced and Solutions Implemented

### 3.1 Data Collection Challenges

**Challenge**: Extracting consistent restaurant data from various sources with different DOM structures.

**Solution**: 
- Implemented flexible extraction patterns with multiple selector fallbacks
- Added error recovery and partial data collection capabilities
- Used Selenium for JavaScript-rendered content that couldn't be accessed with simple HTTP requests

### 3.2 Query Understanding Challenges

**Challenge**: Determining whether a query is restaurant-related or general knowledge.

**Solution**:
- Created an extensive keyword list (100+ terms) for food and restaurant identification
- Implemented a layered approach where restaurant data is tried first, with fallback to general knowledge
- Added conversation context to help disambiguate follow-up questions

### 3.3 Vector Search Optimization Challenges

**Challenge**: Simple vector search returned too many irrelevant results.

**Solution**:
- Split restaurant data into multiple document types (restaurant info, menu items, etc.)
- Implemented metadata filtering to sort and prioritize results
- Added document weighting based on match quality
- Developed a context builder that organizes information by type before presentation to the LLM

### 3.4 Response Quality Challenges

**Challenge**: LLM responses were sometimes inconsistent in structure and information inclusion.

**Solution**:
- Created detailed prompt templates with specific formatting instructions
- Implemented structured context building with clear section headings
- Added explicit response guidelines for different query types (restaurant recommendations, menu queries, etc.)
- Included conversation history in the context for better continuity

## 4. Future Improvement Opportunities

### 4.1 Technical Enhancements

1. **Backend API Development**:
   - Migrate from Streamlit-only to a Flask/FastAPI backend with Streamlit as frontend
   - Implement proper API endpoints for better scalability and integration options

2. **Data Expansion**:
   - Expand data collection to more cities and restaurant types
   - Implement automatic regular updates to keep information current
   - Add integration with live restaurant APIs (where available)

3. **Advanced Search Features**:
   - Implement hybrid search combining vector and keyword matching
   - Add geolocation-based search and filtering
   - Develop multi-hop reasoning for complex queries

### 4.2 User Experience Improvements

1. **Multimodal Capabilities**:
   - Add voice input/output using speech-to-text and text-to-speech
   - Implement image recognition for uploaded photos of food/restaurants
   - Add visual response elements (maps, restaurant photos, etc.)

2. **Personalization**:
   - Develop user preference tracking
   - Implement personalized recommendations based on past interactions
   - Add dietary preference settings and restrictions

3. **Extended Functionality**:
   - Integrate booking/reservation capabilities
   - Add delivery service integration
   - Implement social sharing features

### 4.3 AI and Machine Learning Enhancements

1. **Fine-tuned Models**:
   - Create a domain-specific fine-tuned model for restaurant queries
   - Implement adaptive learning from user interactions

2. **Advanced Context Processing**:
   - Develop a more sophisticated context window management system
   - Implement multi-document reasoning capabilities
   - Add fact-checking against the vector database

3. **Visual Understanding**:
   - Integrate vision transformer models for restaurant image analysis
   - Implement dish recognition from food images
   - Add menu OCR capabilities for processing uploaded menu photos

## 5. Conclusion

The Agentic Restaurant Assistant Chatbot demonstrates an effective architecture for domain-specific knowledge retrieval combined with general LLM capabilities. The system showcases how vector databases and embeddings can be used to create context-aware chatbots that provide specific information while maintaining the conversational abilities of large language models.

The modular design allows for easy expansion and enhancement, while the current implementation already provides valuable restaurant information discovery capabilities. Future improvements can build on this foundation to create an even more powerful and user-friendly assistant. 
