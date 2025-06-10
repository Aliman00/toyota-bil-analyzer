# filepath: /toyota-bil-analyzer/toyota-bil-analyzer/main.py
import os
import requests
import re
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()  # Load environment variables from .env file

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

#finn_url = "https://www.finn.no/mobility/search/car?fuel=6&fuel=1352&location=20061&location=20007&location=20003&location=20002&model=1.813.3074&model=1.813.2000660&price_to=350000&registration_class=1&sales_form=1&sort=MILEAGE_ASC&stored-id=80223608&wheel_drive=2&year_from=2019"
finn_url = "https://www.finn.no/mobility/search/car?location=20007&location=20061&location=20003&location=20002&model=1.813.3074&model=1.813.2000660&price_to=380000&sales_form=1&sort=MILEAGE_ASC&stored-id=80260642&wheel_drive=2&year_from=2019"

def fetch_car_data(url_to_fetch: str) -> str | None:
    """Fetches the raw HTML content from the given URL."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url_to_fetch, headers=headers, timeout=10)
        response.raise_for_status()

        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {url_to_fetch}: {e}")
        return None


def parse_car_data(html_content: str) -> list:
    """Parses car data from raw HTML content using BeautifulSoup."""
    if not html_content:
        return []

    soup = BeautifulSoup(html_content, 'lxml')
    parsed_cars_list = []
    current_year = 2025 # As per environment date and reference function
    successful_car_id_counter = 0 # Initialize a counter for successfully parsed cars

    # Find the main tag with a class that starts with "page-container"
    main_element = soup.find('main', class_=re.compile(r"page-container"))
    if not main_element:
        return []

    # CSS selector to navigate to the container of car listings
    ads_container_selector = 'div:nth-of-type(1) > div:nth-of-type(2) > section > div:nth-of-type(3)'
    ads_container = main_element.select_one(ads_container_selector)
    if not ads_container:
        return []

    # Get all direct div children of ads_container
    car_item_wrapper_divs = ads_container.find_all('div', recursive=False)
    if not car_item_wrapper_divs:
        return []

    # Iterate through potential car ad wrappers without using enumerate for ID
    for car_wrapper_div in car_item_wrapper_divs: 
        article_element = car_wrapper_div.find('article', recursive=False)
        if not article_element:
            article_element = car_wrapper_div.find('article') 
            if not article_element:
                continue # This div doesn't contain an article, skip (e.g., it's an ad)
        
        # Initialize dictionary for this potential car
        car_info = {
            # 'id' will be assigned later if parsing is successful
            'name': None,
            'link': None,
            'image_url': None,
            'additional_info': None,
            'year': None,
            'mileage': None,
            'price': None,
            'age': None,
            'km_per_year': None
        }

        # Image URL
        image_tag = article_element.select_one('div:nth-of-type(2) > div > img')
        if image_tag:
            car_info['image_url'] = image_tag.get('src') or image_tag.get('data-src')

        # Main info container
        info_div = article_element.select_one('div:nth-of-type(3)')
        
        if info_div:
            # Car Name (Model) and Ad Link
            name_tag = info_div.find('h2')
            if name_tag:
                car_info['name'] = name_tag.get_text(strip=True)
                link_tag = name_tag.find('a')
                if link_tag and link_tag.has_attr('href'):
                    ad_url = link_tag['href']
                    if ad_url.startswith('/'):
                        base_url = "https://www.finn.no" # Adjust if needed
                        ad_url = base_url + ad_url
                    car_info['link'] = ad_url
                else:
                    car_info['link'] = "Not found" # Or None

            # Additional Info
            additional_info_tag = info_div.find('span', class_='text-caption')
            if additional_info_tag:
                car_info['additional_info'] = additional_info_tag.get_text(strip=True)
            else:
                car_info['additional_info'] = "Not found" # Or None

            # Year and Mileage details
            details_tag = info_div.select_one('span:nth-of-type(2)')
            if details_tag:
                details_text = details_tag.get_text(strip=True)
                
                year_match = re.search(r'\b(19\d{2}|20\d{2})\b', details_text)
                if year_match:
                    year_str = year_match.group(0)
                    if year_str.isdigit():
                        car_info['year'] = int(year_str)
                        car_info['age'] = current_year - car_info['year']
                
                mileage_match = re.search(r'(\d[\d\s.,]*\s*km)\b', details_text, re.IGNORECASE)
                if mileage_match:
                    raw_mileage_text = mileage_match.group(1)
                    # Clean mileage: remove "km", non-digits (except for internal spaces that were part of the number)
                    mileage_str_cleaned = re.sub(r'[^\d]', '', raw_mileage_text.lower().replace('km', ''))
                    if mileage_str_cleaned.isdigit():
                        car_info['mileage'] = int(mileage_str_cleaned)

            # Calculate km_per_year
            if car_info['mileage'] is not None and car_info['age'] is not None:
                if car_info['age'] > 0:
                    car_info['km_per_year'] = round(car_info['mileage'] / car_info['age'])
                elif car_info['age'] == 0: # Car is from the current year
                    car_info['km_per_year'] = car_info['mileage'] 
            
            # Price
            price_tag = info_div.select_one('div:nth-of-type(1)')
            if price_tag:
                price_text = price_tag.get_text(strip=True)
                # Check for "Solgt" or similar text if applicable from HTML
                if "solgt" in price_text.lower(): # Basic check for "Solgt"
                    car_info['price'] = "Solgt"
                else:
                    price_digits = re.sub(r'[^\d]', '', price_text)
                    if price_digits:
                        car_info['price'] = int(price_digits)
                    # else: car_info['price'] remains None if no digits and not "Solgt"

        # Only add to list if essential data like name was found
        if car_info.get('name'): 
            successful_car_id_counter += 1 # Increment counter for successfully parsed car
            car_info['id'] = successful_car_id_counter # Assign the sequential ID
            parsed_cars_list.append(car_info)

    return parsed_cars_list
