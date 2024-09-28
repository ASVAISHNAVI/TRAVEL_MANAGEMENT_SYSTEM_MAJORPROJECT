from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os
import urllib.parse
import requests
from datetime import datetime, timedelta
import googlemaps
load_dotenv()
app = Flask(__name__)
app.secret_key = 'your_secret_key'
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')
app.config['GOOGLEMAPS_KEY'] =os.getenv('GOOGLE_API_KEY')
gmaps = googlemaps.Client(key=app.config['GOOGLEMAPS_KEY'])

OPENWEATHER_BASE_URL = 'https://api.openweathermap.org/data/2.5/weather'

# Simulated user credentials (replace with secure storage in production)
USER_CREDENTIALS = {
    'admin': generate_password_hash('password')  # Hashed password for 'admin'
}
USER_BUDGETS = {
    'admin': []
}
USER_PACKING_LISTS = {
    'admin': []
}

# Configure file uploads
UPLOAD_FOLDER = 'static/photos'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Helper functions
def get_location_coordinates(location_name):
    encoded_location_name = urllib.parse.quote(location_name)
    geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_location_name}&key={GOOGLE_API_KEY}"
    response = requests.get(geocode_url)
    location_data = response.json()

    if location_data['status'] == 'OK':
        location = location_data['results'][0]['geometry']['location']
        return f"{location['lat']},{location['lng']}"
    else:
        raise ValueError(f"Location not found: {location_name} (Status: {location_data['status']})")


def get_weather_data(latitude, longitude):
    params = {
        'lat': latitude,
        'lon': longitude,
        'appid': OPENWEATHER_API_KEY,
        'units': 'metric'  # Use metric units for Celsius
    }
    response = requests.get(OPENWEATHER_BASE_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        weather = {
            'temperature': data['main']['temp'],
            'humidity': data['main']['humidity'],
            'description': data['weather'][0]['description']
        }
        return weather
    else:
        return None

@app.route('/weather', methods=['GET', 'POST'])
def weather():
    if request.method == 'POST':
        latitude = float(request.form.get('latitude'))
        longitude = float(request.form.get('longitude'))
    else:
        latitude = 37.7749  # Default latitude (San Francisco)
        longitude = -122.4194  # Default longitude (San Francisco)

    weather = get_weather_data(latitude, longitude)
    return render_template('weather.html', weather=weather)
def get_weather_by_location(location_name):
    params = {
        'q': location_name,
        'appid': OPENWEATHER_API_KEY,
        'units': 'metric'  # Use metric units for Celsius
    }
    response = requests.get(OPENWEATHER_BASE_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        weather = {
            'location': location_name,
            'temperature': data['main']['temp'],
            'humidity': data['main']['humidity'],
            'description': data['weather'][0]['description']
        }
        return weather
    else:
        return None

@app.route('/check_weather', methods=['POST'])
def check_weather():
    location = request.form['location']
    weather = get_weather_by_location(location)
    return render_template('weather.html', weather=weather)



@app.route('/directions')
def directions():
    return render_template('directions.html')

def get_places(location, radius=5000, place_type="tourist_attraction"):
    url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={location}&radius={radius}&type={place_type}&key={GOOGLE_API_KEY}"
    response = requests.get(url)
    places_data = response.json()

    if places_data['status'] != 'OK':
        raise ValueError(f"Error fetching places: {places_data['status']}. Check location and API key.")

    return places_data

def get_place_details(place_id):
    url = f'https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&key={GOOGLE_API_KEY}'
    response = requests.get(url)
    place_data = response.json()
    return place_data.get('result', {})

@app.route('/transit')
def transit():
    return render_template('transit.html')

def get_place_photos(photo_reference):
    url = 'https://maps.googleapis.com/maps/api/place/photo'
    params = {
        'maxwidth': 400,
        'photoreference': photo_reference,
        'key': ''  # Replace with your actual API key
    }
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        # Assuming response.json() returns a dictionary
        place_data = response.json()
        
        # Check if 'result' exists in place_data
        if 'result' in place_data:
            return place_data['result']
        else:
            # Handle case where 'result' is missing
            return None
    else:
        # Handle API request failure
        return None

def get_distance_matrix(origins, destinations, api_key):
    base_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        'origins': '|'.join(origins),
        'destinations': '|'.join(destinations),
        'key': api_key
    }

    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        raise ValueError(f"Failed to fetch distance matrix: {response.status_code}")

@app.route('/calculate-distance', methods=['POST'])
def calculate_distance():
    if request.method == 'POST':
        origin = request.form['origin']
        destination = request.form['destination']

        # Call Distance Matrix API
        distance_result = gmaps.distance_matrix(origin, destination)

        if distance_result['status'] == 'OK':
            distance = distance_result['rows'][0]['elements'][0]['distance']['text']
            duration = distance_result['rows'][0]['elements'][0]['duration']['text']
            return f"Distance: {distance}, Duration: {duration}"
        else:
            return "Failed to calculate distance. Please try again."

    return "Invalid request method."

def format_itinerary(places, start_date, end_date):
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")
    delta = end_date - start_date

    itinerary = {}
    day_count = 0

    for day in range(delta.days + 1):
        current_date = start_date + timedelta(days=day)
        itinerary[current_date.strftime("%Y-%m-%d")] = places[day_count:day_count + 3]
        day_count += 3

    return itinerary

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Routes
@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('generate_itinerary'))
    return redirect(url_for('login'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in USER_CREDENTIALS and check_password_hash(USER_CREDENTIALS[username], password):
            session['username'] = username
            flash(f'Logged in as {username}')
            return redirect(url_for('generate_itinerary'))
        else:
            flash('Invalid username or password')

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in USER_CREDENTIALS:
            flash('Username already exists. Please choose another.')
        else:
            hashed_password = generate_password_hash(password)
            USER_CREDENTIALS[username] = hashed_password  # Store new user credentials
            flash('Account created successfully. Please login.')
            return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.')
    return redirect(url_for('login'))

@app.route('/generate-itinerary', methods=['GET', 'POST'])
def generate_itinerary():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        location_name = request.form['location']
        start_date = request.form['start-date']
        end_date = request.form['end-date']

        try:
            location = get_location_coordinates(location_name)
            places_data = get_places(location)
            places = places_data['results']
            latitude = request.form.get('latitude')
            longitude = request.form.get('longitude')

            if not places:
                flash("No places found. Try increasing the radius or changing the location.")
                return redirect(url_for('generate_itinerary'))

            # Extract relevant details for each place
            place_details = []
            for place in places:
                place_id = place['place_id']
                details = get_place_details(place_id)
                place['photo_url'] = get_place_photos(place_id)
                place_details.append({
                    'name': place['name'],
                    'place_id': place_id,
                    'address': details.get('formatted_address', ''),
                    'phone_number': details.get('formatted_phone_number', ''),
                    'rating': details.get('rating', ''),
                    'reviews_count': details.get('user_ratings_total', ''),
                    'photo_url': details['photos'][0]['html_attributions'][0] if 'photos' in details and details['photos'] else None
                })
            weather = get_weather_data(latitude, longitude)
            itinerary = format_itinerary(place_details, start_date, end_date)
            return render_template('itinerary.html', itinerary=itinerary, weather=weather)
        except ValueError as e:
            flash(str(e))
            return redirect(url_for('generate_itinerary'))

    return render_template('index.html')

@app.route('/washroom-finder', methods=['GET', 'POST'])
def washroom_finder():
    if 'username' not in session:
        return redirect(url_for('login'))

    washrooms = []
    if request.method == 'POST':
        location_name = request.form['location']
        try:
            location = get_location_coordinates(location_name)
            washrooms_data = get_places(location, place_type="restroom")
            washrooms = washrooms_data['results']

            if not washrooms:
                flash("No washrooms found. Try increasing the radius or changing the location.")
                return redirect(url_for('washroom_finder'))

            # Extract relevant details for each washroom
            for washroom in washrooms:
                place_id = washroom['place_id']
                details = get_place_details(place_id)
                washroom['photo_url'] = get_place_photos(place_id)
        except ValueError as e:
            flash(str(e))
            return redirect(url_for('washroom_finder'))

    return render_template('washroom_finder.html', washrooms=washrooms)

@app.route('/budget', methods=['GET', 'POST'])
def budget():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']

    if request.method == 'POST':
        date = request.form['date']
        description = request.form['description']
        amount = float(request.form['amount'])

        if username not in USER_BUDGETS:
            USER_BUDGETS[username] = []

        USER_BUDGETS[username].append({
            'date': date,
            'description': description,
            'amount': amount
        })

        flash('Expense added successfully.')

    budget_data = USER_BUDGETS.get(username, [])
    return render_template('budget.html', budget=budget_data)

@app.route('/packing-list', methods=['GET', 'POST'])
def packing_list():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']

    if request.method == 'POST':
        item = request.form['item']
        if username not in USER_PACKING_LISTS:
            USER_PACKING_LISTS[username] = []

        USER_PACKING_LISTS[username].append({
            'item': item,
            'checked': False
        })

        flash('Item added successfully.')

    packing_list_data = USER_PACKING_LISTS.get(username, [])
    return render_template('packing_list.html', packing_list=packing_list_data)

@app.route('/packing-list/check/<int:item_id>', methods=['POST'])
def check_item(item_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    if username in USER_PACKING_LISTS and 0 <= item_id < len(USER_PACKING_LISTS[username]):
        USER_PACKING_LISTS[username][item_id]['checked'] = not USER_PACKING_LISTS[username][item_id]['checked']
        flash('Item updated successfully.')
    
    return redirect(url_for('packing_list'))

@app.route('/photo-gallery')
def photo_gallery():
    if 'username' not in session:
        return redirect(url_for('login'))

    photo_folder = os.path.join(app.root_path, 'static/photos')
    photos = os.listdir(photo_folder)
    return render_template('photo_gallery.html', photos=photos)

@app.route('/upload-photo', methods=['GET', 'POST'])
def upload_photo():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        if 'photo' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['photo']

        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash('Photo uploaded successfully.')
            return redirect(url_for('photo_gallery'))

        flash('Allowed file types are txt, pdf, png, jpg, jpeg, gif')
        return redirect(request.url)

    # Render the upload_photo.html template for GET requests
    return render_template('upload_photo.html')

@app.route('/recommend-attractions', methods=['GET', 'POST'])
def recommend_attractions():
    if 'username' not in session:
        return redirect(url_for('login'))

    attractions = []
    if request.method == 'POST':
        location_name = request.form['location']
        try:
            location = get_location_coordinates(location_name)
            places_data = get_places(location)
            places = places_data['results']

            if not places:
                flash("No attractions found. Try increasing the radius or changing the location.")
                return redirect(url_for('recommend_attractions'))

            # Extract relevant details for each place
            for place in places:
                place_id = place['place_id']
                details = get_place_details(place_id)
                photo_url = None
                if 'photos' in details and details['photos']:
                    photo_reference = details['photos'][0]['photo_reference']
                    photo_url = get_place_photos(photo_reference)
                attractions.append({
                    'name': place['name'],
                    'place_id': place_id,
                    'address': details.get('formatted_address', ''),
                    'phone_number': details.get('formatted_phone_number', ''),
                    'rating': details.get('rating', ''),
                    'reviews_count': details.get('user_ratings_total', ''),
                    'photo_url': photo_url
                })
        except ValueError as e:
            flash(str(e))
            return redirect(url_for('recommend_attractions'))

    return render_template('recommend_attractions.html', attractions=attractions)

def get_attractions(location):
    # Use Google Places API to fetch attractions based on location
    endpoint = 'https://maps.googleapis.com/maps/api/place/textsearch/json'
    params = {
        'query': f'tourist attractions in {location}',
        'key': google_api_key
    }

    try:
        response = requests.get(endpoint, params=params)
        data = response.json()
        attractions = []
        
        for place in data['results']:
            attraction = {
                'name': place.get('name', 'N/A'),
                'address': place.get('formatted_address', 'N/A'),
                'phone_number': place.get('formatted_phone_number', 'N/A'),
                'rating': place.get('rating', 'N/A'),
                'reviews_count': place.get('user_ratings_total', 'N/A')
            }

            # Get photo URL if available
            if 'photos' in place:
                photo_ref = place['photos'][0]['photo_reference']
                attraction['photo_url'] = f'https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_ref}&key={google_api_key}'
            else:
                attraction['photo_url'] = None

            attractions.append(attraction)
        
        return attractions

    except Exception as e:
        print(f"Error fetching attractions: {e}")
        return []


@app.route('/recommend-hotels', methods=['GET', 'POST'])
def recommend_hotels():
    if 'username' not in session:
        return redirect(url_for('login'))

    hotels = []
    if request.method == 'POST':
        location_name = request.form['location']
        try:
            location = get_location_coordinates(location_name)
            places_data = get_places(location, place_type="lodging")
            places = places_data['results']

            if not places:
                flash("No hotels found. Try increasing the radius or changing the location.")
                return redirect(url_for('recommend_hotels'))

            # Extract relevant details for each place
            for place in places:
                place_id = place['place_id']
                details = get_place_details(place_id)
                photo_url = None
                if 'photos' in details and details['photos']:
                    photo_reference = details['photos'][0]['photo_reference']
                    photo_url = get_place_photos(photo_reference)
                hotels.append({
                    'name': place['name'],
                    'place_id': place_id,
                    'address': details.get('formatted_address', ''),
                    'phone_number': details.get('formatted_phone_number', ''),
                    'rating': details.get('rating', ''),
                    'reviews_count': details.get('user_ratings_total', ''),
                    'photo_url': photo_url
                })
        except ValueError as e:
            flash(str(e))
            return redirect(url_for('recommend_hotels'))

    return render_template('recommend_hotels.html', hotels=hotels)

@app.route('/recommend-restaurants', methods=['GET', 'POST'])
def recommend_restaurants():
    if 'username' not in session:
        return redirect(url_for('login'))

    restaurants = []
    if request.method == 'POST':
        location_name = request.form['location']
        try:
            location = get_location_coordinates(location_name)
            places_data = get_places(location, place_type="restaurant")
            places = places_data['results']

            if not places:
                flash("No restaurants found. Try increasing the radius or changing the location.")
                return redirect(url_for('recommend_restaurants'))

            # Extract relevant details for each place
            for place in places:
                place_id = place['place_id']
                details = get_place_details(place_id)
                photo_url = None
                if 'photos' in details and details['photos']:
                    photo_reference = details['photos'][0]['photo_reference']
                    photo_url = get_place_photos(photo_reference)
                restaurants.append({
                    'name': place['name'],
                    'place_id': place_id,
                    'address': details.get('formatted_address', ''),
                    'phone_number': details.get('formatted_phone_number', ''),
                    'rating': details.get('rating', ''),
                    'reviews_count': details.get('user_ratings_total', ''),
                    'photo_url': photo_url
                })
        except ValueError as e:
            flash(str(e))
            return redirect(url_for('recommend_restaurants'))

    return render_template('recommend_restaurants.html', restaurants=restaurants)

@app.route('/place-details/<place_id>')
def place_details(place_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    place_details = get_place_details(place_id)
    return render_template('place_details.html', place_details=place_details)

if __name__ == '__main__':
    app.run(debug=True)
