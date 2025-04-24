import json
import os

# File paths
CURRENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESTAURANT_DATA_FILE = os.path.join(CURRENT_DIR, "data", "restaurant_data.json")
OUTPUT_FILE = os.path.join(CURRENT_DIR, "data", "normalized_with_urls.json")

def extract_normalized_data_with_urls():
    """
    Extract restaurant data, normalize it, and add URLs
    """
    try:
        # Load the restaurant data
        with open(RESTAURANT_DATA_FILE, "r", encoding="utf-8") as f:
            restaurants = json.load(f)
        
        print(f"Processing {len(restaurants)} restaurants")
        
        normalized_restaurants = []
        
        for restaurant in restaurants:
            # Extract and normalize data
            normalized_restaurant = {
                "name": restaurant.get("name", ""),
                "location": restaurant.get("location", ""),
                "cost_for_two": f"Cost for two: ₹{restaurant.get('cost_for_two', '1000')}",
                "rating": restaurant.get("rating", ""),
                "url": restaurant.get("url", ""),  # Include URL from original data
                "address": restaurant.get("location", ""),
                "contact": restaurant.get("contact", ""),
                "description": f"{restaurant.get('name', '')} is a restaurant located at {restaurant.get('location', '')}.",
                "cuisines": extract_cuisines_from_features(restaurant.get("features", [])),
                "operational_hours": format_hours(restaurant.get("hours", "")),
                "menu_items": normalize_menu_items(restaurant.get("menu_items", []))
            }
            
            normalized_restaurants.append(normalized_restaurant)
        
        # Save normalized data with URLs
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(normalized_restaurants, f, indent=2, ensure_ascii=False)
        
        print(f"Normalized data with URLs saved to {OUTPUT_FILE}")
        return normalized_restaurants
        
    except Exception as e:
        print(f"Error processing data: {str(e)}")
        raise

def extract_cuisines_from_features(features):
    """
    Extract cuisine types from features list
    """
    # Common cuisine types to look for in features
    cuisine_keywords = [
        "Chinese", "Italian", "Indian", "Mexican", "Thai", "Japanese", 
        "Mediterranean", "French", "American", "Continental", "Mughlai",
        "South Indian", "North Indian", "Fast Food", "Desserts", "Bakery",
        "Cafe", "Pizzeria", "Grill", "BBQ", "Seafood", "Vegetarian", "Vegan"
    ]
    
    # Extract cuisines that match keywords
    cuisines = [feature for feature in features if any(cuisine.lower() in feature.lower() for cuisine in cuisine_keywords)]
    
    # If no cuisines found, add some default categories based on features
    if not cuisines:
        if "Breakfast" in features:
            cuisines.append("Breakfast")
        if "Gluten Free Options" in features or "Gluten Free" in features:
            cuisines.append("Gluten Free")
        if not cuisines:  # Still no cuisines, add a generic one
            cuisines.append("Contemporary")
    
    return cuisines

def format_hours(hours_str):
    """
    Format hours string to operational_hours format
    Example input: "11am - 11pm (Today)"
    Example output: {"MONDAY": "11:00:00 - 23:00:00", ...}
    """
    # Default hours if parsing fails
    default_hours = "11:00:00 - 23:00:00"
    
    # Extract hours from string like "11am - 11pm (Today)"
    try:
        hours_part = hours_str.split(" (")[0]
        open_time, close_time = hours_part.split(" - ")
        
        # Convert to 24-hour format
        open_24h = convert_to_24h(open_time)
        close_24h = convert_to_24h(close_time)
        
        formatted_hours = f"{open_24h} - {close_24h}"
    except:
        formatted_hours = default_hours
    
    # Apply the same hours to all days
    return {
        "MONDAY": formatted_hours,
        "TUESDAY": formatted_hours,
        "WEDNESDAY": formatted_hours,
        "THURSDAY": formatted_hours,
        "FRIDAY": formatted_hours,
        "SATURDAY": formatted_hours,
        "SUNDAY": formatted_hours
    }

def convert_to_24h(time_str):
    """
    Convert 12-hour time format to 24-hour format
    Example: "11am" -> "11:00:00", "9pm" -> "21:00:00"
    """
    if "am" in time_str.lower():
        hour = time_str.lower().replace("am", "").strip()
        hour = int(hour)
        if hour == 12:  # 12am is 00:00
            hour = 0
    else:
        hour = time_str.lower().replace("pm", "").strip()
        hour = int(hour)
        if hour < 12:  # 1pm-11pm add 12 hours
            hour += 12
    
    return f"{hour:02d}:00:00"

def normalize_menu_items(menu_items):
    """
    Normalize menu items to match the expected format
    """
    normalized_items = []
    
    for item in menu_items:
        food_type = normalize_food_type(item.get("food_type", "unknown"))
        
        normalized_item = {
            "name": item.get("name", ""),
            "price": item.get("price", ""),
            "description": item.get("description", ""),
            "food_type": food_type
        }
        
        normalized_items.append(normalized_item)
    
    return normalized_items

def normalize_food_type(food_type):
    """
    Normalize food type to match expected format (Veg, Non-Veg, Egg)
    """
    if not food_type or food_type == "unknown":
        return "Veg"  # Default to Veg if unknown
    
    food_type = food_type.lower()
    
    if "non" in food_type or "non-veg" in food_type:
        return "Non-Veg"
    elif "egg" in food_type:
        return "Egg"
    else:
        return "Veg"

def main():
    extract_normalized_data_with_urls()

if __name__ == "__main__":
    main() 