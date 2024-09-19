from geopy.geocoders import Nominatim
from shapely.geometry import Point
import geopy.distance
import streamlit as st
import joblib
import pandas as pd
import datetime
import numpy as np
from PIL import Image
from PIL import Image, ImageDraw, ImageOps
import pydeck as pdk
import requests
import polyline
import geopandas as gpd
import openrouteservice


API_KEY = 'Your API'

locations = {
    "Express Avenue Mall": (13.058821, 80.264103),
    "Chennai Citi Centre": (13.043025, 80.273870),
    "Chennai Lighthouse": (13.039716, 80.279442),
    "Marina Beach": (13.053275, 80.283289),
    "Semmozhi Poonga": (13.050626, 80.251510),
    "Sai Baba Temple Mylapore": (13.032698,80.264734),
    "PVR Ampa SkyOne":(13.073553, 80.221499)
}

# Load the pipelines
price_pipeline = joblib.load('distModels/price_pipeline.pkl')
waiting_pipeline = joblib.load('distModels/time_pipeline.pkl')
time_pipeline = joblib.load('distModels/waiting_pipeline.pkl')

def add_rounded_corners(image, radius):
    # Create a mask for the rounded corners
    mask = Image.new('L', image.size, 0)
    draw = ImageDraw.Draw(mask)
    width, height = image.size
    draw.rounded_rectangle([(0, 0), (width, height)], radius, fill=255)

    # Apply the mask to the image
    rounded_image = ImageOps.fit(image, mask.size, centering=(0.5, 0.5))
    rounded_image.putalpha(mask)
    return rounded_image


# Path to the single landscape-oriented image
image_path = "imagesplaces/chennai.png"  # Replace with your actual image path

# Load and display the image
image = Image.open(image_path)

# Add rounded corners
radius = 40  # Adjust the radius as needed
rounded_image = add_rounded_corners(image, radius)

# Display the image
st.image(rounded_image, use_column_width=True)

def get_lat_long(location_name):
    geolocator = Nominatim(user_agent="geoapiExercise")
    location = geolocator.geocode(location_name)
    if location:
        return location.latitude, location.longitude
    else:
        return None, None

def is_within_radius(lat_center, lon_center, lat_point, lon_point, radius_km=20):
    distance = geopy.distance.distance((lat_center, lon_center), (lat_point, lon_point)).km
    return distance <= radius_km


# Load unique values from file
df = pd.read_csv('data/justadf.csv')  # Replace with your actual file path


# Fetch unique routes and ride types
routes_from = df['route_from'].unique()
routes_to = df['route_to'].unique()
ride_types = df['ride_type'].unique()

# Streamlit input fields
st.title('Uber X Chennai Ride Fare Predictor')


# Create two columns
col1, col2 = st.columns(2)

with col1:
    date_input = st.date_input('Select date', value=datetime.date.today())
    # Hourly time selection using selectbox
    hour_options = [f"{i}:00" for i in range(7,23)]
    hour_selected = st.selectbox('Select hour', options=hour_options)
    hour_int = int(str(hour_selected).split(':')[0])  # Extract hour from selected option

    hour = np.int32(hour_int)

    day_of_week_int = date_input.weekday()

    day_of_week = np.int32(day_of_week_int)

    ride_type = st.selectbox('Ride Type', options=ride_types)

    # Set ride_max_persons based on ride_type
    ride_max_persons_dict = {
        'Uber Go': 4,
        'Go Sedan': 4,
        'UberXL': 6,
        'Premier': 4,
        'Uber Auto': 3,
        'Moto': 1
    }
    ride_max_persons_str = ride_max_persons_dict.get(ride_type, 1)

    # Display ride_max_persons as read-only
    # st.write(f'**Max Persons: {ride_max_persons_str}**')
    st.text_input("Max Persons", value=ride_max_persons_str, disabled=True)

    ride_max_persons = float(ride_max_persons_str)

with col2:
    # Dropdowns for routes and ride types
    route_from = st.text_input("Route from",value="Marina Beach")
    route_to = st.text_input("Route to",value="Express Avenue Mall")

    lat_from, lon_from = get_lat_long(route_from)
    lat_to, lon_to = get_lat_long(route_to)
    st.write(lat_from, lon_from)
    st.write(lat_to, lon_to)

    # Check if the entered locations are within 20km of the midpoint
    midpoint_lat = 13.05024543591047
    midpoint_lon = 80.26263587238336
    radius_km = 20

    client = openrouteservice.Client(key=API_KEY)

    coords = ((lon_from, lat_from), (lon_to, lat_to))
    route = client.directions(coords)
    # Extract distance from the route (in meters)
    distance = route['routes'][0]['summary']['distance']
    st.write("Distance:",distance)

# Initialize flags for start and end location
is_start_within_radius = is_within_radius(midpoint_lat, midpoint_lon, lat_from, lon_from)
is_end_within_radius = is_within_radius(midpoint_lat, midpoint_lon, lat_to, lon_to)

# Check if both locations are within the radius and give individual feedback
if lat_from and lon_from and lat_to and lon_to:
    # Check for the start location
    if is_start_within_radius:
        st.write("Start location is within 20km radius.")
    else:
        st.write("Start location is outside the 20km radius. Try Again")

    # Check for the end location
    if is_end_within_radius:
        st.write("End location is within 20km radius.")
    else:
        st.write("End location is outside the 20km radius. Try Again")

    # Show the Predict button only if both locations are valid
    if is_start_within_radius and is_end_within_radius:
        if st.button("Predict"):

            from_coords = (lat_from, lon_from)
            to_coords = (lat_to, lon_to)

            def calculate_midpoint(coord1, coord2):
                mid_lat = (coord1[0] + coord2[0]) / 2
                mid_lon = (coord1[1] + coord2[1]) / 2
                return mid_lat, mid_lon


            # Create predictions for the current hour
            features = {
                'ride_max_persons': [ride_max_persons],
                'hour': [hour],
                'day_of_week': [day_of_week],
                'distance_meters': [distance],
                'lat_route_from': [lat_from],
                'lon_route_from': [lon_from],
                'lat_route_to': [lat_to],
                'lon_route_to': [lon_to],
                'ride_type': [ride_type]
            }

            # Convert the dictionary to a DataFrame
            input_df = pd.DataFrame(features)

            # Perform predictions for the current time
            price_current = price_pipeline.predict(input_df)[0]
            waiting_current = waiting_pipeline.predict(input_df)[0]
            time_current = time_pipeline.predict(input_df)[0]

            st.write('**Predictions for the Selected Time:**')

            # Display current predictions in a centered box
            st.markdown(f"""
                        <style>
                            .current-box {{
                                padding: 10px;
                                border: 2px solid #ddd;
                                border-radius: 10px;
                                background-color: #1e2226;
                                margin-bottom: 10px;
                                text-align: center;
                            }}
                            .current-box h6 {{
                                margin: 0;
                                color: #d2d4d6;
                            }}
                            .current-box span {{
                                color: #007bff;
                            }}
                        </style>
                        <div class="current-box">
                            <h6>Price: <span>Rs. {price_current:.2f}</span></h6>
                            <h6>Waiting Time: <span>{waiting_current:.2f} minutes</span></h6>
                            <h6>Ride Time: <span>{time_current:.2f} minutes</span></h6>
                        </div>
                        """, unsafe_allow_html=True)

            # Predictions for the next three hours
            future_hours = [hour + i for i in range(1, 4)]  # Next 3 hours
            future_predictions = []

            for future_hour in future_hours:
                features = {
                    'ride_max_persons': [ride_max_persons],
                    'hour': [np.int32(future_hour)],
                    'day_of_week': [day_of_week],
                    'distance_meters': [distance],
                    'lat_route_from': [lat_from],
                    'lon_route_from': [lon_from],
                    'lat_route_to': [lat_to],
                    'lon_route_to': [lon_to],
                    'ride_type': [ride_type]
                }

                # Convert to DataFrame
                future_df = pd.DataFrame(features)

                # Predict for future hours
                future_price = price_pipeline.predict(future_df)[0]
                future_waiting = waiting_pipeline.predict(future_df)[0]
                future_time = time_pipeline.predict(future_df)[0]

                future_predictions.append({
                    'hour': future_hour,
                    'price': future_price,
                    'waiting_time': future_waiting,
                    'ride_time': future_time
                })

                # Calculate percentage changes


            def percentage_change(current, future):
                return ((future - current) / current) * 100 if current != 0 else 0


            # Display predictions for the next three hours with styled boxes and arrows
            st.write('**Predictions for the Next 3 Hours:**')
            for prediction in future_predictions:
                # Calculate percentage changes
                price_change = percentage_change(price_current, prediction['price'])
                waiting_change = percentage_change(waiting_current, prediction['waiting_time'])
                time_change = percentage_change(time_current, prediction['ride_time'])

                # Determine color

                price_color = 'red' if price_change > 0 else 'green'
                waiting_color = 'red' if waiting_change > 0 else 'green'
                time_color = 'red' if time_change > 0 else 'green'

                # Display prediction with percentage change
                st.markdown(f"""
                    <style>
                        .future-box {{
                            padding: 10px;
                            border: 2px solid #ddd;
                            border-radius: 10px;
                            background-color: #1e2226;
                            margin-bottom: 10px;
                            text-align: center;
                        }}
                        .future-box h4 {{
                            margin: 0;
                            color: #333;
                        }}
                        .future-box p {{
                            margin: 0;
                            color: {price_color};
                        }}
                    </style>
                    <div class="future-box">
                        <h6>Hour: {prediction['hour']}:00</h6>
                        <h6 style="margin: 0; color: #d2d4d6;">Price: <span style="color: {price_color};"> Rs. {prediction['price']:.2f} ({price_change:.2f}%)</span></h6>
                        <h6 style="margin: 0; color: #d2d4d6;">Waiting Time: <span style="color: {waiting_color};"> {prediction['waiting_time']:.2f} minutes ({waiting_change:.2f}%)</span></h6>
                        <h6 style="margin: 0; color: #d2d4d6;">Ride Time: <span style="color: {time_color};"> {prediction['ride_time']:.2f} minutes ({time_change:.2f}%)</span></p>
                    </div>
                    """, unsafe_allow_html=True)


            # Function to get driving route from OpenRouteService
            def get_driving_route(from_coords, to_coords, api_key):
                headers = {
                    'Authorization': api_key,
                    'Content-Type': 'application/json'
                }
                payload = {
                    "coordinates": [
                        [from_coords[1], from_coords[0]],  # [lon, lat]
                        [to_coords[1], to_coords[0]]
                    ]
                }
                response = requests.post('https://api.openrouteservice.org/v2/directions/driving-car', json=payload,
                                         headers=headers)
                response.raise_for_status()  # Raise an error for bad responses
                data = response.json()
                return data


            # Get route data
            try:
                route_data = get_driving_route(from_coords, to_coords, API_KEY)
                # st.write(route_data)

                # Extract polyline from the route data
                encoded_polyline = route_data['routes'][0]['geometry']

                # Decode the polyline into a list of coordinates
                coordinates = polyline.decode(encoded_polyline)

                # st.write("Decoded coordinates:", coordinates)

                # Convert the coordinates into the format required by Pydeck
                path_coordinates = [[lat, lon] for lon, lat in coordinates]  # Convert (lat, lon) to (lon, lat)

                # Debugging: Print path coordinates to ensure correct format
                # st.write("Path coordinates:", path_coordinates)

                lines = [{"start": path_coordinates[i], "end": path_coordinates[i + 1]} for i in
                         range(len(path_coordinates) - 1)]

                mid_latitude, mid_longitude = calculate_midpoint(from_coords, to_coords)

                INITIAL_VIEW_STATE = pdk.ViewState(
                    latitude=mid_latitude,  # Approximate center latitude
                    longitude=mid_longitude,  # Approximate center longitude
                    zoom=14,
                    pitch=50,
                    bearing=0
                )

                line_layer = pdk.Layer(
                    "LineLayer",
                    lines,
                    get_source_position="start",
                    get_target_position="end",
                    get_color=[255, 0, 0, 200],  # Red color with 200 alpha
                    get_width=5,
                    pickable=True,
                )

                r = pdk.Deck(
                    layers=[line_layer],
                    initial_view_state=INITIAL_VIEW_STATE,
                    tooltip={"text": "{start} -> {end}"}
                )

                # r.to_html("path_coordinates.html")

                st.pydeck_chart(r)

            except requests.HTTPError as e:

                st.error(f"Error fetching route data: {e}")

            except KeyError as e:

                st.error(f"Error processing route data: Missing key {e}")

            except Exception as e:

                st.error(f"An error occurred: {e}")

        df_loc = pd.read_csv('locations_with_lat_lon.csv')

        df_loc.columns = ['name', 'Latitudes', 'Longitudes']

        with st.expander("Click to view 7 locations used for modelling this App"):
            # Create a pydeck map
            deck = pdk.Deck(
                initial_view_state=pdk.ViewState(
                    latitude=df_loc['Latitudes'].mean(),
                    longitude=df_loc['Longitudes'].mean(),
                    zoom=12
                ),
                layers=[
                    pdk.Layer(
                        "ScatterplotLayer",
                        data=df_loc,
                        get_position=["Longitudes", "Latitudes"],  # Longitude first
                        get_color=[255, 0, 0],
                        get_radius=200,
                        pickable=True,  # Enable interaction
                        auto_highlight=True  # Highlight the point on hover
                    )
                ],
                tooltip={
                    "text": "{name}"  # Display the name of the location
                }
            )
            # Display the map
            st.pydeck_chart(deck)


else:
    st.write("Please select valid start and end locations.")

