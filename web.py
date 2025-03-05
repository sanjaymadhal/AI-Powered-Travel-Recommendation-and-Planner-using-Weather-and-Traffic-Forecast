import streamlit as st
import pandas as pd
import requests
import logging
from datetime import datetime


# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables

OPENWEATHER_API_KEY = "3fcbb4e945f4372e7b24f6d4b17b9ec4"
GOOGLE_MAPS_API_KEY = "AIzaSyDHuLqogx1pAdE8ljnahXazw7D6vFrshkE"

if not OPENWEATHER_API_KEY or not GOOGLE_MAPS_API_KEY:
    st.error("API keys not found. Please set up a .env file with OPENWEATHER_API_KEY and GOOGLE_MAPS_API_KEY.")
    st.stop()

# Fetch coordinates for a city
@st.cache_data(ttl=86400)
def get_coordinates(city, api_key=GOOGLE_MAPS_API_KEY):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={city}&key={api_key}"
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

# Fetch coordinates for user's location
@st.cache_data(ttl=86400)
def get_user_coordinates(user_location, api_key=GOOGLE_MAPS_API_KEY):
    if not user_location:
        return None, None
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={user_location}&key={api_key}"
    try:
        response = requests.get(url)
        data = response.json()
        if data["status"] == "OK" and data["results"]:
            location = data["results"][0]["geometry"]["location"]
            return location["lat"], location["lng"]
        else:
            logger.warning(f"Geocoding failed for user location {user_location}: {data.get('error_message', 'Unknown error')}")
            return None, None
    except Exception as e:
        logger.error(f"Error fetching coordinates for user location {user_location}: {str(e)}")
        return None, None

# Fetch nearby places
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
                "photo": place.get("photos", [{}])[0].get("photo_reference", None),
                "types": place.get("types", [])
            } for place in places]
            logger.info(f"Fetched {len(nearby_places)} places")
            return nearby_places
        else:
            logger.warning(f"Places API failed: {data.get('error_message', 'Unknown error')}")
            return []
    except Exception as e:
        logger.error(f"Error fetching nearby places: {str(e)}")
        return []

# Fetch weather data
@st.cache_data(ttl=1800)
def get_weather_data_cached(city, api_key=OPENWEATHER_API_KEY):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
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

# Fetch traffic data
@st.cache_data(ttl=600)
def get_traffic_data_for_places_cached(origin_lat, origin_lng, places, api_key=GOOGLE_MAPS_API_KEY):
    traffic_data = {}
    default_count = 0
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
                    default_count += 1
                traffic_data[place["name"]] = {"travel_time": travel_time, "traffic_level": traffic_level}
            else:
                traffic_data[place["name"]] = {"travel_time": 15, "traffic_level": 5}
                default_count += 1
        except Exception as e:
            logger.error(f"Error fetching traffic for {place['name']}: {str(e)}")
            traffic_data[place["name"]] = {"travel_time": 15, "traffic_level": 5}
            default_count += 1
    if default_count > len(places) // 2:
        logger.warning("More than half of traffic data requests failed; using default travel times.")
    return traffic_data

# Categorize places based on types
place_type_categories = {
    "park": "outdoor",
    "museum": "indoor",
    "art_gallery": "indoor",
    "restaurant": "dining",
    "cafe": "dining",
    "bar": "dining",
    "amusement_park": "outdoor",
    "zoo": "outdoor",
    "shopping_mall": "indoor",
    "point_of_interest": "mixed",
    "establishment": "mixed",
}

def categorize_place(types):
    for t in types:
        if t in place_type_categories:
            return place_type_categories[t]
    return "mixed"

# Generate itinerary
def generate_itinerary(recommendations, weather_data, user_preferences, num_days):
    itinerary = []
    sorted_recs = sorted(recommendations, key=lambda x: x["Travel Time"])
    outdoor_friendly = "clear" in weather_data["condition"] or "sunny" in weather_data["condition"] or "few clouds" in weather_data["condition"]
    
    for day in range(num_days):
        start_idx = day * 4
        end_idx = start_idx + 4
        day_places = sorted_recs[start_idx:end_idx]
        if not day_places:
            break
        for place in day_places:
            category = categorize_place(place.get("types", []))
            travel_time = place["Travel Time"]
            traffic_symbol = "🟢" if travel_time < 20 else "🟡" if travel_time < 30 else "🔴"
            
            if category == "outdoor" and outdoor_friendly:
                best_time = "Morning" if start_idx % 3 == 0 else "Afternoon" if start_idx % 3 == 1 else "Evening"
            elif category == "indoor":
                best_time = "Anytime"
            elif category == "dining":
                best_time = "Lunch" if start_idx % 2 == 0 else "Dinner"
            else:
                best_time = "Afternoon"
            
            itinerary.append({
                "Day": f"Day {day + 1}",
                "Place": place["Place"],
                "Category": category.capitalize(),
                "Travel Time": f"{travel_time} mins",
                "Traffic": traffic_symbol,
                "Best Time": best_time,
                "Rating": place["Rating"],
                "lat": place["lat"],
                "lng": place["lng"]
            })
    return itinerary

# Recommend places
def recommend_places(places, traffic_data, weather_quality, user_preferences, sort_by_travel_time=False):
    weather_importance = user_preferences.get("weather_importance", 0.3)
    crowd_importance = user_preferences.get("crowd_importance", 0.3)
    attractions_importance = user_preferences.get("attractions_importance", 0.2)
    trip_type = user_preferences.get("trip_type", "Adventure")

    trip_type_weights = {"Adventure": 1.2, "Relaxation": 0.8, "Cultural": 1.5}
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
            "lng": place["lng"],
            "types": place["types"]
        })

    if sort_by_travel_time:
        sorted_places = sorted(scored_places, key=lambda x: (x["Travel Time"], -x["Score"]))
    else:
        sorted_places = sorted(scored_places, key=lambda x: -x["Score"])
    
    return sorted_places

# Generate PDF with error handling
def generate_itinerary_pdf(itinerary, destination, num_days):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, f"Travel Itinerary for {destination}", ln=True, align="C")
        pdf.set_font("Arial", "I", 12)
        pdf.cell(0, 10, f"Generated on {datetime.now().strftime('%Y-%m-%d')}", ln=True, align="C")
        pdf.ln(10)
        
        for day in range(1, num_days + 1):
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, f"Day {day}", ln=True)
            pdf.set_font("Arial", "", 12)
            items = [item for item in itinerary if item["Day"] == f"Day {day}"]
            for item in items:
                pdf.cell(0, 10, f"- {item['Place']} ({item['Category']})", ln=True)
                pdf.cell(0, 10, f"  Best Time: {item['Best Time']}, Travel Time: {item['Travel Time']}, Rating: {item['Rating']} ★", ln=True)
            pdf.ln(5)
        
        return pdf.output(dest="S")
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        return None

# Streamlit App
def main():
    st.set_page_config(page_title="Travel Planner", layout="wide")
    st.markdown("<h1 style='text-align: center; color: #2c3e50;'>🌍 WanderWise Travel Planner</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #7f8c8d;'>Plan your perfect trip with real-time insights!</p>", unsafe_allow_html=True)

    # Initialize session state
    if "recommendations" not in st.session_state:
        st.session_state.recommendations = None
        st.session_state.weather_data = None
        st.session_state.destination = "Bangalore"
        st.session_state.nearby_places = None
        st.session_state.lat = None
        st.session_state.lng = None
        st.session_state.user_lat = None
        st.session_state.user_lng = None
        st.session_state.num_places_to_show = 6

    # Sidebar for preferences
    st.sidebar.header("Your Preferences")
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

    # Input section
    col1, col2 = st.columns(2)
    with col1:
        user_location = st.text_input("Your Current Location (Optional, for directions)", "")
    with col2:
        destination = st.text_input("Destination City", st.session_state.destination)

    if st.button("Plan My Trip", key="plan_trip"):
        with st.spinner("Fetching your travel plan..."):
            st.session_state.destination = destination
            lat, lng = get_coordinates(destination)
            user_lat, user_lng = get_user_coordinates(user_location)
            st.session_state.user_lat = user_lat
            st.session_state.user_lng = user_lng
            origin_lat, origin_lng = (user_lat, user_lng) if user_lat and user_lng else (lat, lng)

            if lat and lng:
                st.session_state.lat, st.session_state.lng = lat, lng
                nearby_places = get_nearby_places_cached(lat, lng)
                st.session_state.nearby_places = nearby_places
                st.session_state.weather_data = get_weather_data_cached(destination)
                traffic_data = get_traffic_data_for_places_cached(origin_lat, origin_lng, nearby_places)
                sort_by_travel_time = user_lat is not None and user_lng is not None
                st.session_state.recommendations = recommend_places(
                    nearby_places, traffic_data, st.session_state.weather_data["quality"], user_preferences, sort_by_travel_time
                )
            else:
                st.error("Could not fetch coordinates for the destination. Please try again.")

    # Tabs
    tab1, tab2, tab3 = st.tabs(["🏙️ Top Picks", "🗓️ Itinerary", "🏞️ Explore Nearby"])

    with tab1:
        st.subheader("Top Recommendations")
        if st.session_state.recommendations and st.session_state.lat:
            weather = st.session_state.weather_data
            weather_icon = "☀️" if "clear" in weather["condition"] or "sunny" in weather["condition"] else "☁️" if "cloud" in weather["condition"] else "🌧️" if "rain" in weather["condition"] else "❓"
            st.markdown(
                f"<h3 style='color: #2980b9;'>Weather in {destination}: {weather_icon} {weather['condition'].capitalize()}, {weather['temp']}°C</h3>",
                unsafe_allow_html=True
            )
            if st.session_state.user_lat and st.session_state.user_lng:
                st.write("Recommendations sorted by travel time from your location.")
            else:
                st.write("Recommendations sorted by overall score.")
            top_5 = st.session_state.recommendations[:5]
            rec_df = pd.DataFrame(top_5)[["Place", "Travel Time", "Rating"]]
            rec_df["Travel Time"] = rec_df["Travel Time"].apply(lambda x: f"{x} mins")
            rec_df["Rating"] = rec_df["Rating"].apply(lambda x: f"{x} ★")
            st.dataframe(rec_df.style.set_properties(**{'text-align': 'left'}), hide_index=True)
            m = folium.Map(location=[st.session_state.lat, st.session_state.lng], zoom_start=12)
            for place in top_5:
                folium.Marker(
                    [place["lat"], place["lng"]],
                    popup=f"{place['Place']}: {place['Travel Time']} mins, {place['Rating']} ★",
                    icon=folium.Icon(color="blue", icon="star")
                ).add_to(m)
            st_folium(m, width=725, height=400)
        else:
            st.info("Enter a destination and click 'Plan My Trip' to see recommendations.")

    with tab2:
        st.subheader("Your Travel Itinerary")
        if st.session_state.recommendations and st.session_state.weather_data:
            num_days = st.number_input("Number of Days", min_value=1, max_value=7, value=3)
            itinerary = generate_itinerary(st.session_state.recommendations, st.session_state.weather_data, user_preferences, num_days)
            st.write(f"Based on current weather ({st.session_state.weather_data['condition']}) and your preferences:")
            for day in range(1, num_days + 1):
                items = [item for item in itinerary if item["Day"] == f"Day {day}"]
                if items:
                    with st.expander(f"Day {day} - Explore {destination}", expanded=day == 1):
                        itin_df = pd.DataFrame(items)[["Place", "Category", "Travel Time", "Traffic", "Best Time", "Rating"]]
                        itin_df["Rating"] = itin_df["Rating"].apply(lambda x: f"{x} ★")
                        st.dataframe(itin_df.style.set_properties(**{'text-align': 'left'}), hide_index=True)
            m = folium.Map(location=[st.session_state.lat, st.session_state.lng], zoom_start=12)
            for item in itinerary:
                color = "green" if "Morning" in item["Best Time"] else "orange" if "Afternoon" in item["Best Time"] else "red"
                folium.Marker(
                    [item["lat"], item["lng"]],
                    popup=f"{item['Place']}<br>{item['Day']}<br>{item['Best Time']}",
                    icon=folium.Icon(color=color)
                ).add_to(m)
            st_folium(m, width=725, height=400)
            if itinerary:
                pdf_str = generate_itinerary_pdf(itinerary, st.session_state.destination, num_days)
                if pdf_str:
                    st.download_button(
                        label="Download Itinerary as PDF",
                        data=pdf_str,
                        file_name=f"{st.session_state.destination}_itinerary.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.error("Failed to generate PDF. Please try again.")
            else:
                st.warning("No itinerary available to download.")
        else:
            st.info("Itinerary will appear after fetching recommendations.")

    with tab3:
        st.subheader(f"Explore Nearby in {st.session_state.destination}")
        if st.session_state.nearby_places:
            origin_lat, origin_lng = (st.session_state.user_lat, st.session_state.user_lng) if st.session_state.user_lat and st.session_state.user_lng else (st.session_state.lat, st.session_state.lng)
            traffic_data = get_traffic_data_for_places_cached(origin_lat, origin_lng, st.session_state.nearby_places)
            places_to_show = st.session_state.nearby_places[:st.session_state.num_places_to_show]
            cols = st.columns(3)
            for i, place in enumerate(places_to_show):
                with cols[i % 3]:
                    st.markdown(f"**{place['name']}**")
                    if place["photo"]:
                        photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={place['photo']}&key={GOOGLE_MAPS_API_KEY}"
                        st.markdown(
                            f'<img src="{photo_url}" style="max-width:100%; height:auto; border-radius:8px; margin:5px 0;">',
                            unsafe_allow_html=True
                        )
                    else:
                        st.write("No photo available")
                    st.write(f"Rating: {place['rating']} ★" if place['rating'] != 'N/A' else "Rating: N/A")
                    travel_time = traffic_data.get(place['name'], {}).get('travel_time', 15)
                    st.write(f"Travel Time: {travel_time} mins")
                    origin = user_location if user_location else st.session_state.destination
                    directions_url = f"https://www.google.com/maps/dir/?api=1&origin={origin}&destination={place['name']}"
                    st.markdown(
                        f'<a href="{directions_url}" target="_blank" style="text-decoration:none;"><button style="background-color:#3498db; color:white; padding:5px 10px; border:none; border-radius:5px;">Get Directions</button></a>',
                        unsafe_allow_html=True
                    )
                    st.markdown("<hr style='margin:15px 0; border:0; border-top:1px solid #ddd;'>", unsafe_allow_html=True)
            st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
            if st.button("Show More", key="show_more") and st.session_state.num_places_to_show < len(st.session_state.nearby_places):
                st.session_state.num_places_to_show += 6
                st.experimental_rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("Nearby places will load after recommendations are fetched.")

if __name__ == "__main__":
    main()
