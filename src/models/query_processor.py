from src.prompts.prompts import RESTAURANT_QUERY_PROMPT, GENERAL_QUERY_PROMPT, FOOD_RELATED_KEYWORDS
from src.config.llm_config import generate_response
from src.database.vector_db import query_database
from src.models.conversation_history import (
    load_conversation_history, 
    add_message_to_history,
    get_recent_context,
    generate_session_id
)

# Global history store
conversation_history = load_conversation_history()
session_id = generate_session_id()

def process_query(user_query, collection):
    # Process user query and generate response using either restaurant-specific 
    # or general knowledge, depending on query type
    global conversation_history
    
    # Add user message to history
    conversation_history = add_message_to_history(
        session_id, 
        "user", 
        user_query, 
        conversation_history
    )
    
    # Get recent conversation context (last 4 messages)
    convo_context = get_recent_context(session_id, conversation_history)
    
    # First check if the query is restaurant-related
    is_food_related = any(keyword in user_query.lower() for keyword in FOOD_RELATED_KEYWORDS)
    
    if is_food_related:
        # Query the vector database with increased results for more options
        results = query_database(user_query, collection, n_results=20)
        
        if results and results['documents'][0]:
            # Enhanced context building with metadata awareness
            db_context = build_enhanced_context(results, user_query)
            
            # Format prompt with both database and conversation context
            prompt = RESTAURANT_QUERY_PROMPT.format(
                context=db_context,
                conversation_history=convo_context,
                user_query=user_query
            )
            
            # Get response from Gemini with context
            response = generate_response(prompt)
            
            # Add assistant response to history
            conversation_history = add_message_to_history(
                session_id,
                "assistant",
                response,
                conversation_history
            )
            
            return response
    
    # For general queries or if no relevant results found
    prompt = GENERAL_QUERY_PROMPT.format(
        conversation_history=convo_context,
        user_query=user_query
    )
    
    response = generate_response(prompt)
    
    # Add assistant response to history
    conversation_history = add_message_to_history(
        session_id,
        "assistant",
        response,
        conversation_history
    )
    
    return response

def build_enhanced_context(results, user_query):
    """
    Build an enhanced context from query results, using metadata to organize information.
    
    Args:
        results: Results from ChromaDB query
        user_query: The original user query to prioritize relevant info
        
    Returns:
        str: A well-formatted context for the LLM
    """
    if not results or not results['documents'][0]:
        return ""
    
    # Get documents and their metadata
    documents = results['documents'][0]
    metadatas = results['metadatas'][0]
    distances = results['distances'][0]
    
    # Create a list of (document, metadata, distance) tuples for easier sorting and processing
    result_items = list(zip(documents, metadatas, distances))
    
    # Track restaurants to avoid duplicates
    seen_restaurants = set()
    
    # Organize documents by type
    restaurants_info = []
    cuisine_info = []
    location_info = []
    menu_sections = []
    menu_items = []
    
    # Sort restaurant info by relevance first
    restaurant_items = [item for item in result_items if item[1].get('type', '') == 'restaurant_info']
    
    # Sort by distance (lower is better)
    restaurant_items.sort(key=lambda x: x[2])
    
    # Create prioritized restaurant info
    for doc, meta, _ in restaurant_items:
        restaurant_name = meta.get('restaurant', meta.get('name', ''))
        if restaurant_name not in seen_restaurants:
            restaurants_info.append(doc)
            seen_restaurants.add(restaurant_name)
    
    # Process other document types
    for doc, meta, _ in result_items:
        doc_type = meta.get('type', '')
        restaurant_name = meta.get('restaurant', meta.get('name', ''))
        
        # Add unique restaurant information
        if doc_type == 'restaurant_info':
            # Already processed above
            pass
        # Add cuisine-specific information
        elif doc_type == 'cuisine_info':
            cuisine_info.append(doc)
        # Add location-specific information
        elif doc_type == 'location_info':
            location_info.append(doc)
        # Add menu sections
        elif doc_type == 'menu_section':
            menu_sections.append(doc)
        # Add menu items
        elif doc_type == 'menu_item':
            menu_items.append(doc)
    
    # Build context with sections and ensure we include enough restaurants
    context_parts = []
    
    # Add restaurant information first (most important)
    if restaurants_info:
        context_parts.append("RESTAURANT INFORMATION:")
        # Ensure we include at least 5 restaurant info blocks if available
        for i, info in enumerate(restaurants_info[:min(8, len(restaurants_info))]):
            context_parts.append(f"Restaurant Option #{i+1}:")
            context_parts.append(info)
    
    # Add cuisine information
    if cuisine_info:
        context_parts.append("\nCUISINE INFORMATION:")
        context_parts.extend(cuisine_info[:min(5, len(cuisine_info))])
    
    # Add location information
    if location_info:
        context_parts.append("\nLOCATION INFORMATION:")
        context_parts.extend(location_info[:min(5, len(location_info))])
    
    # Add menu sections
    if menu_sections:
        context_parts.append("\nMENU SECTIONS:")
        context_parts.extend(menu_sections[:min(8, len(menu_sections))])
    
    # Add individual menu items
    if menu_items:
        context_parts.append("\nMENU ITEMS:")
        context_parts.extend(menu_items[:min(12, len(menu_items))])
    
    # Join all parts
    context = "\n\n".join(context_parts)
    
    # Limit context size if extremely large
    max_chars = 16000
    if len(context) > max_chars:
        context = context[:max_chars] + "...\n[Context truncated due to size]"
    
    return context 