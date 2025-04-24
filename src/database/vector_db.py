"""
This module handles vector database operations for the agentic chatbot.
"""
import os
import json
import time
import logging
import streamlit as st
import chromadb
from src.models.embeddings import get_embedding_function

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database settings
COLLECTION_NAME = "restaurant_data"
BATCH_SIZE = 100
DATA_FILE = "data/1combined_restaurants.json"
CHROMA_PERSIST_DIR = "chroma_db"

@st.cache_resource
def setup_chromadb():
    
    # Create a persistent client with the specified directory
    client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    
    # Get embedding function
    embedding_func = get_embedding_function()
    
    # Check if collection already exists
    try:
        # Try to get the existing collection first
        collection = client.get_collection(
            name=COLLECTION_NAME,
            embedding_function=embedding_func
        )
        logger.info(f"Connected to existing vector database with {collection.count()} documents")
    except Exception:
        # Collection doesn't exist, create it and load data
        collection = client.create_collection(
            name=COLLECTION_NAME,
            embedding_function=embedding_func
        )
        
        # Load data into collection
        with st.spinner("Setting up database for the first time..."):
            load_restaurant_data(collection)
    
    return collection

def load_restaurant_data(collection):

    # Load restaurant data from JSON file and add to ChromaDB collection.

    start_time = time.time()
    
    try:
        # Load the data file
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            restaurant_data = json.load(f)
        
        logger.info(f"Processing {len(restaurant_data)} restaurants...")
        
        # Initialize empty lists for batch processing
        ids = []
        documents = []
        metadatas = []
        
        # Process each restaurant
        for idx, restaurant in enumerate(restaurant_data):
            # 1. Create a document for the restaurant overview
            restaurant_info = create_restaurant_document(restaurant)
            
            # Add to batch
            doc_id = f"restaurant_{idx}"
            ids.append(doc_id)
            documents.append(restaurant_info)
            metadatas.append({
                "type": "restaurant_info",
                "name": restaurant.get('name', 'Unknown'),
                "location": restaurant.get('location', 'Unknown'),
                "rating": restaurant.get('rating', 'Unknown'),
                "cuisines": ",".join(restaurant.get('cuisines', [])),
                "cost": restaurant.get('cost_for_two', 'Unknown'),
                "url": restaurant.get('url', 'Unknown'),
                "contact": restaurant.get('contact', 'Unknown'),
                "address": restaurant.get('address', 'Unknown')
            })
            
            # 2. Add all menu items individually for better search coverage
            menu_items = restaurant.get('menu_items', [])
            for menu_idx, item in enumerate(menu_items):
                menu_item_info = create_menu_item_document(restaurant, item)
                
                doc_id = f"item_{idx}_{menu_idx}"
                ids.append(doc_id)
                documents.append(menu_item_info)
                metadatas.append({
                    "type": "menu_item",
                    "restaurant": restaurant.get('name', 'Unknown'),
                    "food_type": item.get('food_type', 'Unknown'),
                    "item_name": item.get('name', 'Unknown'),
                    "price": item.get('price', 'Unknown'),
                    "restaurant_location": restaurant.get('location', 'Unknown'),
                    "restaurant_cuisines": ",".join(restaurant.get('cuisines', [])),
                    "restaurant_rating": restaurant.get('rating', 'Unknown'),
                    "restaurant_url": restaurant.get('url', 'Unknown')
                })
            
            # 3. Create searchable cuisine documents for each restaurant
            cuisines = restaurant.get('cuisines', [])
            if cuisines:
                cuisine_info = create_cuisine_document(restaurant, cuisines)
                
                doc_id = f"cuisine_{idx}"
                ids.append(doc_id)
                documents.append(cuisine_info)
                metadatas.append({
                    "type": "cuisine_info",
                    "restaurant": restaurant.get('name', 'Unknown'),
                    "cuisines": ",".join(cuisines),
                    "location": restaurant.get('location', 'Unknown'),
                    "rating": restaurant.get('rating', 'Unknown'),
                    "cost": restaurant.get('cost_for_two', 'Unknown'),
                    "url": restaurant.get('url', 'Unknown')
                })
            
            # 4. Create searchable location documents
            location_info = create_location_document(restaurant)
            
            doc_id = f"location_{idx}"
            ids.append(doc_id)
            documents.append(location_info)
            metadatas.append({
                "type": "location_info",
                "restaurant": restaurant.get('name', 'Unknown'),
                "location": restaurant.get('location', 'Unknown'),
                "address": restaurant.get('address', 'Unknown'),
                "cuisines": ",".join(restaurant.get('cuisines', [])),
                "rating": restaurant.get('rating', 'Unknown'),
                "cost": restaurant.get('cost_for_two', 'Unknown'),
                "url": restaurant.get('url', 'Unknown')
            })
            
            # 5. Group menu items by food type for categorized searching
            menu_by_type = {}
            for item in menu_items:
                food_type = item.get('food_type', 'Other')
                if food_type not in menu_by_type:
                    menu_by_type[food_type] = []
                menu_by_type[food_type].append(item)
            
            # Create a document for each food type
            for food_type, items in menu_by_type.items():
                menu_info = create_menu_section_document(restaurant, food_type, items)
                
                doc_id = f"menu_{idx}_{food_type}"
                ids.append(doc_id)
                documents.append(menu_info)
                metadatas.append({
                    "type": "menu_section",
                    "restaurant": restaurant.get('name', 'Unknown'),
                    "food_type": food_type,
                    "item_count": len(items),
                    "location": restaurant.get('location', 'Unknown'),
                    "cuisines": ",".join(restaurant.get('cuisines', [])),
                    "rating": restaurant.get('rating', 'Unknown'),
                    "cost": restaurant.get('cost_for_two', 'Unknown'),
                    "url": restaurant.get('url', 'Unknown')
                })
        
        # Add data to collection in batches
        total_added = 0
        for i in range(0, len(ids), BATCH_SIZE):
            end_idx = min(i + BATCH_SIZE, len(ids))
            batch_ids = ids[i:end_idx]
            batch_docs = documents[i:end_idx]
            batch_meta = metadatas[i:end_idx]
            
            collection.add(
                ids=batch_ids,
                documents=batch_docs,
                metadatas=batch_meta
            )
            total_added += len(batch_ids)
        
        elapsed_time = time.time() - start_time
        logger.info(f"Vector database created with {total_added} documents in {elapsed_time:.2f} seconds")
        
        return total_added
        
    except Exception as e:
        logger.error(f"Error loading restaurant data: {str(e)}")
        st.error("There was an error loading the restaurant data.")
        return 0

def create_restaurant_document(restaurant):
    """
    Create a document for restaurant overview information.
    
    Args:
        restaurant: Restaurant data dictionary
        
    Returns:
        str: Formatted document text
    """
    # Format hours of operation if available
    hours_info = ""
    if operational_hours := restaurant.get('operational_hours'):
        hours_info = "Hours of Operation:\n"
        for day, hours in operational_hours.items():
            hours_info += f"  {day}: {hours}\n"
    
    # Format cuisines if available
    cuisines_text = ", ".join(restaurant.get('cuisines', []))
    
    # Format photos if available
    photos_info = ""
    if photos := restaurant.get('photos', []):
        photos_info = "Photos:\n"
        for photo_url in photos:
            photos_info += f"  {photo_url}\n"
    
    # Format menu items summary
    menu_summary = ""
    if menu_items := restaurant.get('menu_items', []):
        menu_summary = f"Menu Items: {len(menu_items)} items available\n"
    
    # Create a more searchable document with clear field markers
    return (
        f"Restaurant Name: {restaurant.get('name', '')}\n"
        f"Location: {restaurant.get('location', '')}\n"
        f"Cost for Two: {restaurant.get('cost_for_two', '')}\n"
        f"Rating: {restaurant.get('rating', '')}\n"
        f"Website URL: {restaurant.get('url', '')}\n"
        f"Address: {restaurant.get('address', '')}\n"
        f"Contact: {restaurant.get('contact', '')}\n"
        f"Cuisines: {cuisines_text}\n"
        f"{hours_info}\n"
        f"{photos_info}\n"
        f"{menu_summary}\n"
        f"Description: {restaurant.get('description', '')}\n"
    )

def create_menu_section_document(restaurant, food_type, menu_items):
    """
    Create a document for a menu section grouped by food type.
    
    Args:
        restaurant: Restaurant data dictionary
        food_type: Type of food for this section
        menu_items: List of menu items in this section
        
    Returns:
        str: Formatted document text
    """
    # Format menu items with detailed information
    items_text = "\n".join([
        f"  • Item: {item.get('name', '')}\n    Price: {item.get('price', '')}\n    Description: {item.get('description', '')}"
        for item in menu_items
    ])
    
    # Create document with comprehensive restaurant information
    return (
        f"Restaurant: {restaurant.get('name', '')}\n"
        f"Food Category: {food_type}\n"
        f"Restaurant Details:\n"
        f"  - Location: {restaurant.get('location', '')}\n"
        f"  - Address: {restaurant.get('address', '')}\n"
        f"  - Cuisines: {', '.join(restaurant.get('cuisines', []))}\n"
        f"  - Rating: {restaurant.get('rating', '')}\n"
        f"  - Cost for Two: {restaurant.get('cost_for_two', '')}\n"
        f"  - Website: {restaurant.get('url', '')}\n"
        f"  - Contact: {restaurant.get('contact', '')}\n"
        f"\nMenu Items ({len(menu_items)} items in {food_type} category):\n{items_text}\n"
    )

def create_menu_item_document(restaurant, item):
    """
    Create a document for an individual menu item.
    
    Args:
        restaurant: Restaurant data dictionary
        item: Menu item dictionary
        
    Returns:
        str: Formatted document text
    """
    return (
        f"Restaurant: {restaurant.get('name', '')}\n"
        f"Menu Item: {item.get('name', '')}\n"
        f"Price: {item.get('price', '')}\n"
        f"Food Type: {item.get('food_type', '')}\n"
        f"Description: {item.get('description', '')}\n"
        f"Restaurant Info:\n"
        f"  - Cuisines: {', '.join(restaurant.get('cuisines', []))}\n"
        f"  - Location: {restaurant.get('location', '')}\n"
        f"  - Address: {restaurant.get('address', '')}\n"
        f"  - Rating: {restaurant.get('rating', '')}\n"
        f"  - Cost for Two: {restaurant.get('cost_for_two', '')}\n"
        f"  - Website: {restaurant.get('url', '')}\n"
        f"  - Contact: {restaurant.get('contact', '')}\n"
    )

def create_cuisine_document(restaurant, cuisines):
    """
    Create a searchable document focused on cuisines.
    
    Args:
        restaurant: Restaurant data dictionary
        cuisines: List of cuisines
        
    Returns:
        str: Formatted document text
    """
    # Format menu items with this cuisine
    menu_items = restaurant.get('menu_items', [])
    matching_items = []
    
    for item in menu_items:
        food_type = item.get('food_type', '').lower()
        if any(cuisine.lower() in food_type for cuisine in cuisines):
            matching_items.append(f"- {item.get('name', '')}: {item.get('price', '')}")
    
    cuisine_menu_items = "\n".join(matching_items[:10])  # Limit to avoid too large documents
    if len(matching_items) > 10:
        cuisine_menu_items += f"\n... and {len(matching_items) - 10} more items"
    
    return (
        f"Restaurant: {restaurant.get('name', '')}\n"
        f"Cuisine Types: {', '.join(cuisines)}\n"
        f"Restaurant serves {', '.join(cuisines)} food.\n"
        f"Location: {restaurant.get('location', '')}\n"
        f"Address: {restaurant.get('address', '')}\n"
        f"Rating: {restaurant.get('rating', '')}\n"
        f"Cost for Two: {restaurant.get('cost_for_two', '')}\n"
        f"Website: {restaurant.get('url', '')}\n"
        f"Contact: {restaurant.get('contact', '')}\n"
        f"\nPopular items in these cuisines:\n{cuisine_menu_items if matching_items else 'No specific items found'}\n"
    )

def create_location_document(restaurant):
    """
    Create a searchable document focused on location.
    
    Args:
        restaurant: Restaurant data dictionary
        
    Returns:
        str: Formatted document text
    """
    # Format operating hours if available
    hours_info = ""
    if operational_hours := restaurant.get('operational_hours'):
        hours_info = "Hours of Operation:\n"
        for day, hours in operational_hours.items():
            hours_info += f"  {day}: {hours}\n"
    
    return (
        f"Restaurant: {restaurant.get('name', '')}\n"
        f"Location: {restaurant.get('location', '')}\n"
        f"Full Address: {restaurant.get('address', '')}\n"
        f"This restaurant is located in {restaurant.get('location', '')}.\n"
        f"Contact: {restaurant.get('contact', '')}\n"
        f"Website: {restaurant.get('url', '')}\n"
        f"Cuisines: {', '.join(restaurant.get('cuisines', []))}\n"
        f"Rating: {restaurant.get('rating', '')}\n"
        f"Cost for Two: {restaurant.get('cost_for_two', '')}\n"
        f"{hours_info}\n"
    )

def query_database(query, collection, n_results=20):
    """
    Query the vector database for relevant documents.
    
    Args:
        query (str): The user query to find relevant documents for
        collection: ChromaDB collection to query
        n_results (int): Number of results to return (default increased to 20)
        
    Returns:
        dict: Query results from ChromaDB
    """
    # Increased n_results to ensure comprehensive coverage and more restaurant options
    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        include=["documents", "metadatas", "distances"]
    )
    return results 