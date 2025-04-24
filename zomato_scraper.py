import os
import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Function to set up and return a Selenium WebDriver
def get_driver():
    options = Options()
    options.headless = True  # Run in headless mode to avoid opening a browser window
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

# Function to scrape the restaurant URLs from the main page
def get_restaurant_links(driver, url):
    driver.get(url)
    time.sleep(3)  # Allow time for JavaScript to render
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    restaurant_links = []
    
    # Scrape the restaurant URLs (including the image)
    for a in soup.select("a.sc-hqGPoI.kCiEKB"):  # Using your provided class
        href = a.get("href")
        image = a.find("img")["src"] if a.find("img") else None  # Extract image URL
        if href and href.startswith("/mumbai/"):
            full_url = "https://www.zomato.com" + href
            if full_url not in restaurant_links:
                restaurant_links.append({"url": full_url, "image": image})

    return restaurant_links

def scrape_restaurant_details(driver, url):
    try:
        driver.get(url)
        time.sleep(3)

        # Try to find the "Order Online" button with multiple possible selectors
        order_button = None
        selectors = [
            'a.sc-dENsGg.jTakJE',
            'a[href*="order"]',  # More generic selector for order links
            'a[data-testid*="order"]'  # Another common pattern
        ]
        
        for selector in selectors:
            try:
                order_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                if order_button:
                    break
            except Exception:
                continue
                
        if not order_button:
            print(f"[Warning] Could not find 'Order Online' button for {url}")
            # Proceed without order data
        else:
            order_url = order_button.get_attribute('href')
            driver.get(order_url)
            time.sleep(5)

            # Scroll to load all menu
            last_height = driver.execute_script("return document.body.scrollHeight")
            while True:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

        menu_soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Go back to main restaurant page for info
        driver.get(url)
        time.sleep(3)
        info_soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Extract restaurant info with fallback selectors
        name = "N/A"
        name_tag = info_soup.find("h1", class_="sc-7kepeu-0 sc-iSDuPN fwzNdh")
        if not name_tag:
            name_tag = info_soup.find("h1")  # Fallback to any h1
        if name_tag:
            name = name_tag.get_text(strip=True)

        location = "N/A"
        location_tag = info_soup.find("div", class_="sc-clNaTc ckqoPM")
        if not location_tag:
            location_tag = info_soup.find("a", {"href": lambda x: x and "/mumbai/" in x})
        if location_tag:
            location = location_tag.get_text(strip=True)

        opening_time = "N/A"
        opening_tag = info_soup.find("span", class_="sc-kasBVs dfwCXs")
        if opening_tag:
            opening_time = opening_tag.get_text(strip=True).replace("\u2013", "-")

        rating = "N/A"
        rating_tag = info_soup.find("div", class_="sc-1q7bklc-1 cILgox")
        if rating_tag:
            rating = rating_tag.get_text(strip=True)

        contact = "N/A"
        contact_tag = info_soup.find("a", class_="sc-bFADNz leEVAg")
        if contact_tag:
            contact = contact_tag.get_text(strip=True)

        special_features = []
        special_features_tags = info_soup.find_all("p", class_="sc-1hez2tp-0 cunMUz")
        if special_features_tags:
            special_features = [tag.get_text(strip=True) for tag in special_features_tags]

        menu_items = []
        
        # Try different selectors for menu cards
        menu_card_selectors = [
            "div.sc-iipuKH.ethBdQ",
            "div[data-testid*='menu-item']",
            "div.sc-iipuKH",
            "div",
            "div.sc-fwyeXZ fhjzPM sc-cpUXGm izLoCo"
        ]
        
        menu_cards = []
        for selector in menu_card_selectors:
            menu_cards = menu_soup.select(selector)
            if menu_cards:
                break
                
        for card in menu_cards:
            # Extract item name (h4, h3, h5, or strong)
            item_name = card.find("h4", class_="sc-cGCqpu chKhYc")
            if not item_name:
                item_name = card.find("h4") or card.find(["h3", "h5", "strong"])
            
            # Extract price (span with class or text containing ₹)
            price = card.find("span", class_="sc-17hyc2s-1 cCiQWA")
            if not price:
                price = card.find(text=lambda t: t and "₹" in t)
                if price and not hasattr(price, 'get_text'):
                    price = price.parent
            
            # Extract description (p tag with class or generic p tag)
            desc = card.find("p", class_="sc-gsxalj jqiNmO")
            if not desc:
                desc = card.find("p")
            
            # Extract tag (if available)
            tag_tag = card.find("div", class_="sc-2gamf4-0 fSJGVb")
            tag = tag_tag.get_text(strip=True) if tag_tag else None
            
            # Extract food type (veg, non-veg, or egg)
            food_type = "unknown"
            
            # First check if the description itself mentions veg or non-veg
            if desc:
                desc_text = desc.get_text(strip=True).lower()
                if "[veg" in desc_text or "[vegetarian" in desc_text or "veg preparation" in desc_text:
                    food_type = "veg"
                elif "[non-veg" in desc_text or "[non veg" in desc_text:
                    food_type = "non-veg"
                elif "[dairy free]" in desc_text.lower():
                    # Dairy-free items are often vegan/vegetarian
                    food_type = "veg"
            
            # Also check for food type in the name - some items clearly indicate vegetarian/non-vegetarian
            if food_type == "unknown" and item_name:
                name_text = item_name.get_text(strip=True).lower()
                if "chicken" in name_text or "fish" in name_text or "beef" in name_text or "mutton" in name_text or "prawn" in name_text or "egg" in name_text:
                    food_type = "non-veg"
                elif "paneer" in name_text or "tofu" in name_text or "veg" in name_text:
                    food_type = "veg"
            
            # Extract item name text
            item_name_text = item_name.get_text(strip=True) if item_name else None
            
            # Only add items with at least a name
            if item_name_text:
                menu_items.append({
                    "name": item_name_text,
                    "price": price.get_text(strip=True).replace("\u20b9", "₹") if price else "N/A",
                    "description": desc.get_text(strip=True) if desc else "N/A",
                    "tag": tag,
                    "food_type": food_type
                })


        # Create base restaurant data
        restaurant_data = {
            "name": name,
            "location": location,
            "hours": opening_time,
            "rating": rating,
            "contact": contact,
            "features": special_features
        }

        # Only add menu_items if we found any
        if menu_items:
            restaurant_data["menu_items"] = menu_items

        return restaurant_data
    except Exception as e:
        print(f"[Error] Failed to scrape {url}: {e}")
        return None

# Main function
def main():
    base_url = "https://www.zomato.com/mumbai/best-dine-out-restaurants"
    
    driver = get_driver()
    restaurant_links = get_restaurant_links(driver, base_url)
    data = []
    
    # Try to process at least 5 restaurants
    for restaurant in restaurant_links[:17]:  # Increased from 1 to 10
        print(f"Scraping {restaurant['url']}...")
        details = scrape_restaurant_details(driver, restaurant['url'])
        if details is not None and "menu_items" in details and details["menu_items"]:
            # Store the image URL in a photos array for consistency
            if restaurant["image"]:
                print(f"Found image URL: {restaurant['image']}")
                details["photos"] = [
                    {
                        "url": restaurant["image"],
                        "alt_text": f"{details['name']} photo"
                    }
                ]
                # Debug - confirm photos was added
                print(f"Added photos array with {len(details['photos'])} items")
            else:
                print("No image URL found for this restaurant")
                
            details["url"] = restaurant["url"]  # Add restaurant URL to the data
            
            # Remove any old 'image' field that might exist
            if "image" in details:
                del details["image"]
                
            data.append(details)
        else:
            print(f"Skipping {restaurant['url']} due to missing menu items or scraping error")
        
        # Add a longer delay between restaurants to avoid rate limiting
        time.sleep(5)
    
    driver.quit()
    
    # Process the data to replace Unicode rupee symbol with actual rupee symbol
    def replace_rupee_unicode(item):
        if isinstance(item, dict):
            for key, value in item.items():
                if isinstance(value, str):
                    item[key] = value.replace("\u20b9", "₹")
                elif isinstance(value, (list, dict)):
                    replace_rupee_unicode(value)
        elif isinstance(item, list):
            for i in range(len(item)):
                if isinstance(item[i], str):
                    item[i] = item[i].replace("\u20b9", "₹")
                elif isinstance(item[i], (list, dict)):
                    replace_rupee_unicode(item[i])
    
    # Apply the rupee symbol replacement to the entire dataset
    replace_rupee_unicode(data)
    
    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    # Save data to a JSON file in the data folder
    with open("restaurant_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    
    print(f"Saved data of {len(data)} restaurants to data/restaurant_data.json ✅")

# Run the scraper
if __name__ == "__main__":
    main()