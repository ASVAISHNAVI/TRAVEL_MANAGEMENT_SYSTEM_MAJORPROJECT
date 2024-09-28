import requests
from dotenv import load_dotenv
import os
load_dotenv()
# Your Places API key
api_key =  os.getenv('api_key')

# Example place (e.g., "New York")
place = 'New York'

# Make a request to the Places API
url = f'https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={place}&inputtype=textquery&fields=formatted_address,name,geometry&key={api_key}'

response = requests.get(url)
data = response.json()

if response.status_code == 200:
    print("API Key is working.")
    print("Response data:")
    print(data)
else:
    print("Failed to connect to the API.")
    print(f"Status code: {response.status_code}")
    print("Error message:")
    print(data)

