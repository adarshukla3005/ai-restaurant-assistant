import json
import os
import sys
import time

# Add parent directory to path to import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.vector_db import (
    setup_chromadb,
    create_restaurant_document, 
    create_menu_item_document,
    create_cuisine_document,
    create_location_document,
    create_menu_section_document
)

# Current directory 
CURRENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# File paths with absolute paths
NORMALIZED_FILE = os.path.join(CURRENT_DIR, "data", "normalized_zomato_data.json")
BATCH_SIZE = 100

def insert_into_chromadb():
    """
    Insert normalized restaurant data with URLs into ChromaDB
    """
    start_time = time.time()
    
    # Load the normalized data with URLs
    try:
        with open(NORMALIZED_FILE, "r", encoding="utf-8") as f:
            restaurants = json.load(f)
            
        print(f"Loaded {len(restaurants)} restaurants from {NORMALIZED_FILE}")
    except Exception as e:
        print(f"Error loading normalized data: {str(e)}")
        return 0
    
    # Initialize ChromaDB
    collection = setup_chromadb()
    
    try:
        print(f"Processing {len(restaurants)} restaurants for ChromaDB insertion")
        
        # Initialize empty lists for batch processing
        ids = []
        documents = []
        metadatas = []
        
        # Process each restaurant
        for idx, restaurant in enumerate(restaurants):
            # Use a different index offset for the new data to avoid overwriting existing entries
            idx_offset = 20000 + idx  # Using 20000 as offset to ensure we don't conflict with previous data
            
            # 1. Create a document for the restaurant overview
            restaurant_info = create_restaurant_document(restaurant)
            
            # Add to batch
            doc_id = f"restaurant_url_{idx_offset}"
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
                
                doc_id = f"item_url_{idx_offset}_{menu_idx}"
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
                
                doc_id = f"cuisine_url_{idx_offset}"
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
            
            doc_id = f"location_url_{idx_offset}"
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
                
                doc_id = f"menu_url_{idx_offset}_{food_type}"
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
            print(f"Added batch: {i} to {end_idx} ({len(batch_ids)} items)")
        
        elapsed_time = time.time() - start_time
        print(f"Added {total_added} documents to ChromaDB in {elapsed_time:.2f} seconds")
        
        return total_added
        
    except Exception as e:
        print(f"Error adding data to ChromaDB: {str(e)}")
        raise

def main():
    """Main function to run the ChromaDB insertion"""
    try:
        print("Starting insertion of normalized data with URLs into ChromaDB")
        total_added = insert_into_chromadb()
        
        print(f"Successfully added {total_added} documents to ChromaDB")
        
    except Exception as e:
        print(f"Error in insertion process: {str(e)}")
        raise

if __name__ == "__main__":
    main() 