import requests
from datetime import datetime, timedelta
import urllib.parse
import os
from dotenv import load_dotenv
load_dotenv()
# Configuration
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')


def get_location_coordinates(location_name):
    """
    Get the latitude and longitude of a location using Google Geocoding API.
    """
    # URL encode the location name to handle spaces and special characters
    encoded_location_name = urllib.parse.quote(location_name)
    geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_location_name}&key={GOOGLE_API_KEY}"
    response = requests.get(geocode_url)
    location_data = response.json()

    print(f"Geocoding API Response: {location_data}")  # Debugging output

    if location_data['status'] == 'OK':
        location = location_data['results'][0]['geometry']['location']
        return f"{location['lat']},{location['lng']}"
    else:
        raise ValueError(f"Location not found: {location_name} (Status: {location_data['status']})")


def get_places(location, radius=5000, types="tourist_attraction"):
    """
    Fetch nearby places of interest using Google Places API.
    """
    url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={location}&radius={radius}&type={types}&key={GOOGLE_API_KEY}"
    response = requests.get(url)
    places_data = response.json()

    print(f"Places API Response: {places_data}")  # Debugging output

    if places_data['status'] != 'OK':
        raise ValueError(f"Error fetching places: {places_data['status']}. Check location and API key.")

    return places_data


def format_itinerary(places, start_date, end_date):
    """
    Organize places into a daily itinerary.
    """
    # Convert date strings to datetime objects
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")
    delta = end_date - start_date

    itinerary = {}
    day_count = 0

    for day in range(delta.days + 1):
        current_date = start_date + timedelta(days=day)
        itinerary[current_date.strftime("%Y-%m-%d")] = places[day_count:day_count + 3]  # 3 places per day
        day_count += 3

    return itinerary


def generate_itinerary(location_name, start_date, end_date):
    """
    Generate the itinerary for the given location and dates.
    """
    try:
        # Ensure dates are in the correct format
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
            datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            print("Please enter dates in YYYY-MM-DD format.")
            return

        # Get location coordinates
        location = get_location_coordinates(location_name)
        print(f"Coordinates for {location_name}: {location}")

        # Fetch places data
        places_data = get_places(location)
        place_names = [place['name'] for place in places_data['results']]

        if not place_names:
            print("No places found. Try increasing the radius or changing the location.")
            return

        # Generate itinerary
        itinerary = format_itinerary(place_names, start_date, end_date)
        return itinerary

    except ValueError as e:
        print(e)
        return None


# Main script
if _name_ == "_main_":
    location_name = input("Enter the location name: ")
    start_date = input("Enter the start date (YYYY-MM-DD): ")
    end_date = input("Enter the end date (YYYY-MM-DD): ")

    itinerary = generate_itinerary(location_name, start_date, end_date)

    if itinerary:
        print("\nOrganized Itinerary:\n")
        for date, activities in itinerary.items():
            print(f"Date: {date}")
            for activity in activities:
                print(f" - {activity}")
            print()