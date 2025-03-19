import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import random
import json
from streamlit_lottie import st_lottie
import base64
import os
from streamlit_elements import elements, mui, html
import numpy as np
import joblib
import logging
import folium
from streamlit_folium import st_folium
from dotenv import load_dotenv
import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch


def get_image_base64(image_path):
    """Convert local image to Base64 format."""
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None



# Set API keys
GOOGLE_MAPS_API_KEY = "AIzaSyBdRYZ_JIDxNbK8sUP6s2zGbbEh--0An0c"


# Extended city data with more attractions
city_data = {
    "Bengaluru": {
        "image": "bengaluru.jpg",
        "significance": "The Silicon Valley of India, known for its vibrant culture and IT hubs.",
        "info": "Best visited between October and March.",
        "attractions": [
            {"name": "Lalbagh Botanical Garden", "distance": "5 km", "category": "Nature"},
            {"name": "Cubbon Park", "distance": "3 km", "category": "Nature"},
            {"name": "Bangalore Palace", "distance": "7 km", "category": "Historical"},
            {"name": "ISKCON Temple", "distance": "9 km", "category": "Religious"},
            {"name": "Wonderla Amusement Park", "distance": "28 km", "category": "Entertainment"},
            {"name": "UB City Mall", "distance": "4 km", "category": "Shopping"},
            {"name": "Bannerghatta National Park", "distance": "22 km", "category": "Nature"},
            {"name": "Commercial Street", "distance": "5 km", "category": "Shopping"}
        ],
        "nearby_cities": ["Mysuru", "Chennai", "Coimbatore"],
        "local_dishes": ["Bisi Bele Bath", "Dosa", "Filter Coffee", "Ragi Mudde"],
        "coordinates": {"lat": 12.9716, "lng": 77.5946}
    },
    "Mysuru": {
        "image": "mysuru.jpg",
        "significance": "Famous for its royal heritage and grand Dasara festival.",
        "info": "Best visited between September and February.",
        "attractions": [
            {"name": "Mysore Palace", "distance": "2 km", "category": "Historical"},
            {"name": "Chamundi Hills", "distance": "13 km", "category": "Nature"},
            {"name": "Brindavan Gardens", "distance": "21 km", "category": "Nature"},
            {"name": "St. Philomena's Church", "distance": "3 km", "category": "Religious"},
            {"name": "Mysore Zoo", "distance": "4 km", "category": "Nature"},
            {"name": "Railway Museum", "distance": "5 km", "category": "Historical"},
            {"name": "Devaraja Market", "distance": "2 km", "category": "Shopping"},
            {"name": "Karanji Lake", "distance": "6 km", "category": "Nature"}
        ],
        "nearby_cities": ["Bengaluru", "Coimbatore", "Ooty"],
        "local_dishes": ["Mysore Pak", "Mysore Masala Dosa", "Nanjangud Rasabale"],
        "coordinates": {"lat": 12.2958, "lng": 76.6394}
    },
    "Chennai": {
        "image": "chennai.jpg",
        "significance": "A coastal city with rich cultural history and beautiful beaches.",
        "info": "Best visited between November and February.",
        "attractions": [
            {"name": "Marina Beach", "distance": "4 km", "category": "Nature"},
            {"name": "Kapaleeshwarar Temple", "distance": "6 km", "category": "Religious"},
            {"name": "Fort St. George", "distance": "3 km", "category": "Historical"},
            {"name": "Government Museum", "distance": "5 km", "category": "Historical"},
            {"name": "Santhome Basilica", "distance": "7 km", "category": "Religious"},
            {"name": "Phoenix Marketcity", "distance": "12 km", "category": "Shopping"},
            {"name": "Elliot's Beach", "distance": "9 km", "category": "Nature"},
            {"name": "Arignar Anna Zoological Park", "distance": "30 km", "category": "Nature"}
        ],
        "nearby_cities": ["Pondicherry", "Mahabalipuram", "Vellore"],
        "local_dishes": ["Chettinad Chicken", "Filter Coffee", "Idli Sambhar", "Madras Fish Curry"],
        "coordinates": {"lat": 13.0827, "lng": 80.2707}
    },
    "Pondicherry": {
        "image": "pondicherry.jpg",
        "significance": "Former French colony with beautiful architecture and beaches.",
        "info": "Best visited between October and March.",
        "attractions": [
            {"name": "Promenade Beach", "distance": "1 km", "category": "Nature"},
            {"name": "Auroville", "distance": "10 km", "category": "Spiritual"},
            {"name": "Paradise Beach", "distance": "7 km", "category": "Nature"},
            {"name": "Basilica of the Sacred Heart of Jesus", "distance": "3 km", "category": "Religious"},
            {"name": "French Quarter", "distance": "2 km", "category": "Historical"},
            {"name": "Pondicherry Museum", "distance": "2 km", "category": "Historical"},
            {"name": "Sri Aurobindo Ashram", "distance": "1 km", "category": "Spiritual"},
            {"name": "Chunnambar Boat House", "distance": "8 km", "category": "Nature"}
        ],
        "nearby_cities": ["Chennai", "Mahabalipuram", "Thanjavur"],
        "local_dishes": ["Bouillabaisse", "Fish Curry", "Creole Prawns", "Creme Caramel"],
        "coordinates": {"lat": 11.9416, "lng": 79.8083}
    }
}




                
# Function to generate mock itinerary
def generate_itinerary(city, days):
    itinerary = {}
    attractions = city_data[city]["attractions"]
    
    for day in range(1, days + 1):
        day_attractions = random.sample(attractions, min(3, len(attractions)))
        
        morning = day_attractions[0]["name"] if len(day_attractions) > 0 else "Free time"
        afternoon = day_attractions[1]["name"] if len(day_attractions) > 1 else "Local cuisine exploration"
        evening = day_attractions[2]["name"] if len(day_attractions) > 2 else "Shopping and relaxation"
        
        itinerary[f"Day {day}"] = {
            "Morning": morning,
            "Afternoon": afternoon,
            "Evening": evening
        }
    
    return itinerary

# Function to get weather forecast



# Main Streamlit UI setup
st.set_page_config(page_title="AI Travel Planner", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
        text-shadow: 1px 1px 2px #0D47A1;
    }
    .sub-header {
        font-size: 1.8rem;
        color: #0D47A1;
        margin-top: 1.5rem;
    }
    .city-card {
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        padding: 1rem;
        transition: transform 0.3s;
    }
    .city-card:hover {
        transform: scale(1.03);
    }
    .highlight {
        background-color: #E3F2FD;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #1E88E5;
    }
    .attraction-card {
        background-color: white;
        padding: 0.8rem;
        border-radius: 5px;
        margin-bottom: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .category-tag {
        background-color: #E1F5FE;
        color: #0277BD;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 0.8rem;
        margin-left: 10px;
    }
    .weather-card {
        background: linear-gradient(135deg, #42A5F5, #1976D2);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* Fix for sections with visibility issues */
    .unique-local-experience h1, 
    .unique-local-experience h2,
    .unique-local-experience h3,
    .unique-local-experience p,
    .unique-local-experience li,
    .ai-assistant h1,
    .ai-assistant h2,
    .ai-assistant h3,
    .ai-assistant p,
    .ai-assistant li,
    .travel-inspiration h1,
    .travel-inspiration h2,
    .travel-inspiration h3,
    .travel-inspiration p,
    .travel-inspiration li,
    .travel-tips h1,
    .travel-tips h2,
    .travel-tips h3,
    .travel-tips p,
    .travel-tips li {
        color: #000000 !important;
    }
    
    /* Additional fix for AI assistant section */
    .ai-assistant-section h1,
    .ai-assistant-section h2,
    .ai-assistant-section h3,
    .ai-assistant-section p,
    .ai-assistant-section li {
        color: #000000 !important;
    }
</style>
""", unsafe_allow_html=True)


# Function to load Lottie animation
def load_lottie_url(url):
    response = requests.get(url)
    if response.status_code != 200:
        return None
    return json.loads(response.text)

# Initialize session state variables if needed
if 'selected_city' not in st.session_state:
    st.session_state.selected_city = None
if 'trip_plan' not in st.session_state:
    st.session_state.trip_plan = None

# Sidebar content
with st.sidebar:
    # Smaller animation that loads once
    travel_animation_url = "https://assets8.lottiefiles.com/packages/lf20_UgZWvP.json"
    lottie_travel = load_lottie_url(travel_animation_url)
    if lottie_travel:
        # Very small, very fast animation
        st_lottie(
            lottie_travel, 
            speed=2,            # Double speed
            height=175,          # Even smaller
            key="travel_animation",
            loop=True,         # Play only once
            quality="high"       # Lower quality for faster loading
        )
    else:
        st.image("travel.png", use_column_width=True, width=80)

# Create a more visually appealing header with gradient, icon and subtle animation
st.sidebar.markdown("""
<div style="text-align: center;">
    <h1 style="
        background: linear-gradient(45deg, #FF5A5F, #FF385C);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 800;
        letter-spacing: 1px;
        margin-bottom: 0;
        padding: 10px 0;
        font-size: 2.2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        display: inline-block;
    ">
    <span>✈️</span> WANDERWISE
    </h1>
    <p style="
        color: #666;
        font-style: italic;
        margin-top: 0;
        font-size: 1.0rem;
    ">Explore. Discover. Experience.</p>
    
</div>
                    
""", unsafe_allow_html=True)

# Animation with minimal impact



# Navigation options
page = st.sidebar.radio(
    "",
    options=[
        "🏠 Home",
        "✈️ Plan Your Trip",
        "🔍 Neighborhood Navigator",
        "💡 Trip Ideas"
    ]
)


# Return the selected page for your existing content sections to use
# This ensures your existing content logic will work with the new page variable
# ------------- HOME PAGE -------------------
if page == "🏠 Home":
    st.markdown("""
<div style="text-align: center; margin-bottom: 2rem;">
    <h1 style="
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(120deg, #1E88E5, #9C27B0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
        padding: 1rem 0;
        font-family: 'Helvetica Neue', sans-serif;
    ">
        ✈️ Welcome to WANDERWISE
    </h1>
    <h3 style="
        color: #555;
        font-weight: 400;
        margin-top: 0;
        padding-bottom: 1rem;
        border-bottom: 2px solid #f0f0f0;
    ">
        Your Everyday Travel Companion
    </h3>
</div>
""", unsafe_allow_html=True)
    
   
    
    # Top destinations
    st.markdown("<h2 class='sub-header'>🌆 Top Destinations</h2>", unsafe_allow_html=True)
    cols = st.columns(4)     
    cities = list(city_data.keys())          
    for i, city in enumerate(cities):         
        if i < len(cols):            
            with cols[i]:                 
                image_path = f"images/{city}.jpg"  # Ensure images are inside the 'images/' directory

                image_base64 = get_image_base64(image_path)
                image_src = f"data:image/jpeg;base64,{image_base64}" if image_base64 else "https://via.placeholder.com/300x200.png?text=No+Image"

                st.markdown(f"""
                    <div class='city-card'>
                        <img src="{image_src}" width="100%" style="border-radius: 8px;">
                        <h3>{city}</h3>
                        <p style="font-size: 0.9rem;">{city_data[city]["significance"][:80]}...</p>
                        <p style="font-size: 0.8rem;">Top attraction: {city_data[city]["attractions"][0]["name"]}</p>
                    </div>
                """, unsafe_allow_html=True)
                                 
                if st.button(f"Explore {city}", key=f"explore{city}"):                     
                    st.session_state.selected_city = city
    
     # Show selected city info if a city was selected
    if st.session_state.selected_city:
        city = st.session_state.selected_city
        city_info = city_data[city]
        
        st.markdown(f"<h2 class='sub-header'>🏙️ {city}</h2>", unsafe_allow_html=True)
        
        # City info in columns
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"""
            <div style="background: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.7)), 
                        url('https://via.placeholder.com/800x400.png?text={city}'); 
                        background-size: cover; color: white; padding: 2rem; border-radius: 10px;">
                <h3>{city}</h3>
                <p><strong>Significance:</strong> {city_info['significance']}</p>
                <p><strong>Best Time to Visit:</strong> {city_info['info']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            local_foods = ", ".join(city_info["local_dishes"])
            st.markdown(f"""
            <div style="margin-top: 1rem;">
                <strong>Local Cuisine:</strong> {local_foods}
            </div>
            """, unsafe_allow_html=True)
        
            
        with col2:
            st.subheader("Top Attractions")
            for attraction in city_info["attractions"][:4]:
                st.markdown(f"""
    <style>
        .attraction-card {{
            background-color: #2C3E50; /* Dark blue background */
            color: #ECF0F1; /* Light text color */
            padding: 10px;
            border-radius: 10px;
            margin: 10px 0;
        }}
        .category-tag {{
            background-color: #E74C3C; /* Red category tag */
            color: white;
            padding: 3px 7px;
            border-radius: 5px;
            font-size: 12px;
        }}
    </style>
    <div class='attraction-card'>
        <strong>{attraction['name']}</strong> 
        <span class='category-tag'>{attraction['category']}</span>
        <br><small>{attraction['distance']} from city center</small>
    </div>
""", unsafe_allow_html=True)

            
            
        # Google Maps Embed
        st.markdown("<h3 class='sub-header'>📍 Location</h3>", unsafe_allow_html=True)
        st.markdown(f"""
        <iframe width="100%" height="350" style="border:0; border-radius: 10px;" 
        loading="lazy" allowfullscreen referrerpolicy="no-referrer-when-downgrade"
        src="https://www.google.com/maps/embed/v1/place?key={GOOGLE_MAPS_API_KEY}&q={city}">
        </iframe>""", unsafe_allow_html=True)
    

    
    
    
    # Travel inspiration
    st.markdown("""
    <style>
    .sub-header {
        color: #f0f0f0;
        font-size: 28px;
        margin-bottom: 1.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #4a4a4a;
    }
    
    .inspiration-container {
        display: flex;
        flex-wrap: wrap;
        gap: 16px;
        margin-bottom: 2rem;
    }
    
    .highlight {
        background: linear-gradient(145deg, #2a2a2a, #333333);
        border-radius: 12px;
        padding: 1.5rem;
        height: 100%;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        position: relative;
        overflow: hidden;
        border-left: 4px solid;
    }
    
    .highlight:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.3);
    }
    
    .nature {
        border-color: #4CAF50;
    }
    
    .culture {
        border-color: #E91E63;
    }
    
    .culinary {
        border-color: #FF9800;
    }
    
    .highlight h4 {
        color: #ffffff;
        font-size: 20px;
        margin-bottom: 0.8rem;
        font-weight: 600;
    }
    
    .highlight p {
        color: #c0c0c0;
        font-size: 15px;
        line-height: 1.5;
        margin: 0;
    }
    
    .highlight-icon {
        font-size: 24px;
        margin-bottom: 0.8rem;
        display: block;
    }
    
    @media (max-width: 768px) {
        .inspiration-container {
            flex-direction: column;
        }
    }
    </style>

    <h2 class='sub-header'>🌟 Travel Inspiration</h2>

    <div class="inspiration-container">
    <div class='highlight nature' style="flex: 1;">
        <span class="highlight-icon">🌿</span>
        <h4>Nature Escapes</h4>
        <p>Discover the most beautiful natural attractions across South India. From misty hill stations to serene backwaters.</p>
    </div>
    
    <div class='highlight culture' style="flex: 1;">
        <span class="highlight-icon">🏛️</span>
        <h4>Cultural Experiences</h4>
        <p>Immerse yourself in the rich cultural heritage of historic cities. Explore ancient temples, palaces and traditions.</p>
    </div>
    
    <div class='highlight culinary' style="flex: 1;">
        <span class="highlight-icon">🍽️</span>
        <h4>Culinary Adventures</h4>
        <p>Taste the authentic flavors of traditional and modern cuisine. Enjoy street food, fine dining and cooking classes.</p>
    </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<h2 class='sub-header'>🌍 Journey Styles</h2>", unsafe_allow_html=True)
    
    theme_cols = st.columns(3)
    
    themes = [
        {"name": "Heritage & History", "icon": "🏛️", "color": "#FFF59D"},
        {"name": "Nature & Wildlife", "icon": "🌿", "color": "#A5D6A7"},
        {"name": "Food & Cuisine", "icon": "🍽️", "color": "#FFAB91"},
        {"name": "Adventure", "icon": "🧗", "color": "#90CAF9"},
        {"name": "Relaxation", "icon": "🧘", "color": "#CE93D8"},
        {"name": "Cultural Immersion", "icon": "🎭", "color": "#F48FB1"}
    ]
    
    for i, theme in enumerate(themes):
        with theme_cols[i % 3]:
            st.markdown(f"""
            <div style="background-color: {theme['color']}; padding: 1.5rem; border-radius: 10px; 
                      margin-bottom: 1rem; text-align: center; cursor: pointer;">
                <h1 style="font-size: 2.5rem; margin: 0; color: black;">{theme['icon']}</h1>
                <h3 style="margin: 0.5rem 0; color: black;">{theme['name']}</h3>
            </div>
            """, unsafe_allow_html=True)
   

# ------------- PLAN YOUR TRIP PAGE -------------------
elif page == "✈️ Plan Your Trip":
    import streamlit as st
    import pandas as pd
    import requests
    import logging
    from datetime import datetime
    import folium
    from streamlit_folium import st_folium
    from dotenv import load_dotenv
    import os
    from fpdf import FPDF
    import io
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.units import inch
    from reportlab.lib.styles import getSampleStyleSheet
    import json

    # Set up logging (optional, for debugging)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    # Multi-language support
    # Dictionary of translations for supported Indian languages
    LANGUAGES = {
        "English": "en",
        "हिंदी (Hindi)": "hi",
        "தமிழ் (Tamil)": "ta",
        "తెలుగు (Telugu)": "te",
        "ಕನ್ನಡ (Kannada)": "kn",
        "മലയാളം (Malayalam)": "ml",
        "বাংলা (Bengali)": "bn",
        "ਪੰਜਾਬੀ (Punjabi)": "pa",
        "ગુજરાતી (Gujarati)": "gu",
        "मराठी (Marathi)": "mr"
    }

    # Dictionary of translation content
    def load_translations():
        translations = {
            "en": {
                "app_title": "🌍 WanderWise Travel Planner",
                "app_subtitle": "Plan your perfect trip with real-time insights!",
                "your_preferences": "Your Preferences",
                "weather_importance": "Weather Importance",
                "avoid_crowds": "Avoid Crowds Importance",
                "attractions_importance": "Attractions Importance",
                "trip_type": "Trip Type",
                "adventure": "Adventure",
                "relaxation": "Relaxation",
                "cultural": "Cultural",
                "current_location": "Your Current Location (Optional, for directions)",
                "destination_city": "Destination City",
                "pit_stops": "🚏 Add Pit Stops",
                "pit_stops_desc": "Add up to 3 stops along your journey to explore more destinations!",
                "current_stops": "Current Stops:",
                "no_stops": "No stops added yet",
                "add_stop": "➕ Add Stop",
                "reset_stops": "Reset Stops",
                "plan_trip": "Plan My Trip",
                "top_picks": "🏙️ Top Picks",
                "pit_stops_tab": "🛑 Pit Stops",
                "itinerary": "🗓️ Itinerary",
                "explore_nearby": "🏞️ Explore Nearby",
                "top_recommendations": "Top Recommendations",
                "weather_in": "Weather in",
                "recommendations_travel_time": "Recommendations sorted by travel time from your location.",
                "recommendations_score": "Recommendations sorted by overall score.",
                "get_directions": "🚗 Get Directions with All Stops",
                "pit_stop_recommendations": "Pit Stop Recommendations",
                "get_directions_to": "🚗 Get Directions to",
                "personalized_itinerary": "Your Personalized Itinerary",
                "number_of_days": "Number of Days",
                "download_itinerary": "📄 Download Itinerary as PDF",
                "no_itinerary": "Could not generate an itinerary. Please try with different preferences.",
                "enter_destination": "Enter a destination and click 'Plan My Trip' to generate an itinerary.",
                "explore_nearby_attractions": "Explore Nearby Attractions",
                "number_of_places": "Number of places to show",
                "detailed_list": "Detailed List of Nearby Places",
                "footer_text": "Plan your perfect trip with real-time insights!",
                "place": "Place",
                "category": "Category",
                "best_time": "Best Time",
                "travel_time": "Travel Time",
                "rating": "Rating",
                "day": "Day",
                "users": "Users"
            }
            # We would add other languages here, but for brevity I'll keep just English
            # For a real implementation, use a proper translation service or files
        }
        
        # Add basic translations for other languages - in a real app, these would be complete
        for lang_code in LANGUAGES.values():
            if lang_code != "en" and lang_code not in translations:
                translations[lang_code] = translations["en"].copy()
        
        return translations

    # Translation function
    def translate_text(text_key, lang_code="en"):
        translations = load_translations()
        if lang_code in translations and text_key in translations[lang_code]:
            return translations[lang_code][text_key]
        return translations["en"].get(text_key, text_key)

    # Load environment variables
    try:
        OPENWEATHER_API_KEY = os.environ["OPENWEATHER_API_KEY"]
        GOOGLE_MAPS_API_KEY = os.environ["GOOGLE_MAPS_API_KEY"]
    except KeyError:
        st.error("API keys not found. Please set OPENWEATHER_API_KEY and GOOGLE_MAPS_API_KEY in Streamlit secrets.")
        st.stop()

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

    # Generate PDF with dark theme
    def generate_itinerary_pdf(itinerary, destination, num_days, pit_stops=None):
        try:
            # Create a file-like buffer to receive PDF data
            buffer = io.BytesIO()
            
            # Create the PDF object using ReportLab
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            
            # Container for the 'Flowable' objects
            elements = []
            
            # Define styles
            styles = getSampleStyleSheet()
            title_style = styles['Heading1']
            title_style.textColor = colors.whitesmoke
            subtitle_style = styles['Heading2']
            subtitle_style.textColor = colors.lightblue
            normal_style = styles['Normal']
            normal_style.textColor = colors.whitesmoke
            
            # Add title
            elements.append(Paragraph(f"Travel Itinerary for {destination}", title_style))
            elements.append(Spacer(1, 0.25*inch))
            elements.append(Paragraph(f"Duration: {num_days} days", subtitle_style))
            elements.append(Spacer(1, 0.25*inch))
            
            # Add pit stops if available
            if pit_stops and any(pit_stops):
                pit_stop_text = "Pit Stops: " + ", ".join([ps for ps in pit_stops if ps])
                elements.append(Paragraph(pit_stop_text, normal_style))
                elements.append(Spacer(1, 0.25*inch))
            
            # Group by day
            days = {}
            for item in itinerary:
                day = item['Day']
                if day not in days:
                    days[day] = []
                days[day].append(item)
            
            # Process each day
            for day in sorted(days.keys()):
                elements.append(Paragraph(day, subtitle_style))
                elements.append(Spacer(1, 0.15*inch))
                
                # Create a table for this day's activities
                day_items = days[day]
                table_data = [["Place", "Category", "Best Time", "Travel Time", "Rating"]]
                
                for item in day_items:
                    table_data.append([
                        item['Place'],
                        item['Category'],
                        item['Best Time'],
                        item['Travel Time'],
                        str(item['Rating'])
                    ])
                
                # Create the table
                table = Table(table_data, colWidths=[2.5*inch, 1*inch, 1*inch, 1*inch, 0.7*inch])
                
                # Add dark theme style to the table
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.darkslategray),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.whitesmoke),
                    ('GRID', (0, 0), (-1, -1), 1, colors.darkgrey)
                ]))
                
                elements.append(table)
                elements.append(Spacer(1, 0.25*inch))
            
            # Build the PDF
            doc.build(elements)
            
            # Get the value of the BytesIO buffer
            pdf_data = buffer.getvalue()
            buffer.close()
            
            logger.info("PDF generation with ReportLab completed successfully")
            return pdf_data
            
        except Exception as e:
            logger.error(f"ReportLab PDF generation failed: {str(e)}")
            return None

    # Create a route with multiple stops
    def create_route_with_stops(origin, destination, stops):
        # Filter out empty stops
        valid_stops = [stop for stop in stops if stop]
        
        if not valid_stops:
            return f"https://www.google.com/maps/dir/?api=1&origin={origin}&destination={destination}"
        
        # Format waypoints for Google Maps URL
        waypoints = "|".join(valid_stops)
        return f"https://www.google.com/maps/dir/?api=1&origin={origin}&destination={destination}&waypoints={waypoints}"

    # Set dark theme for the app
    def set_dark_theme():
        # Dark theme CSS
        st.markdown("""
        <style>
        /* Main page background */
        .main {
            background-color: #121212;
            color: #e0e0e0;
        }
        
        /* Sidebar background */
        .sidebar-content {
            background-color: #1e1e1e;
            color: #e0e0e0;
        }
        
        /* Headers */
        h1, h2, h3, h4, h5, h6 {
            color: #e0e0e0 !important;
        }
        
        /* Text */
        p, li, ol, div {
            color: #e0e0e0;
        }
        
        /* Sliders */
        .stSlider > div > div {
            background-color: #3a3a3a !important;
        }
        
        /* Text inputs */
        .stTextInput > div > div > input {
            background-color: #2d2d2d;
            color: #e0e0e0;
            border-color: #444;
        }
        
        /* Buttons */
        .stButton > button {
            background-color: #3d5a80;
            color: white;
            border: none;
            transition: background-color 0.3s ease;
        }
        .stButton > button:hover {
            background-color: #4e70a6;
        }
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            background-color: #1e1e1e;
            border-bottom: 1px solid #333;
        }
        .stTabs [data-baseweb="tab"] {
            color: #e0e0e0;
        }
        .stTabs [aria-selected="true"] {
            background-color: #3d5a80 !important;
            color: white !important;
        }
        
        /* Select boxes */
        .stSelectbox > div > div {
            background-color: #2d2d2d;
            color: #e0e0e0;
        }
        
        /* Expander */
        .streamlit-expanderHeader {
            background-color: #2d2d2d !important;
            color: #e0e0e0 !important;
        }
        
        /* Data editor */
        .stDataFrame {
            background-color: #2d2d2d;
        }
        
        /* Cards styling */
        .recommendation-card {
            background-color: #2d2d2d !important;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            margin-bottom: 15px;
            padding: 15px;
            transition: transform 0.3s, box-shadow 0.3s;
        }
        .recommendation-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 15px rgba(0, 0, 0, 0.4);
        }
        .place-name {
            font-size: 18px;
            font-weight: bold;
            color: #e0e0e0 !important;
            margin-bottom: 8px;
        }
        .place-info {
            display: flex;
            justify-content: space-between;
            color: #a0a0a0;
        }
        .place-rating {
            color: #ffd700;
            font-weight: bold;
        }
        .place-time {
            color: #64b5f6;
        }
        .place-category {
            color: #b388ff;
        }
        </style>
        """, unsafe_allow_html=True)

    # Streamlit App
    def main():
        # Apply dark theme
        set_dark_theme()
        
        # Session state for language
        if "language" not in st.session_state:
            st.session_state.language = "English"
            st.session_state.lang_code = "en"
            
        # Language selector in top right
        lang = st.sidebar.selectbox(
            "🌐 Language / भाषा", 
            list(LANGUAGES.keys()),
            index=list(LANGUAGES.keys()).index(st.session_state.language)
        )
        
        # Update language if changed
        if lang != st.session_state.language:
            st.session_state.language = lang
            st.session_state.lang_code = LANGUAGES[lang]
            st.rerun()
            
        # Get language code
        lang_code = st.session_state.lang_code
        
        # Translate function shorthand
        def t(key):
            return translate_text(key, lang_code)

        st.markdown(f"<h1 style='text-align: center; color: #64b5f6;'>{t('app_title')}</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; color: #a0a0a0;'>{t('app_subtitle')}</p>", unsafe_allow_html=True)

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
            st.session_state.pit_stops = ["", "", ""]
            st.session_state.pit_stop_count = 0
            st.session_state.pit_stop_data = {}

        # Sidebar for preferences
        st.sidebar.header(t("your_preferences"))
        weather_importance = st.sidebar.slider(t("weather_importance"), 0.0, 1.0, 0.3)
        crowd_importance = st.sidebar.slider(t("avoid_crowds"), 0.0, 1.0, 0.3)
        attractions_importance = st.sidebar.slider(t("attractions_importance"), 0.0, 1.0, 0.2)
        trip_type = st.sidebar.selectbox(t("trip_type"), [t("adventure"), t("relaxation"), t("cultural")])
        user_preferences = {
            "weather_importance": weather_importance,
            "crowd_importance": crowd_importance,
            "attractions_importance": attractions_importance,
            "trip_type": trip_type
        }

        # Weather-based travel tips based on destination weather
        if st.session_state.weather_data:
            weather = st.session_state.weather_data
            st.sidebar.markdown("---")
            st.sidebar.subheader("📌 Travel Tips")
            temp = weather["temp"]
            condition = weather["condition"]
            
            if "rain" in condition:
                st.sidebar.info("☔ Rainy weather detected! Pack an umbrella and waterproof clothing.")
            elif "clear" in condition or "sunny" in condition:
                if temp > 30:
                    st.sidebar.info("🌡️ Hot weather detected! Stay hydrated and carry sunscreen.")
                else:
                    st.sidebar.info("☀️ Perfect weather for outdoor activities! Enjoy your adventure.")
            elif "snow" in condition:
                st.sidebar.info("❄️ Snowy conditions detected! Pack warm clothes and check road conditions.")
            elif "cloud" in condition:
                st.sidebar.info("☁️ Cloudy weather is good for sightseeing without harsh sunlight.")

        # Input section
        col1, col2 = st.columns(2)
        with col1:
            user_location = st.text_input(t("current_location"), "")
        with col2:
            destination = st.text_input(t("destination_city"), st.session_state.destination)
        
        # Pit Stops Section
        st.markdown("<div style='background-color: #2d2d2d; padding: 15px; border-radius: 10px; margin-top: 10px;'>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='color: #64b5f6;'>{t('pit_stops')}</h3>", unsafe_allow_html=True)
        st.markdown(f"<p>{t('pit_stops_desc')}</p>", unsafe_allow_html=True)
        
        # Display existing pit stops and add button
        col1, col2 = st.columns([3, 1])
        with col1:
            pit_stops_display = ", ".join([ps for ps in st.session_state.pit_stops if ps])
            if pit_stops_display:
                st.markdown(f"<p><b>{t('current_stops')}</b> {pit_stops_display}</p>", unsafe_allow_html=True)
            else:
                st.markdown(f"<p><i>{t('no_stops')}</i></p>", unsafe_allow_html=True)
        with col2:
            if st.session_state.pit_stop_count < 3 and st.button(t("add_stop"), key="add_stop_btn"):
                st.session_state.pit_stop_count += 1
                st.rerun()
        
        # Show input fields for pit stops
        for i in range(st.session_state.pit_stop_count):
            st.session_state.pit_stops[i] = st.text_input(f"Pit Stop {i+1}", st.session_state.pit_stops[i], key=f"stop_{i}")
        
        if st.session_state.pit_stop_count > 0 and st.button(t("reset_stops"), key="reset_stops"):
            st.session_state.pit_stops = ["", "", ""]
            st.session_state.pit_stop_count = 0
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Plan trip button
        if st.button(t("plan_trip"), key="plan_trip_btn", type="primary"):
            if not destination:
                st.error("Please enter a destination city.")
                return
                
            with st.spinner("Planning your trip..."):
                st.session_state.destination = destination
                
                # Get coordinates
                lat, lng = get_coordinates(destination)
                st.session_state.lat, st.session_state.lng = lat, lng
                
                if user_location:
                    user_lat, user_lng = get_user_coordinates(user_location)
                    st.session_state.user_lat, st.session_state.user_lng = user_lat, user_lng
                else:
                    st.session_state.user_lat, st.session_state.user_lng = lat, lng
                
                if not lat or not lng:
                    st.error(f"Could not find coordinates for {destination}. Please try a different city.")
                    return
                
                # Get weather data
                weather_data = get_weather_data_cached(destination)
                st.session_state.weather_data = weather_data
                
                # Get nearby places
                nearby_places = get_nearby_places_cached(lat, lng)
                st.session_state.nearby_places = nearby_places
                
                # Get traffic data
                traffic_data = get_traffic_data_for_places_cached(
                    st.session_state.user_lat, st.session_state.user_lng, nearby_places
                )
                
                # Get recommendations
                recommendations = recommend_places(
                    nearby_places, traffic_data, weather_data["quality"], user_preferences
                )
                recommendations_by_time = recommend_places(
                    nearby_places, traffic_data, weather_data["quality"], user_preferences, sort_by_travel_time=True
                )
                
                st.session_state.recommendations = recommendations
                st.session_state.recommendations_by_time = recommendations_by_time
                
                # Process pit stops if provided
                if any(st.session_state.pit_stops):
                    st.session_state.pit_stop_data = {}
                    for stop in st.session_state.pit_stops:
                        if stop:
                            # Get coordinates for pit stop
                            stop_lat, stop_lng = get_coordinates(stop)
                            if stop_lat and stop_lng:
                                # Get nearby places for pit stop
                                stop_places = get_nearby_places_cached(stop_lat, stop_lng)
                                
                                # Get traffic data for pit stop
                                stop_traffic = get_traffic_data_for_places_cached(
                                    st.session_state.user_lat, st.session_state.user_lng, stop_places
                                )
                                
                                # Get recommendations for pit stop
                                stop_recommendations = recommend_places(
                                    stop_places, stop_traffic, weather_data["quality"], user_preferences
                                )[:3]
                                
                                st.session_state.pit_stop_data[stop] = stop_recommendations

        # Tabs for different views
        if st.session_state.recommendations:
            tab1, tab2, tab3, tab4 = st.tabs([t("top_picks"), t("pit_stops_tab"), t("itinerary"), t("explore_nearby")])
            
            with tab1:
                st.subheader(t("top_recommendations"))
                weather = st.session_state.weather_data
                
                # Display weather information
                st.info(f"🌡️ {t('weather_in')} {st.session_state.destination}: {weather['temp']}°C, {weather['condition'].capitalize()}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"#### {t('recommendations_travel_time')}")
                    for i, place in enumerate(st.session_state.recommendations_by_time[:st.session_state.num_places_to_show]):
                        with st.container():
                            st.markdown(f"""
                            <div class="recommendation-card">
                                <div class="place-name">{i+1}. {place['Place']}</div>
                                <div class="place-info">
                                    <span class="place-rating">⭐ {place['Rating']}</span>
                                    <span class="place-time">🕒 {place['Travel Time']} mins</span>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"#### {t('recommendations_score')}")
                    for i, place in enumerate(st.session_state.recommendations[:st.session_state.num_places_to_show]):
                        with st.container():
                            st.markdown(f"""
                            <div class="recommendation-card">
                                <div class="place-name">{i+1}. {place['Place']}</div>
                                <div class="place-info">
                                    <span class="place-rating">⭐ {place['Rating']}</span>
                                    <span class="place-score">📊 {place['Score']:.1f}</span>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                
                # Map for top recommendations
                if st.session_state.lat and st.session_state.lng:
                    st.subheader("🗺️ Map View")
                    m = folium.Map(location=[st.session_state.lat, st.session_state.lng], zoom_start=12)
                    
                    # Add destination marker
                    folium.Marker(
                        [st.session_state.lat, st.session_state.lng],
                        popup=st.session_state.destination,
                        icon=folium.Icon(color="red", icon="info-sign")
                    ).add_to(m)
                    
                    # Add user location marker if provided
                    if st.session_state.user_lat and st.session_state.user_lng and user_location:
                        folium.Marker(
                            [st.session_state.user_lat, st.session_state.user_lng],
                            popup="Your Location",
                            icon=folium.Icon(color="green", icon="home")
                        ).add_to(m)
                    
                    # Add recommended places markers
                    for i, place in enumerate(st.session_state.recommendations[:st.session_state.num_places_to_show]):
                        folium.Marker(
                            [place["lat"], place["lng"]],
                            popup=f"{place['Place']} - ⭐ {place['Rating']} - 🕒 {place['Travel Time']} mins",
                            icon=folium.Icon(color="blue", icon="map-marker")
                        ).add_to(m)
                    
                    # Display the map
                    st_folium(m, width=700, height=500)
                    
                    # Get directions button
                    if user_location:
                        if st.button(t("get_directions"), key="get_directions"):
                            route_url = create_route_with_stops(
                                user_location, 
                                st.session_state.destination,
                                st.session_state.pit_stops
                            )
                            st.markdown(f"[Open Google Maps Directions]({route_url})")
            
            with tab2:
                st.subheader(t("pit_stop_recommendations"))
                
                if not any(st.session_state.pit_stops) or not st.session_state.pit_stop_data:
                    st.info("Add pit stops to see recommendations for stops along your journey.")
                else:
                    for stop, recommendations in st.session_state.pit_stop_data.items():
                        with st.expander(f"🛑 {stop}"):
                            for i, place in enumerate(recommendations):
                                with st.container():
                                    st.markdown(f"""
                                    <div class="recommendation-card">
                                        <div class="place-name">{i+1}. {place['Place']}</div>
                                        <div class="place-info">
                                            <span class="place-rating">⭐ {place['Rating']}</span>
                                            <span class="place-time">🕒 {place['Travel Time']} mins</span>
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                            
                            if user_location:
                                if st.button(f"{t('get_directions_to')} {stop}", key=f"dir_{stop}"):
                                    route_url = f"https://www.google.com/maps/dir/?api=1&origin={user_location}&destination={stop}"
                                    st.markdown(f"[Open Google Maps Directions]({route_url})")
            
            with tab3:
                st.subheader(t("personalized_itinerary"))

                # Select number of days
                num_days = st.slider(t("number_of_days"), 1, 5, 3)
                
                # Generate itinerary
                itinerary = generate_itinerary(
                    st.session_state.recommendations[:20], 
                    st.session_state.weather_data,
                    user_preferences,
                    num_days
                )
                
                if not itinerary:
                    st.warning(t("no_itinerary"))
                else:
                    # Display itinerary
                    days = {}
                    for item in itinerary:
                        day = item['Day']
                        if day not in days:
                            days[day] = []
                        days[day].append(item)
                    
                    for day, items in days.items():
                        with st.expander(day, expanded=True):
                            for item in items:
                                with st.container():
                                    st.markdown(f"""
                                    <div class="recommendation-card">
                                        <div class="place-name">{item['Place']}</div>
                                        <div class="place-info">
                                            <span class="place-category">🏛️ {item['Category']}</span>
                                            <span class="place-time">⏰ {item['Best Time']}</span>
                                            <span class="place-traffic">{item['Traffic']} {item['Travel Time']}</span>
                                            <span class="place-rating">⭐ {item['Rating']}</span>
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                    
                    # Map for itinerary
                    if st.session_state.lat and st.session_state.lng:
                        st.subheader("🗺️ Itinerary Map")
                        m = folium.Map(location=[st.session_state.lat, st.session_state.lng], zoom_start=12)
                        
                        # Add destination marker
                        folium.Marker(
                            [st.session_state.lat, st.session_state.lng],
                            popup=st.session_state.destination,
                            icon=folium.Icon(color="red", icon="info-sign")
                        ).add_to(m)
                        
                        # Color by day
                        day_colors = ["blue", "green", "purple", "orange", "darkpurple"]
                        
                        # Add itinerary places markers
                        for item in itinerary:
                            day_num = int(item['Day'].split()[-1]) - 1
                            color = day_colors[day_num % len(day_colors)]
                            folium.Marker(
                                [item["lat"], item["lng"]],
                                popup=f"{item['Place']} - {item['Day']} - {item['Best Time']}",
                                icon=folium.Icon(color=color)
                            ).add_to(m)
                        
                        # Display the map
                        st_folium(m, width=700, height=500)
                    
                    # Download itinerary PDF button
                    if st.button(t("download_itinerary"), key="download_itinerary"):
                        pdf_data = generate_itinerary_pdf(
                            itinerary, 
                            st.session_state.destination, 
                            num_days,
                            st.session_state.pit_stops
                        )
                        if pdf_data:
                            st.download_button(
                                label="📥 Download PDF",
                                data=pdf_data,
                                file_name=f"itinerary_{st.session_state.destination}.pdf",
                                mime="application/pdf",
                            )
                        else:
                            st.error("Error generating PDF. Please try again.")
            
            with tab4:
                st.subheader(t("explore_nearby_attractions"))
                
                # Slider for number of places to show
                num_places = st.slider(
                    t("number_of_places"), 
                    5, 20, 
                    st.session_state.num_places_to_show, 
                    key="places_slider"
                )
                st.session_state.num_places_to_show = num_places
                
                # Map for all places
                if st.session_state.lat and st.session_state.lng and st.session_state.nearby_places:
                    m = folium.Map(location=[st.session_state.lat, st.session_state.lng], zoom_start=13)
                    
                    # Add destination marker
                    folium.Marker(
                        [st.session_state.lat, st.session_state.lng],
                        popup=st.session_state.destination,
                        icon=folium.Icon(color="red", icon="info-sign")
                    ).add_to(m)
                    
                    # Add all places markers
                    for place in st.session_state.nearby_places[:num_places]:
                        folium.Marker(
                            [place["lat"], place["lng"]],
                            popup=f"{place['name']} - ⭐ {place['rating']}",
                            icon=folium.Icon(color="blue")
                        ).add_to(m)
                    
                    # Display the map
                    st_folium(m, width=700, height=500)
                    
                    # Detailed list
                    st.subheader(t("detailed_list"))
                    place_data = []
                    for place in st.session_state.nearby_places[:num_places]:
                        place_type = ", ".join(place["types"][:2]) if place["types"] else "Unknown"
                        place_data.append({
                            t("place"): place["name"],
                            t("category"): place_type,
                            t("rating"): place["rating"]
                        })
                    
                    # Show as a dataframe
                    if place_data:
                        df = pd.DataFrame(place_data)
                        st.dataframe(df, use_container_width=True)
        
        else:
            st.info(t("enter_destination"))
            
        # Footer
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown(
                f"<p style='text-align: center; color: #a0a0a0;'>{t('footer_text')}</p>", 
                unsafe_allow_html=True
            )
            st.markdown(
                "<p style='text-align: center; color: #a0a0a0;'>© 2024 WanderWise Travel</p>", 
                unsafe_allow_html=True
            )
            # Simulated user count - could be replaced with real analytics
            user_count = 15783  # Simulated number
            st.markdown(
                f"<p style='text-align: center; color: #64b5f6;'>🧳 {user_count} {t('users')} {t('app_title')}</p>", 
                unsafe_allow_html=True
            )

    if __name__ == "__main__":
        main()

    
# ------------- EXPLORE NEARBY PAGE -------------------
elif page == "🔍 Neighborhood Navigator":
    st.markdown("<h1 class='main-header'>🗺️ Explore Nearby Places</h1>", unsafe_allow_html=True)
    
    base_city = st.selectbox("Select your base location:", list(city_data.keys()))
    city_info = city_data[base_city]
    
    st.markdown(f"""
    <div style="background: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.7)), 
                url('https://via.placeholder.com/1200x400.png?text={base_city}'); 
                background-size: cover; color: white; padding: 2rem; border-radius: 10px; margin-bottom: 2rem;">
        <h2>{base_city}</h2>
        <p>{city_info['significance']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Map view
    st.subheader("Interactive Map View")
    
    lat, lng = city_info["coordinates"]["lat"], city_info["coordinates"]["lng"]
    
    # Google Maps Embed with nearby places
    st.markdown(f"""
    <iframe width="100%" height="450" style="border:0; border-radius: 10px;" 
    loading="lazy" allowfullscreen referrerpolicy="no-referrer-when-downgrade"
    src="https://www.google.com/maps/embed/v1/search?key={GOOGLE_MAPS_API_KEY}&q=must+visit+tourist+attractions+near+{base_city}&center={lat},{lng}&zoom=11">
    </iframe>""", unsafe_allow_html=True)
    
    # Nearby cities section
    st.markdown("<h2 class='sub-header'>🚗 Day Trips From Here</h2>", unsafe_allow_html=True)
    
    nearby_cols = st.columns(len(city_info["nearby_cities"]))
    
    for i, nearby_city in enumerate(city_info["nearby_cities"]):
        if nearby_city in city_data:
            with nearby_cols[i]:
                nearby_info = city_data[nearby_city]
                image_base64 = get_image_base64(f"images/{nearby_city.lower().replace(' ', '_')}.jpg")

# HTML with Base64 embedded image
                st.markdown(f"""
                <div style="background-color: #1E1E1E; padding: 1.2rem; border-radius: 8px;
                margin-bottom: 1.5rem; box-shadow: 0 4px 8px rgba(0,0,0,0.3);
                border-left: 4px solid #9575CD;">
                <img src="data:image/jpeg;base64,{image_base64}" width="100%" style="border-radius: 8px; margin-bottom: 10px;">
                <h3 style="color: #FFFFFF; margin-top: 0;">{nearby_city}</h3>
                <p style="font-size: 0.9rem; color: #E0E0E0;">{nearby_info['significance'][:80]}...</p>
                <p style="font-size: 0.8rem; color: #E0E0E0;"><strong>Top attraction:</strong> {nearby_info['attractions'][0]['name']}</p>
                </div>
                """, unsafe_allow_html=True)

    st.subheader("Travel Tips for " + base_city)
            
            # Local transportation
    st.markdown("""
            <div style='background-color:rgb(40, 38, 40); padding: 1rem; border-radius: 8px; margin-bottom: 1rem;border-left: 4px solid rgb(244, 135, 11);'>
                <h4>🚕 Local Transportation</h4>
                <ul>
                    <li>Auto-rickshaws are common for short distances</li>
                    <li>App-based cabs like Uber and Ola are widely available</li>
                    <li>Public buses are economical but can be crowded</li>
                    <li>Consider renting a scooter for flexibility (international license may be required)</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            # Food recommendations
    st.markdown(f"""
            <div style='background-color: rgb(40, 38, 40); padding: 1rem; border-radius: 8px; margin-bottom: 1rem;border-left: 4px solid rgb(144, 243, 14);'>
                <h4>🍽️ Local Cuisine</h4>
                <p>Must-try dishes in {base_city}:</p>
                <ul>
                    {"".join([f"<li>{dish}</li>" for dish in city_data[base_city]["local_dishes"]])}
                </ul>
                <p>Look for restaurants with good reviews and local crowds for authentic experiences.</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Safety tips
    st.markdown("""
            <div style='background-color:rgb(40, 38, 40); padding: 1rem; border-radius: 8px;border-left: 4px solid rgb(73, 37, 163);'>
                <h4>🛡️ Safety Tips</h4>
                <ul>
                    <li>Keep a digital copy of important documents</li>
                    <li>Stay hydrated and protect yourself from the sun</li>
                    <li>Be careful with street food and always drink bottled water</li>
                    <li>Use reputable ATMs in public places for cash withdrawals</li>
                    <li>Keep emergency contacts saved in your phone</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
    
    # Local experiences section
    st.markdown("<h2 class='sub-header' style='color: white;'>🌟 Unique Local Experiences</h2>", unsafe_allow_html=True)

    
    experiences = [
        {"name": "Cooking Class", "description": "Learn to cook traditional local dishes with an expert chef."},
        {"name": "Heritage Walk", "description": "Guided walk through historic parts of the city with a local historian."},
        {"name": "Artisan Workshop", "description": "Visit local artisans and learn traditional crafts like pottery or weaving."},
        {"name": "Night Food Tour", "description": "Explore the best street food spots that come alive after dark."}
    ]
    
    experience_cols = st.columns(2)
    for i, exp in enumerate(experiences):
        with experience_cols[i % 2]:
          st.markdown(f"""
<div style="background-color: #1E1E1E; padding: 1.2rem; border-radius: 8px;
            margin-bottom: 1.5rem; box-shadow: 0 4px 8px rgba(0,0,0,0.3);
            border-left: 4px solid #9575CD;">
    <h4 style="color: #FFFFFF; margin-top: 0;">{exp['name']}</h4>
    <p style="color: #E0E0E0; margin-bottom: 1.2rem;">{exp['description']}</p>
    <button style="background-color: #9575CD; color: white;
                 border: none; padding: 0.5rem 1.2rem; border-radius: 4px;
                 cursor: pointer; font-weight: 500; transition: all 0.3s ease;">
        Book Experience
    </button>
</div>
""", unsafe_allow_html=True)

        def get_category_color(category):
            category_colors = {
        "Historical": "#4E9BF5",  # Blue
        "Nature": "#4CAF50",      # Green
        "Shopping": "#E57373",    # Pink/Red
        "Religious": "#9575CD"    # Purple
    }
            return category_colors.get(category, "#4E9BF5")  # Default to blue if category not found


    
# ------------- TRIP IDEAS PAGE -------------------
elif page == "💡 Trip Ideas":
    st.markdown("<h1 class='main-header'>💡 Trip Ideas & Itineraries</h1>", unsafe_allow_html=True)
    
    # Featured itineraries
    st.markdown("<h2 class='sub-header'>Featured Itineraries</h2>", unsafe_allow_html=True)
    
    itineraries = [
        {
            "title": "South India Cultural Tour",
            "duration": "7 days",
            "cities": ["Chennai", "Mysuru", "Bengaluru"],
            "description": "Experience the rich cultural heritage of South India through its temples, palaces, and vibrant traditions.",
            "highlight": "Mysore Palace light show"
        },
        {
            "title": "Coastal Getaway",
            "duration": "5 days",
            "cities": ["Chennai", "Pondicherry"],
            "description": "Relax on beautiful beaches and explore charming coastal towns with French colonial influence.",
            "highlight": "Sunrise at Promenade Beach in Pondicherry"
        },
        {
            "title": "Weekend City Break",
            "duration": "3 days",
            "cities": ["Bengaluru"],
            "description": "Explore the Garden City with its parks, microbreweries, and vibrant tech culture.",
            "highlight": "Bangalore Palace tour"
        }
    ]
    
    for itin in itineraries:
        st.markdown(f"""
        <div style="background-color: #1E1E1E; padding: 1.5rem; border-radius: 10px;
               margin-bottom: 1rem;border-left: 4px solid rgb(34, 186, 138);">
        <h3>{itin['title']}</h3>
        <p style="font-size: 0.9rem;"><strong>Duration:</strong> {itin['duration']} | <strong>Cities:</strong> {', '.join(itin['cities'])}</p>
        <p>{itin['description']}</p>
        <p><strong>Highlight:</strong> {itin['highlight']}</p>
        <a href="https://drive.google.com/file/d/1gVm__uD85a1lvYdhcUToovOKrUdC-PZ-/view?usp=sharing" 
           style="background-color:rgb(34, 200, 169); color: white;
                  border: none; padding: 0.5rem 1rem; border-radius: 4px;
                  cursor: pointer; transition: all 0.3s ease;
                  text-decoration: none; display: inline-block;">
            View and Download Full Itinerary
        </a>
    </div>
    """, unsafe_allow_html=True)
    
    
    # Seasonal recommendations
    

    st.markdown("<h2 style='color: #FFFFFF; margin-bottom: 1rem;'>🌍 Seasonal Recommendations</h2>", unsafe_allow_html=True)

    current_month = datetime.now().strftime("%B")

    st.markdown(f"""
    <div style="background-color: #1E1E1E; padding: 1.5rem; border-radius: 10px;
                margin-bottom: 1.5rem; box-shadow: 0 4px 8px rgba(0,0,0,0.3);
                border-left: 4px solid rgb(198, 43, 136);">
        <h3 style="color: #FFFFFF; margin-top: 0;">Best Places to Visit in {current_month}</h3>
        <p style="color: #E0E0E0;">Our recommendations based on current weather, events, and traveler reviews.</p>
    </div>
    """, unsafe_allow_html=True)

# Generate seasonal recommendations based on current month
    current_month_num = datetime.now().month
    if 11 <= current_month_num <= 2:  # Winter
        recommendations = ["Mysuru", "Chennai", "Pondicherry"]
        reason = "pleasant temperatures and clear skies"
    elif 3 <= current_month_num <= 6:  # Summer
        recommendations = ["Bengaluru", "Mysuru"]
        reason = "relatively cooler temperatures compared to other parts of India"
    else:  # Monsoon and post-monsoon
        recommendations = ["Chennai", "Pondicherry", "Bengaluru"]
        reason = "post-monsoon greenery and cultural festivities"



    
    rec_cols = st.columns(len(recommendations))
    for i, city in enumerate(recommendations):
        with rec_cols[i]:
            if city in city_data:
                city_info = city_data[city]
                image_path = os.path.join("images", f"{city}.jpg")  # Construct the correct path
                image_base64 = get_image_base64(image_path)  # Convert to base64

                st.markdown(f"""
                <div style="background-color: #1E1E1E; padding: 1.2rem; border-radius: 8px;
                margin-bottom: 1.5rem; box-shadow: 0 4px 8px rgba(0,0,0,0.3);
                border-left: 4px solid #9575CD;">
                <img src="data:image/jpeg;base64,{image_base64}" width="100%" style="border-radius: 8px;">
                <h3 style="color: #FFFFFF;">{city}</h3>
                <p style="color: #E0E0E0;">Perfect this season for {reason}.</p>
                <p style="font-size: 0.8rem; color: #E0E0E0;">{city_info['info']}</p>
                </div>
                """, unsafe_allow_html=True)

    # Travel guides and resources
    st.markdown("<h2 class='sub-header'>Travel Guides & Resources</h2>", unsafe_allow_html=True)

    guide_cols = st.columns(2)

    guides = [
    {"title": "First-Time Visitor's Guide to South India", "type": "PDF Guide", 
     "link": "https://drive.google.com/file/d/1p03M0hbZOL7W5AlmF4IfVdGQOr26iUxb/view?usp=sharing"},
    {"title": "South Indian Cuisine: What to Try Where", "type": "Food Guide", 
     "link": "https://drive.google.com/file/d/1Zp3Lam2U0rjxZfw2pwqi5Oqd9o-knLro/view?usp=sharing"},
    {"title": "Navigating Public Transportation", "type": "Travel Tips", 
     "link": "https://drive.google.com/file/d/1HqpqoR7LISyQ2VMFuq09nzbK8ho9Ej0Q/view?usp=sharing"},
    {"title": "Cultural Etiquette in South India", "type": "Cultural Guide", 
     "link": "https://drive.google.com/file/d/1aabpGkCMOAVXx3mfDiqkTXJkYQO4ZO8a/view?usp=sharing"}
    ]

    for i, guide in enumerate(guides):
        with guide_cols[i % 2]:
            st.markdown(f"""
            <div style="display: flex; background-color:#1E1E1E; padding: 1rem;
                   border-radius: 8px; margin-bottom: 1rem; align-items: center;
                   box-shadow: 0 2px 4px rgba(0,0,0,0.1);border-left: 4px solid #1976D2;">
            <a href="{guide['link']}" style="display: flex; text-decoration: none; color: inherit; width: 100%;">
                <div style="background-color: #E3F2FD; color: #1976D2; padding: 1rem;
                           border-radius: 8px; margin-right: 1rem; font-size: 1.5rem;">
                    📚
                </div>
                <div>
                    <h4 style="margin: 0;">{guide['title']}</h4>
                    <p style="margin: 0.3rem 0 0 0; color: #666;">{guide['type']}</p>
                </div>
            </a>
            </div>
            """, unsafe_allow_html=True)


st.sidebar.markdown("""
<div style="margin-top: 2rem; padding: 1rem; border-top: 1px solid #eee;">
    <p style="font-size: 0.8rem; color: #666;">
        Wanderwise Travel Planner v2.0<br>
        &copy; 2025 NUTS co. All rights reserved.
    </p>
</div>
""", unsafe_allow_html=True)
