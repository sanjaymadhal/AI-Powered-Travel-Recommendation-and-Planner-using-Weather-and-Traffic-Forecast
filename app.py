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

# Load dataset (optional)
@st.cache_data
def load_data(file_path="holidify.csv"):
    try:
        df = pd.read_csv(file_path)
        df = df.drop_duplicates(subset=['City'])
        df['City'] = df['City'].str.strip()
        logger.info(f"Loaded dataset with {len(df)} records")
        return df
    except Exception as e:
        logger.error(f"Error loading data: {str(e)}")
        return None

# Load model (optional)
@st.cache_data
def load_model(filename="travel_recommendation_enhanced.joblib"):
    try:
        model_data = joblib.load(filename)
        logger.info("Model loaded successfully")
        return model_data
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        return None

# Fetch coordinates
@st.cache_data(ttl=86400)
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

# Cached API functions
@st.cache_data(ttl=3600)
def get_nearby_places_cached(lat, lng, radius=5000, api_key=GOOGLE_MAPS_API_KEY):
    url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius={radius}&type=tourist_attraction&key={api_key}"
    try:
        response = requests.get(url)
        data = response.json()
        if data["status"] == "OK":
            places = data["results"]
            nearby_places = [{
                "name": place["name"],
                "lat": place["geometry"]["location"]["lat"],
                "lng": place["geometry"]["location"]["lng"],
                "rating": place.get("rating", "N/A"),
                "photo": place.get("photos", [{}])[0].get("photo_reference", None)
            } for place in places]
            num_with_photos = sum(1 for place in nearby_places if place["photo"])
            logger.info(f"Fetched {len(nearby_places)} places, {num_with_photos} with photos")
            return nearby_places
        else:
            logger.warning(f"Places API failed: {data.get('error_message', 'Unknown error')}")
            return []
    except Exception as e:
        logger.error(f"Error fetching nearby places: {str(e)}")
        return []

@st.cache_data(ttl=1800)
def get_weather_data_cached(city, api_key=OPENWEATHER_API_KEY):
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
            return {"condition": condition, "temp": temp, "quality": quality}
        else:
            return {"condition": "unknown", "temp": 25, "quality": 5}
    except Exception as e:
        logger.error(f"Error fetching weather for {city}: {str(e)}")
        return {"condition": "error", "temp": 25, "quality": 5}

@st.cache_data(ttl=600)
def get_traffic_data_for_places_cached(origin_lat, origin_lng, places, api_key=GOOGLE_MAPS_API_KEY):
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
                    travel_time = element["duration_in_traffic"]["value"] // 60
                    traffic_level = min(max(travel_time // 5, 1), 10)
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

# Generate itinerary
def generate_itinerary(destination, places_data, travel_date, weather_data, place_ratings, num_days):
    itinerary = []
    sorted_places = sorted(places_data.items(), key=lambda x: x[1]["travel_time"] if isinstance(x[1], dict) else 15)
    weather_condition = weather_data.get("condition", "unknown")
    outdoor_friendly = "clear" in weather_condition or "sunny" in weather_condition or "few clouds" in weather_condition

    places_per_day = max(1, len(sorted_places) // num_days)
    for day in range(num_days):
        day_places = sorted_places[day * places_per_day:(day + 1) * places_per_day]
        for place, data in day_places:
            travel_time = data["travel_time"] if isinstance(data, dict) else 15
            traffic_symbol = "🟢" if travel_time < 20 else "🟡" if travel_time < 30 else "🔴"
            time_of_day = (
                "Morning" if travel_time < 25 and outdoor_friendly else
                "Afternoon" if travel_time < 40 else
                "Evening"
            )
            place_type = (
                "outdoor" if outdoor_friendly and travel_time < 25 else
                "mixed" if travel_time < 40 else
                "indoor or dining"
            )
            rating = place_ratings.get(place, "N/A")
            itinerary.append({
                "Day": f"Day {day + 1}",
                "Place": place,
                "Travel Time": f"{travel_time} mins",
                "Traffic": traffic_symbol,
                "Best Time": time_of_day,
                "Type": place_type,
                "Rating": rating
            })
    return itinerary

# Recommend places
def recommend_places(places, traffic_data, weather_quality, user_preferences, num_recommendations=5):
    weather_importance = user_preferences.get("weather_importance", 0.3)
    crowd_importance = user_preferences.get("crowd_importance", 0.3)
    attractions_importance = user_preferences.get("attractions_importance", 0.2)
    trip_type = user_preferences.get("trip_type", "Adventure")

    trip_type_weights = {
        "Adventure": 1.2,
        "Relaxation": 0.8,
        "Cultural": 1.5
    }
    trip_factor = trip_type_weights.get(trip_type, 1.0)

    scored_places = []
    max_travel_time = max([data["travel_time"] for data in traffic_data.values()] + [1])

    for place in places:
        travel_time = traffic_data.get(place["name"], {}).get("travel_time", 15)
        rating = float(place["rating"]) if place["rating"] != "N/A" else 3.0
        norm_travel = travel_time / max_travel_time
        norm_rating = rating / 5

        score = (
            (weather_importance * weather_quality / 10) +
            (crowd_importance * (1 - norm_travel) * (trip_factor if trip_type == "Adventure" else 1.0)) +
            (attractions_importance * norm_rating * (trip_factor if trip_type == "Cultural" else 1.0))
        ) * 10
        scored_places.append({
            "Place": place["name"],
            "Travel Time": travel_time,
            "Rating": rating,
            "Score": score,
            "lat": place["lat"],
            "lng": place["lng"]
        })

    return sorted(scored_places, key=lambda x: x["Score"], reverse=True)[:num_recommendations]

# Streamlit App
def main():
    st.set_page_config(page_title="Travel Recommender", layout="wide")
    st.title("🌍 Advanced Travel Planner & Recommender")
    st.write("Plan your trip with real-time data, maps, and personalized recommendations!")

    # Load data and model
    df = load_data()
    model_data = load_model()

    # Sidebar for preferences
    st.sidebar.header("Preferences")
    weather_importance = st.sidebar.slider("Weather Importance", 0.0, 1.0, 0.3)
    crowd_importance = st.sidebar.slider("Avoid Crowds Importance", 0.0, 1.0, 0.3)
    attractions_importance = st.sidebar.slider("Attractions Importance", 0.0, 1.0, 0.2)
    trip_type = st.sidebar.selectbox("Trip Type", ["Adventure", "Relaxation", "Cultural"])
    user_preferences = {
        "weather_importance": weather_importance,
        "crowd_importance": crowd_importance,
        "attractions_importance": attractions_importance,
        "trip_type": trip_type
    }

    # Initialize session state
    if "recommendations" not in st.session_state:
        st.session_state.recommendations = None
        st.session_state.weather_data = None
        st.session_state.destination = "Bangalore"
        st.session_state.nearby_places = None
        st.session_state.lat = None
        st.session_state.lng = None
        st.session_state.num_places_to_show = 6  # For "Show More" functionality

    # User location and destination inputs
    user_location = st.text_input("Your Current Location (for directions)", "")
    destination = st.text_input("Enter Destination City", st.session_state.destination)

    if st.button("Get Recommendations"):
        with st.spinner("Fetching recommendations..."):
            st.session_state.destination = destination
            lat, lng = get_coordinates(destination)
            if lat and lng:
                st.session_state.lat = lat
                st.session_state.lng = lng
                nearby_places = get_nearby_places_cached(lat, lng)
                num_with_photos = sum(1 for place in nearby_places if place["photo"])
                st.session_state.nearby_places = nearby_places
                st.session_state.weather_data = get_weather_data_cached(destination)
                traffic_data = get_traffic_data_for_places_cached(lat, lng, nearby_places)
                st.session_state.recommendations = recommend_places(
                    nearby_places,
                    traffic_data,
                    st.session_state.weather_data["quality"],
                    user_preferences
                )
            else:
                st.error("Could not fetch coordinates for the destination. Please try again.")

    # Tabs
    tab1, tab2, tab3 = st.tabs(["🏙️ Recommendations", "🗓️ Itinerary", "🏞️ Nearby Places"])

    with tab1:
        st.subheader("Top Recommendations")
        if st.session_state.recommendations and st.session_state.lat:
            lat = st.session_state.lat
            lng = st.session_state.lng
            weather = st.session_state.weather_data
            weather_icon = "☀️" if "clear" in weather["condition"] or "sunny" in weather["condition"] else "☁️" if "cloud" in weather["condition"] else "🌧️" if "rain" in weather["condition"] else "❓"
            st.markdown(
                f'<h3>Current Weather in {st.session_state.destination}: {weather_icon} {weather["condition"].capitalize()}, {weather["temp"]}°C</h3>',
                unsafe_allow_html=True
            )
            rec_df = pd.DataFrame(st.session_state.recommendations)[["Place", "Rating", "Score"]]
            rec_df["Rating"] = rec_df["Rating"].apply(lambda x: f"{x} ★" if x != "N/A" else "N/A")
            st.dataframe(rec_df, hide_index=True)
            m = folium.Map(location=[lat, lng], zoom_start=12)
            for place in st.session_state.recommendations:
                folium.Marker(
                    [place["lat"], place["lng"]],
                    popup=f"{place['Place']}: Score {place['Score']:.2f}",
                    icon=folium.Icon(color="blue")
                ).add_to(m)
            st_folium(m, width=700, height=500)
        else:
            st.write("Please enter a destination and click 'Get Recommendations'.")

    with tab2:
        st.subheader("Travel Itinerary")
        if st.session_state.weather_data and st.session_state.nearby_places and st.session_state.lat:
            lat = st.session_state.lat
            lng = st.session_state.lng
            num_days = st.number_input("Number of Days for Itinerary", min_value=1, max_value=7, value=3)
            traffic_data = get_traffic_data_for_places_cached(lat, lng, st.session_state.nearby_places)
            place_ratings = {place["name"]: place["rating"] for place in st.session_state.nearby_places}
            itinerary = generate_itinerary(
                st.session_state.destination,
                traffic_data,
                datetime.now(),
                st.session_state.weather_data,
                place_ratings,
                num_days
            )
            st.write(f"Based on the current weather ({st.session_state.weather_data['condition']}), here's your suggested itinerary:")
            for day in range(1, num_days + 1):
                items = [item for item in itinerary if item["Day"] == f"Day {day}"]
                if items:
                    with st.expander(f"Day {day} Activities"):
                        itin_df = pd.DataFrame(items)[["Place", "Type", "Travel Time", "Traffic", "Rating"]]
                        itin_df["Rating"] = itin_df["Rating"].apply(lambda x: f"{x} ★" if x != "N/A" else "N/A")
                        st.dataframe(itin_df, hide_index=True)
            m = folium.Map(location=[lat, lng], zoom_start=12)
            for item in itinerary:
                place_info = next((p for p in st.session_state.nearby_places if p["name"] == item["Place"]), None)
                if place_info:
                    color = "green" if item["Best Time"] == "Morning" else "orange" if item["Best Time"] == "Afternoon" else "red"
                    folium.Marker(
                        [place_info["lat"], place_info["lng"]],
                        popup=f"{item['Place']}<br>{item['Day']}<br>{item['Best Time']}<br>{item['Travel Time']} {item['Traffic']}",
                        icon=folium.Icon(color=color)
                    ).add_to(m)
            st_folium(m, width=700, height=500)
        else:
            st.write("Itinerary will be generated after recommendations are fetched.")

    with tab3:
        st.subheader(f"Nearby Places in {st.session_state.destination}")
        if st.session_state.nearby_places:
            lat = st.session_state.lat
            lng = st.session_state.lng
            if lat and lng:
                traffic_data = get_traffic_data_for_places_cached(lat, lng, st.session_state.nearby_places)
                num_with_photos = sum(1 for place in st.session_state.nearby_places if place["photo"])
                st.write(f"Showing {len(st.session_state.nearby_places)} nearby places, {num_with_photos} with photos")
                places_to_show = st.session_state.nearby_places[:st.session_state.num_places_to_show]
                cols = st.columns(3)  # Create a 3-column grid
                for i, place in enumerate(places_to_show):
                    with cols[i % 3]:  # Distribute places across columns
                        # Place name in bold
                        st.markdown(f"**{place['name']}**")
                        # Photo display with original aspect ratio
                        if place["photo"]:
                            photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={place['photo']}&key={GOOGLE_MAPS_API_KEY}"
                            st.markdown(
                                f'<img src="{photo_url}" style="max-width:100%; height:auto; border-radius:5px; margin-bottom:10px;">',
                                unsafe_allow_html=True
                            )
                        else:
                            st.write("No photo available")
                        # Compact details
                        st.write(f"Rating: {place['rating']} ★" if place['rating'] != 'N/A' else "Rating: N/A")
                        travel_time = traffic_data.get(place['name'], {}).get('travel_time', 15)
                        st.write(f"Travel Time: {travel_time} mins")
                        # Directions button
                        origin = user_location if user_location else st.session_state.destination
                        directions_url = f"https://www.google.com/maps/dir/?api=1&origin={origin}&destination={place['name']}"
                        if st.button("Get Directions", key=place['name']):
                            st.markdown(f'<a href="{directions_url}" target="_blank">Open in Google Maps</a>', unsafe_allow_html=True)
                        # Subtle divider
                        st.markdown("<hr style='margin:20px 0; border:0; border-top:1px solid #eee;'>", unsafe_allow_html=True)
                # "Show More" button centered below the grid
                st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
                if st.button("Show More") and st.session_state.num_places_to_show < len(st.session_state.nearby_places):
                    st.session_state.num_places_to_show += 6
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.write("Could not fetch coordinates for the destination.")
        else:
            st.write("No nearby places found or recommendations not yet generated.")

if __name__ == "__main__":
    main()
