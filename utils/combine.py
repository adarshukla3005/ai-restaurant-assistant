import os
import json
import csv
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("combine.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_json_file(file_path):
    """Load and parse a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from {file_path}")
        return None
    except Exception as e:
        logger.error(f"Error loading file {file_path}: {e}")
        return None

def combine_json_files():
    """Combine all JSON files in the data directory."""
    data_dir = Path('data')
    combined_data = []
    
    if not data_dir.exists():
        logger.error(f"Data directory {data_dir} does not exist")
        return None
    
    # List all JSON files
    json_files = list(data_dir.glob('*.json'))
    logger.info(f"Found {len(json_files)} JSON files in the data directory")
    
    # Process each file
    for file_path in json_files:
        logger.info(f"Processing {file_path}")
        data = load_json_file(file_path)
        if data:
            # Add the filename as source
            data['source_file'] = file_path.name
            combined_data.append(data)
        else:
            logger.warning(f"Skipping {file_path} due to errors")
    
    logger.info(f"Successfully combined {len(combined_data)} JSON files")
    return combined_data

def save_combined_json(data, output_path):
    """Save combined data to a JSON file."""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Successfully saved combined JSON to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving JSON to {output_path}: {e}")
        return False

def flatten_menu_items(restaurant):
    """Flatten menu items for CSV export."""
    flattened_items = []
    restaurant_name = restaurant.get('name', 'Unknown')
    address = restaurant.get('address', 'N/A')
    cuisines = ','.join(restaurant.get('cuisines', []))
    rating = restaurant.get('rating', 'N/A')
    cost_for_two = restaurant.get('cost_for_two', 'N/A')
    
    # Process menu items
    for item in restaurant.get('menu_items', []):
        flattened_item = {
            'restaurant_name': restaurant_name,
            'address': address,
            'cuisines': cuisines,
            'rating': rating,
            'cost_for_two': cost_for_two,
            'item_name': item.get('name', 'N/A'),
            'price': item.get('price', 'N/A'),
            'description': item.get('description', 'N/A'),
            'food_type': item.get('food_type', 'N/A')
        }
        flattened_items.append(flattened_item)
    
    # Process photos
    photos = restaurant.get('photos', [])
    if photos:
        photo_urls = [photo.get('url', 'N/A') for photo in photos]
        for item in flattened_items:
            item['photo_urls'] = ','.join(photo_urls[:2])  # Add only first two photos
    else:
        for item in flattened_items:
            item['photo_urls'] = 'N/A'
            
    return flattened_items

def main():
    """Main function to combine JSON files and save as JSON and CSV."""
    try:
        # Create data directory if it doesn't exist
        data_dir = Path('data')
        data_dir.mkdir(exist_ok=True)
        
        # Combine JSON files
        combined_data = combine_json_files()
        if not combined_data:
            logger.error("No data to combine")
            return
        
        # Save as combined JSON
        json_output = data_dir / 'combined_restaurants.json'
        save_combined_json(combined_data, json_output)
        
        logger.info("Combination process completed successfully")
        
    except Exception as e:
        logger.error(f"An error occurred in the main function: {e}")

if __name__ == "__main__":
    main()
