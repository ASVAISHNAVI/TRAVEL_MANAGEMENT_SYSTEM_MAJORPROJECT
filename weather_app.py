# File: weather_app.py

import requests
from flask import Flask, render_template, flash, redirect, url_for
from dotenv import load_dotenv
import os
load_dotenv()
app = Flask(__name__)
app.secret_key = 'your_secret_key'

OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')

def get_weather_forecast(latitude, longitude):
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={OPENWEATHER_API_KEY}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        weather = {
            'temperature': data['main']['temp'],
            'humidity': data['main']['humidity'],
            'description': data['weather'][0]['description']
            # Add more fields as needed (e.g., wind speed, sunrise, sunset, etc.)
        }
        return weather
    else:
        return None

# Sample route for generating the itinerary page
@app.route('/')
def home():
    # Example coordinates (replace with actual coordinates or fetch dynamically)
    latitude = 'latitude_value'
    longitude = 'longitude_value'
    
    weather_data = get_weather_forecast(latitude, longitude)
    
    return render_template('itinerary.html', weather=weather_data)

@app.route('/weather-forecast/<location>')
def weather_forecast(location):
    # Placeholder for fetching weather by location if needed
    flash('Fetching weather by location is not implemented.')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
