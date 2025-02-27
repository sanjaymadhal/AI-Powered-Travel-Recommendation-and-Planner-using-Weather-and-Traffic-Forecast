import streamlit as st
import pandas as pd
import numpy as np
import joblib
import os
import requests
import logging
from datetime import datetime
import folium
from streamlit_folium import st_folium
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

if not OPENWEATHER_API_KEY or not GOOGLE_MAPS_API_KEY:
    st.error("API keys not found. Please set up a .env file with OPENWEATHER_API_KEY and GOOGLE_MAPS_API_KEY.")
    st.stop()

# Load dataset
@st.cache_data
def load_data(file_path="holidify.csv"):
    try:
        df = pd.read_csv(file_path)
        df = df.drop_duplicates(subset=['City'])
        df['City'] = df['City'].str.strip()
        df['Best Time to visit'] = df['Best Time to visit'].fillna('Throughout the year')
        df['Year_round'] = df['Best Time to visit'].str.contains('Throughout the year').astype(int)
        logger.info(f"Loaded dataset with {len(df)} records")
        return df
    except Exception as e:
        logger.error(f"Error loading data: {str(e)}")
        return None

# Load trained model
@st.cache_data
def load_model(filename="travel_recommendation_enhanced.joblib"):
    try:
        model_data = joblib.load(filename)
        logger.info("Model loaded successfully")
        return model_data
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        return None

# Fetch coordinates using Google Maps Geocoding API
def get_coordinates(city, api_key=GOOGLE_MAPS_API_KEY):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={city},India&key={api_key}"
    try:
        response = requests.get(url)
        data = response.json()
        if data["status"] == "OK" and data["results"]:
            location = data["results"][0]["geometry"]["location"]
            return location["lat"], location["lng"]
        else:
            logger.warning(f"Geocoding failed for {city}: {data.get('error_message', 'Unknown error')}")
            return None, None
    except Exception as e:
        logger.error(f"Error fetching coordinates for {city}: {str(e)}")
        return None, None

# Fetch nearby places using Google Places API
def get_nearby_places(lat, lng, radius=5000, api_key=GOOGLE_MAPS_API_KEY):
    url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius={radius}&type=tourist_attraction&key={api_key}"
    try:
        response = requests.get(url)
        data = response.json()
        if data["status"] == "OK":
            places = data["results"]
            return [{"name": place["name"], "lat": place["geometry"]["location"]["lat"], "lng": place["geometry"]["location"]["lng"]} for place in places]
        else:
            logger.warning(f"Places API failed: {data.get('error_message', 'Unknown error')}")
            return []
    except Exception as e:
        logger.error(f"Error fetching nearby places: {str(e)}")
        return []

# Real-time weather data
def get_weather_data(cities, api_key=OPENWEATHER_API_KEY):
    weather_data = {}
    for city in cities:
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city},IN&appid={api_key}&units=metric"
            response = requests.get(url)
            data = response.json()
            if response.status_code == 200 and "main" in data and "weather" in data:
                temp = data["main"]["temp"]
                condition = data["weather"][0]["description"]
                quality = 9 if "clear" in condition or "sunny" in condition else (
                    7 if "cloud" in condition else 4 if "rain" in condition else 6
                )
                quality += 1 if 20 <= temp <= 30 else -2 if temp < 5 or temp > 40 else 0
                quality = max(1, min(10, quality))
                weather_data[city] = {"condition": condition, "temp": temp, "quality": quality}
            else:
                weather_data[city] = {"condition": "unknown", "temp": 25, "quality": 5}
        except Exception as e:
            logger.error(f"Error fetching weather for {city}: {str(e)}")
            weather_data[city] = {"condition": "error", "temp": 25, "quality": 5}
    return weather_data

# Real-time traffic data for places
def get_traffic_data_for_places(origin_lat, origin_lng, places, api_key=GOOGLE_MAPS_API_KEY):
    traffic_data = {}
    for place in places:
        try:
            dest_lat, dest_lng = place["lat"], place["lng"]
            url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={origin_lat},{origin_lng}&destinations={dest_lat},{dest_lng}&key={api_key}&departure_time=now&traffic_model=best_guess"
            response = requests.get(url)
            data = response.json()
            if data["status"] == "OK" and data["rows"]:
                element = data["rows"][0]["elements"][0]
                if element["status"] == "OK":
                    travel_time = element["duration_in_traffic"]["value"] // 60  # minutes
                    traffic_level = min(max(travel_time // 5, 1), 10)  # Scale traffic level
                else:
                    travel_time = 15
                    traffic_level = 5
                traffic_data[place["name"]] = {"travel_time": travel_time, "traffic_level": traffic_level}
            else:
                traffic_data[place["name"]] = {"travel_time": 15, "traffic_level": 5}
        except Exception as e:
            logger.error(f"Error fetching traffic for {place['name']}: {str(e)}")
            traffic_data[place["name"]] = {"travel_time": 15, "traffic_level": 5}
    return traffic_data

# Real-time traffic data for cities
def get_traffic_data(cities, current_location, api_key=GOOGLE_MAPS_API_KEY):
    traffic_data = {}
    origin_lat, origin_lng = get_coordinates(current_location)
    if origin_lat is None:
        logger.error(f"Could not get coordinates for {current_location}")
        return {city: {"traffic_level": 5, "places": {}} for city in cities}

    for city in cities:
        try:
            dest_lat, dest_lng = get_coordinates(city)
            if dest_lat is None:
                traffic_data[city] = {"traffic_level": 5, "places": {}}
                continue
            url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={origin_lat},{origin_lng}&destinations={dest_lat},{dest_lng}&key={api_key}&departure_time=now&traffic_model=best_guess"
            response = requests.get(url)
            data = response.json()
            if data["status"] == "OK" and data["rows"]:
                element = data["rows"][0]["elements"][0]
                if element["status"] == "OK":
                    travel_time = element["duration_in_traffic"]["value"] // 60
                    traffic_level = min(max(travel_time // 10, 1), 10)
                else:
                    travel_time = 30
                    traffic_level = 5
                traffic_data[city] = {"traffic_level": traffic_level, "places": {}}
            else:
                traffic_data[city] = {"traffic_level": 5, "places": {}}
        except Exception as e:
            logger.error(f"Error fetching traffic for {city}: {str(e)}")
            traffic_data[city] = {"traffic_level": 5, "places": {}}
    return traffic_data

# Feature engineering
def engineer_features(df, weather_data, traffic_data):
    df_processed = df.copy()
    for city in df_processed["City"]:
        if city in weather_data:
            df_processed.loc[df_processed["City"] == city, "Weather Quality"] = weather_data[city]["quality"]
            df_processed.loc[df_processed["City"] == city, "Temperature"] = weather_data[city]["temp"]
        if city in traffic_data:
            df_processed.loc[df_processed["City"] == city, "Traffic Level"] = traffic_data[city]["traffic_level"]
    df_processed["Temp_Comfort"] = 10 - abs(df_processed["Temperature"] - 24) / 2
    df_processed["Temp_Comfort"] = df_processed["Temp_Comfort"].clip(0, 10)
    return df_processed

# Generate itinerary with real places
def generate_itinerary(destination, places_data, travel_date, weather_data):
    itinerary = []
    sorted_places = sorted(places_data.items(), key=lambda x: x[1]["travel_time"] if isinstance(x[1], dict) else 15)
    weather_condition = weather_data.get("condition", "unknown")
    outdoor_friendly = "clear" in weather_condition or "sunny" in weather_condition or "few clouds" in weather_condition
    
    morning_places, afternoon_places, evening_places = [], [], []
    for place, data in sorted_places:
        travel_time = data["travel_time"] if isinstance(data, dict) else 15
        if travel_time < 25:
            if outdoor_friendly:
                morning_places.append((place, travel_time))
            else:
                afternoon_places.append((place, travel_time))
        elif travel_time < 40:
            afternoon_places.append((place, travel_time))
        else:
            evening_places.append((place, travel_time))
    
    for place_type, places, time_of_day in [
        ("outdoor" if outdoor_friendly else "indoor", morning_places, "Morning"),
        ("mixed", afternoon_places, "Afternoon"),
        ("indoor or dining", evening_places, "Evening")
    ]:
        for place, travel_time in places:
            itinerary.append({
                "Place": place, "Travel Time": f"{travel_time} mins",
                "Best Time to Visit": time_of_day, "Type": place_type
            })
    return itinerary

# Recommendations with user preferences
def recommend_based_on_preferences(df, model_data, user_preferences, destination, num_recommendations=5):
    model, features, scaler = model_data["model"], model_data["features"], model_data["scaler"]
    cities = df["City"].tolist()
    weather_data = get_weather_data(cities)
    traffic_data = get_traffic_data(cities, destination)
    
    df_processed = engineer_features(df, weather_data, traffic_data)
    for feature in features:
        if feature not in df_processed.columns:
            df_processed[feature] = 0
    
    X = df_processed[features].values
    X_scaled = scaler.transform(X)
    proba = model.predict_proba(X_scaled)
    df_processed["Recommendation Score"] = proba[:, 1]
    
    weather_importance = user_preferences.get("weather_importance", 0.3)
    crowd_importance = user_preferences.get("crowd_importance", 0.3)
    attractions_importance = user_preferences.get("attractions_importance", 0.2)
    season = user_preferences.get("season", None)
    
    if season:
        df_processed["Season Match"] = df["Best Time to visit"].str.contains(season, case=False).astype(float)
        season_importance = 0.2
        total = weather_importance + crowd_importance + attractions_importance
        factor = (1 - season_importance) / total
        weather_importance *= factor
        crowd_importance *= factor
        attractions_importance *= factor
        df_processed["Final Score"] = (
            (weather_importance * df_processed["Weather Quality"] / 10) +
            (crowd_importance * (10 - df_processed["Traffic Level"]) / 10) +
            (attractions_importance * df_processed.get("Attractions_Score", 5) / 10) +
            (season_importance * df_processed["Season Match"])
        ) * 10
    else:
        df_processed["Final Score"] = (
            (weather_importance * df_processed["Weather Quality"] / 10) +
            (crowd_importance * (10 - df_processed["Traffic Level"]) / 10) +
            (attractions_importance * df_processed.get("Attractions_Score", 5) / 10)
        ) * 10
    
    sorted_df = df_processed.sort_values(by="Final Score", ascending=False)
    return sorted_df.head(num_recommendations), weather_data, traffic_data

# Sort places based on traffic
def sort_places_by_traffic(places, traffic_data):
    sorted_places = sorted(places, key=lambda x: traffic_data.get(x["name"], {}).get("travel_time", 15))
    return sorted_places

# Streamlit App
def main():
    st.set_page_config(page_title="Travel Recommender", layout="wide")
    st.title("🌍 Advanced Travel Planner & Recommender")
    st.write("Plan your trip with real-time data, maps, and personalized recommendations!")

    # Load data and model
    df = load_data()
    model_data = load_model()
    if df is None or model_data is None:
        st.error("Failed to load data or model. Please check the files and try again.")
        return

    # Sidebar for preferences
    st.sidebar.header("Preferences")
    weather_importance = st.sidebar.slider("Weather Importance", 0.0, 1.0, 0.3, help="Higher values prioritize better weather conditions.")
    crowd_importance = st.sidebar.slider("Avoid Crowds Importance", 0.0, 1.0, 0.3, help="Higher values prioritize less crowded destinations.")
    attractions_importance = st.sidebar.slider("Attractions Importance", 0.0, 1.0, 0.2, help="Higher values prioritize destinations with more attractions.")
    season = st.sidebar.selectbox("Preferred Season", [None, "Summer", "Winter", "Spring", "Fall"], help="Select a season for seasonal recommendations.")
    user_preferences = {
        "weather_importance": weather_importance,
        "crowd_importance": crowd_importance,
        "attractions_importance": attractions_importance,
        "season": season
    }

    # Initialize session state
    if "recommendations" not in st.session_state:
        st.session_state.recommendations = None
        st.session_state.weather_data = None
        st.session_state.traffic_data = None
        st.session_state.destination = "Bangalore"
        st.session_state.nearby_places = None

    # Destination input
    destination = st.text_input("Enter Destination City", st.session_state.destination)
    if st.button("Get Recommendations"):
        with st.spinner("Fetching recommendations..."):
            st.session_state.destination = destination
            recommendations, weather_data, traffic_data = recommend_based_on_preferences(df, model_data, user_preferences, destination)
            st.session_state.recommendations = recommendations
            st.session_state.weather_data = weather_data
            st.session_state.traffic_data = traffic_data

            # Fetch nearby places
            lat, lng = get_coordinates(destination)
            if lat and lng:
                nearby_places = get_nearby_places(lat, lng)
                st.session_state.nearby_places = nearby_places
            else:
                st.session_state.nearby_places = []
    
    # Tabs for Recommendations, Itinerary, Nearby Places
    tab1, tab2, tab3 = st.tabs(["🏙️ Recommendations", "🗓️ Itinerary", "🏞️ Nearby Places"])

    with tab1:
        st.subheader("Top Recommendations")
        if st.session_state.recommendations is not None:
            st.dataframe(st.session_state.recommendations[["City", "Weather Quality", "Traffic Level", "Final Score"]])
            # Map integration with real coordinates
            m = folium.Map(location=[20.5937, 78.9629], zoom_start=5)  # Center on India
            for _, row in st.session_state.recommendations.iterrows():
                lat, lng = get_coordinates(row["City"])
                if lat and lng:
                    folium.Marker(
                        [lat, lng],
                        popup=f"{row['City']}: Score {row['Final Score']:.2f}",
                        tooltip=row["City"]
                    ).add_to(m)
            st_folium(m, width=700, height=500)
        else:
            st.write("Please enter a destination and click 'Get Recommendations'.")

    with tab2:
        st.subheader("Travel Itinerary")
        if st.session_state.weather_data and st.session_state.nearby_places:
            lat, lng = get_coordinates(st.session_state.destination)
            if lat and lng:
                traffic_data_places = get_traffic_data_for_places(lat, lng, st.session_state.nearby_places)
                itinerary = generate_itinerary(
                    st.session_state.destination,
                    traffic_data_places,
                    datetime.now(),
                    st.session_state.weather_data.get(st.session_state.destination, {})
                )
                st.table(itinerary)
            else:
                st.write("Unable to fetch coordinates for itinerary.")
        else:
            st.write("Itinerary will be generated after recommendations are fetched.")

    with tab3:
        st.subheader(f"Nearby Places in {st.session_state.destination}")
        if st.session_state.nearby_places:
            lat, lng = get_coordinates(st.session_state.destination)
            if lat and lng:
                traffic_data_places = get_traffic_data_for_places(lat, lng, st.session_state.nearby_places)
                sorted_places = sort_places_by_traffic(st.session_state.nearby_places, traffic_data_places)
                places_df = pd.DataFrame([
                    {"Place": place["name"], "Travel Time (mins)": traffic_data_places.get(place["name"], {}).get("travel_time", 15)}
                    for place in sorted_places
                ])
                st.dataframe(places_df)
                
                # Directions button
                for place in sorted_places:
                    st.button(f"Directions to {place['name']}", key=place['name'], on_click=lambda p=place['name']: st.write(f"https://www.google.com/maps/dir/?api=1&origin={st.session_state.destination}&destination={p}"))
        else:
            st.write("No nearby places found or recommendations not yet generated.")

if __name__ == "__main__":
    main()