import streamlit as st
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

# Fetch your secrets securely from Streamlit's secrets manager
username = st.secrets["USERNAME"]
password = st.secrets["PASSWORD"]

# Mapping Weather Symbol IDs to Descriptions and Icons (using emojis as placeholders)
weather_symbol_map = {
    0: ("A weather symbol could not be determined", "❓"),
    1: ("Clear sky", "☀️"),
    101: ("Clear sky (night)", "🌕"),
    2: ("Light clouds", "🌤"),
    102: ("Light clouds (night)", "🌥"),
    3: ("Partly cloudy", "⛅"),
    103: ("Partly cloudy (night)", "☁️"),
    4: ("Cloudy", "☁️"),
    104: ("Cloudy (night)", "☁️"),
    5: ("Rain", "🌧"),
    105: ("Rain (night)", "🌧"),
    6: ("Rain and snow / sleet", "🌨"),
    106: ("Rain and snow / sleet (night)", "🌨"),
    7: ("Snow", "❄️"),
    107: ("Snow (night)", "❄️"),
    8: ("Rain shower", "🌦"),
    108: ("Rain shower (night)", "🌦"),
    9: ("Snow shower", "🌨"),
    109: ("Snow shower (night)", "🌨"),
    10: ("Sleet shower", "🌨"),
    110: ("Sleet shower (night)", "🌨"),
    11: ("Light fog", "🌫️"),
    111: ("Light fog (night)", "🌫️"),
    12: ("Dense fog", "🌫️"),
    112: ("Dense fog (night)", "🌫️"),
    13: ("Freezing rain", "🌧❄️"),
    113: ("Freezing rain (night)", "🌧❄️"),
    14: ("Thunderstorms", "⛈"),
    114: ("Thunderstorms (night)", "⛈"),
    15: ("Drizzle", "🌧"),
    115: ("Drizzle (night)", "🌧"),
    16: ("Sandstorm", "🌪️"),
    116: ("Sandstorm (night)", "🌪️")
}

# McDonough, GA coordinates
LATITUDE = '33.4473'
LONGITUDE = '-84.1469'

# RSS feed URLs
RSS_FEED_NHC = "https://www.nhc.noaa.gov/nhc_at1.xml"
RSS_FEED_SPC = "https://www.spc.noaa.gov/products/spcwwrss.xml"

# Function to fetch the first description from an RSS feed
def fetch_first_description_from_rss(url):
    try:
        response = requests.get(url)
        tree = ET.ElementTree(ET.fromstring(response.content))
        root = tree.getroot()

        for item in root.findall(".//item"):
            description = item.find("description")
            if description is not None:
                return description.text
        return "No description available."
    except Exception as e:
        return f"Error fetching data: {e}"

# Function to fetch weather data from Meteomatics API
def fetch_weather_data(latitude, longitude):
    params = {
        'temperature': f"t_2m:F/{latitude},{longitude}",
        'weather_symbol': f"weather_symbol_1h:idx/{latitude},{longitude}",
        'heavy_rain_warning': f"precip_1h:mm/{latitude},{longitude}",
        'air_quality': f"pm2p5:ugm3/{latitude},{longitude}",
    }

    weather_data = {}
    for param, endpoint in params.items():
        try:
            url = f"https://api.meteomatics.com/{datetime.utcnow().isoformat()}Z/{endpoint}/json"
            response = requests.get(url, auth=(username, password))
            response.raise_for_status()
            data = response.json()
            weather_data[param] = data['data'][0]['coordinates'][0]['dates'][0]['value']
        except requests.exceptions.HTTPError as http_err:
            weather_data[param] = f"Error fetching {param}: {http_err}"
        except Exception as err:
            weather_data[param] = f"Error fetching {param}: {err}"

    return weather_data

# Function to get the weather symbol description and icon
def get_weather_symbol_description(symbol_id):
    return weather_symbol_map.get(symbol_id, ("Unknown symbol", "❓"))

# Function to fetch 5-day weather forecast data from Meteomatics API
def fetch_5_day_forecast(latitude, longitude):
    forecast_data = []
    
    # Fetch forecast for the next 5 days in 24-hour intervals (daily forecast)
    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=5)
    interval = "PT24H"  # 24-hour interval (daily)

    params = {
        'temperature': f"t_2m:F/{latitude},{longitude}",
        'weather_symbol': f"weather_symbol_1h:idx/{latitude},{longitude}"
    }

    for param, endpoint in params.items():
        try:
            url = f"https://api.meteomatics.com/{start_date.isoformat()}Z--{end_date.isoformat()}Z:{interval}/{endpoint}/json"
            response = requests.get(url, auth=(username, password))
            response.raise_for_status()
            data = response.json()
            forecast_data.append(data['data'][0]['coordinates'][0]['dates'])
        except requests.exceptions.HTTPError as http_err:
            return f"Error fetching {param}: {http_err}"
        except Exception as err:
            return f"Error fetching {param}: {err}"

    return forecast_data

# Function to display the 5-day weather outlook in Streamlit
def display_5_day_forecast():
    st.header("5-Day Weather Outlook for McDonough, GA")
    
    # Fetch the 5-day forecast data
    forecast_data = fetch_5_day_forecast(LATITUDE, LONGITUDE)

    # Loop through each day's forecast and display
    for day in forecast_data[0]:  # Loop through temperature data
        date = day['date']
        temperature = day['value']
        symbol_id = int(forecast_data[1][forecast_data[0].index(day)]['value'])  # Get weather symbol for the same day
        symbol_description, symbol_icon = get_weather_symbol_description(symbol_id)

        # Display the weather for each day
        st.write(f"**Date**: {date}")
        st.write(f"**Temperature**: {temperature} °F")
        st.write(f"**Weather**: {symbol_icon} {symbol_description}")
        st.write("---")  # Line to separate each day's forecast

# Main function
def main():
    st.title("Tropics & Severe Weather Dashboard")

    st.title("NHC Latest")
    description_nhc = fetch_first_description_from_rss(RSS_FEED_NHC)
    description_with_emoji = f"🌀 {description_nhc}"
    st.markdown(
        f"""
        <div style="background-color: #FF0000; padding: 10px; margin-bottom: 6px;">
            <p style="color: white; text-align: center; text-transform: uppercase;">{description_with_emoji}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.title("SPC Alerts")
    description_spc = fetch_first_description_from_rss(RSS_FEED_SPC)
    description_spc_with_emoji = f"⛈️ {description_spc}"
    st.markdown(
        f"""
        <div style="background-color: #007BFF; padding: 10px; margin-bottom: 10px;">
            <p style="color: white; text-align: center; text-transform: uppercase;">{description_spc_with_emoji}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Fetch current weather data
    weather_data = fetch_weather_data(LATITUDE, LONGITUDE)
    st.header("Current Weather in McDonough, GA:")
    st.write(f"**Temperature**: {weather_data.get('temperature')} °F")

    try:
        weather_symbol_id = int(weather_data.get('weather_symbol', 0))  # default to 0 if missing
    except (TypeError, ValueError):
        weather_symbol_id = 0  # Fallback to default if conversion fails

    symbol_description, symbol_icon = get_weather_symbol_description(weather_symbol_id)
    st.write(f"**Weather Symbol**: {symbol_icon} {symbol_description}")
    st.write(f"**Heavy Rain Warning**: {weather_data.get('heavy_rain_warning')} mm")
    st.write(f"**Air Quality (PM2.5)**: {weather_data.get('air_quality')} µg/m³")

    # Display the 5-day forecast
    display_5_day_forecast()

if __name__ == "__main__":
    main()
