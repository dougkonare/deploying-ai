from langchain.tools import tool
import json
import requests
from dotenv import load_dotenv
import os
from IPython.display import display, Markdown


# _logs = get_logger(__name__)
load_dotenv("05_src/.env")
load_dotenv("05_src/.secrets")



WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')


@tool
def get_current_weather_data(location: str, date: str = None):
    """
    Fetches weather data for a given location and optional date from the Weatherstack API.
    If date is None, it fetches current weather data. If date is provided, it fetches historical weather data.
    """
    base_url = "https://api.apilayer.net/weatherstack/"
    endpoint = "current" if date is None else "historical"
    
    params = {
        "access_key": WEATHER_API_KEY,
        "query": location
    }
    
    if date:
        params["historical_date"] = date
    
    response = requests.get(f"{base_url}{endpoint}", params=params)
    
    if response.status_code != 200:
        raise Exception(f"Error fetching weather data: {response.status_code} - {response.text}")

    # resp_dict = json.loads(response.text)
    # weather_list = resp_dict.get("current", [])
    # weather = "\n".join([f"{i+1}. {fact}\n" for i, fact in enumerate(weather_list)])
    
    return json.dumps(response.text)

def get_weather_forecast(location: str, days: int = 1):
    """
    Fetches weather forecast data for a given location and number of days from the Weatherstack API.
    """
    base_url = "https://api.apilayer.net/weatherstack/forecast"
    
    params = {
        "access_key": WEATHER_API_KEY,
        "query": location,
        "forecast_days": days
    }
    
    response = requests.get(base_url, params=params)
    
    if response.status_code != 200:
        raise Exception(f"Error fetching weather forecast data: {response.status_code} - {response.text}")
    
    return json.loads(response.text)

# response = get_current_weather_data.invoke({"location": "Amsterdam"})
# # print(json.dumps(response, indent=4))
# print(response)

# forecast = get_weather_forecast("Bamako", days=5)
# print(json.dumps(forecast, indent=4))


# Current Weather
# https://api.apilayer.net/weatherstack/current?access_key=YOUR_ACCESS_KEY&query=New%20York
# // With optional parameters:
# https://api.apilayer.net/weatherstack/current?access_key=YOUR_ACCESS_KEY&query=New%20York&units=m&callback=MY_CALLBACK
# Historical Weather
# https://api.apilayer.net/weatherstack/historical?access_key=YOUR_ACCESS_KEY&query=New%20York&historical_date=2015-01-21
# // With optional parameters:
# https://api.apilayer.net/weatherstack/historical?access_key=YOUR_ACCESS_KEY&query=New%20York&historical_date=2015-01-21&hourly=1&interval=3&units=m&callback=MY_CALLBACK
# Historical Weather Time-Series
# https://api.apilayer.net/weatherstack/historical?access_key=YOUR_ACCESS_KEY&query=New%20York&historical_date_start=2015-10-21&historical_date_end=2015-10-25
# // With optional parameters:
# https://api.apilayer.net/weatherstack/historical?access_key=YOUR_ACCESS_KEY&query=New%20York&historical_date_start=2015-10-21&historical_date_end=2015-10-25&hourly=1&interval=3&units=m&callback=MY_CALLBACK
# Weather Forecast
# https://api.apilayer.net/weatherstack/forecast?access_key=YOUR_ACCESS_KEY&query=New%20York
# // With optional parameters:
# https://api.apilayer.net/weatherstack/forecast?access_key=YOUR_ACCESS_KEY&query=