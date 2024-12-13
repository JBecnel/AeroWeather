import os
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WeatherService:
    """Service for fetching weather data from NOAA Weather API"""
    
    def __init__(self):
        self.base_url = "https://api.weather.gov"
        self.headers = {
            'User-Agent': '(Aviation Analytics Platform, contact@aviation-analytics.com)',
            'Accept': 'application/geo+json'
        }
        self.cache = {}
        self.cache_duration = timedelta(minutes=30)
        logger.info("Initialized Weather Service using weather.gov API")
        
        # Default weather data when API fails
        self.default_weather = {
            'temperature': 68.0,  # Default temperature in Fahrenheit
            'feels_like': 65.0,
            'humidity': 50,
            'pressure': 1013.25,
            'wind_speed': 0,
            'wind_direction': 0,
            'visibility': 10,
            'cloud_coverage': 0,
            'weather_condition': 'Clear',
            'precipitation': 0,
            'timestamp': datetime.now().isoformat()
        }

    def _map_weather_condition(self, noaa_description: str) -> str:
        #Map NOAA weather descriptions to our standardized conditions"""
        try:
            if not noaa_description:
                logger.warning("Empty weather description received from NOAA API")
                return 'Clear'
                
            condition_mapping = {
                'CLEAR': 'Clear',
                'SUNNY': 'Clear',
                'FAIR': 'Clear',
                'MOSTLY CLEAR': 'Clear',
                'PARTLY CLOUDY': 'Clouds',
                'MOSTLY CLOUDY': 'Clouds',
                'CLOUDY': 'Clouds',
                'OVERCAST': 'Clouds',
                'RAIN': 'Rain',
                'LIGHT RAIN': 'Rain',
                'HEAVY RAIN': 'Rain',
                'DRIZZLE': 'Rain',
                'SHOWERS': 'Rain',
                'SNOW': 'Snow',
                'LIGHT SNOW': 'Snow',
                'HEAVY SNOW': 'Snow',
                'SNOW SHOWERS': 'Snow',
                'FOG': 'Fog',
                'MIST': 'Fog',
                'HAZE': 'Fog',
                'THUNDERSTORM': 'Thunderstorm',
                'THUNDERSTORMS': 'Thunderstorm',
                'T-STORM': 'Thunderstorm'
            }
            
            description_upper = str(noaa_description).upper()
            logger.debug(f"Mapping weather condition: {description_upper}")
            
            for key, value in condition_mapping.items():
                if key in description_upper:
                    logger.debug(f"Mapped {description_upper} to {value}")
                    return value
                    
            logger.warning(f"Unknown weather condition from NOAA: {noaa_description}")
            return 'Clear'  # Default to Clear if no matching condition found
            
        except Exception as e:
            logger.error(f"Error mapping weather condition: {str(e)}")
            return 'Clear'

    def get_weather(self, airport_code: str, airport_data: Dict, target_date: datetime = None) -> Dict:
        #Get weather data for an airport for a specific date (or current if not specified)"""
        try:
            # If no target date specified, use current time
            if target_date is None:
                target_date = datetime.now()
                
            # Check cache first
            cache_key = f"{airport_code}_{target_date.date().isoformat()}"
            if cache_key in self.cache:
                cache_entry = self.cache[cache_key]
                if datetime.now() - datetime.fromisoformat(cache_entry['timestamp']) < self.cache_duration:
                    logger.debug(f"Using cached weather data for {airport_code} on {target_date.date()}")
                    return cache_entry['data']

            # Construct API URL for points
            lat = airport_data['lat']
            lon = airport_data['lon']
            points_url = f"{self.base_url}/points/{lat},{lon}"
            
            # Get forecast and observation station URLs
            logger.debug(f"Fetching endpoints for {airport_code}")
            response = requests.get(points_url, headers=self.headers)
            response.raise_for_status()
            
            points_data = response.json()
            #forecast_url = points_data['properties']['forecast']
            observation_url = points_data['properties']['observationStations']
            
            # Get nearest observation station
            stations_response = requests.get(observation_url, headers=self.headers)
            stations_response.raise_for_status()
            
            # Get first station from the list
            station_url = stations_response.json()['features'][0]['id']
            
            # Get latest observation
            observation_response = requests.get(f"{station_url}/observations/latest", headers=self.headers)
            observation_response.raise_for_status()
            
            current_data = observation_response.json()
            #print(current_data)
            #import pickle
            #with open(airport_code + 'result.json', 'wb') as file:
            #    pickle.dump(current_data, file)
            properties = current_data['properties']
            #print(properties)
            #print()
            # Process weather data with enhanced error handling
            try:
                # Extract values from NWS API properties
                temp_value = properties.get('temperature', {}).get('value')
                feels_like_value = properties.get('windChill', {}).get('value')
                if feels_like_value is None:
                    feels_like_value = properties.get('heatIndex', {}).get('value')
                
               
                weather_data = {
                    'temperature': self._celsius_to_fahrenheit(temp_value),
                    'feels_like': self._celsius_to_fahrenheit(feels_like_value),
                    'humidity': properties.get('relativeHumidity', {}).get('value', 50),
                    'pressure': properties.get('barometricPressure', {}).get('value', 101325) / 100,
                    'wind_speed': self._ms_to_mph(properties.get('windSpeed', {}).get('value', 0)),
                    'wind_direction': properties.get('windDirection', {}).get('value', 0),
                    'visibility': self._m_to_miles(properties.get('visibility', {}).get('value', 10000)),
                    'cloud_coverage': self._parse_cloud_coverage(properties.get('layers', [])),
                    'weather_condition': self._map_weather_condition(properties.get('textDescription', 'Clear')),
                    'precipitation': properties.get('precipitationLastHour', {}).get('value', 0),
                    'timestamp': datetime.now().isoformat()
                }
                
                logger.debug(f"Processed weather data for {airport_code}: {weather_data}")
                
            except Exception as e:
                logger.error(f"Error processing weather data for {airport_code}: {str(e)}")
                logger.debug("Processing error details:", exc_info=True)
                return self.default_weather

            # Update cache
            self.cache[airport_code] = {
                'data': weather_data,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Successfully fetched weather data for {airport_code}")
            return weather_data

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching weather data for {airport_code}: {str(e)}")
            return self.default_weather
        except Exception as e:
            logger.error(f"Unexpected error fetching weather data for {airport_code}: {str(e)}")
            return self.default_weather

    def _parse_cloud_coverage(self, cloud_layers: List[Dict]) -> int:
        """Parse cloud coverage from NOAA cloud layers data"""
        try:
            if not cloud_layers:
                return 0
                
            coverage_values = {
                'CLR': 0,        # Clear
                'FEW': 25,       # Few clouds (1/8 - 2/8)
                'SCT': 50,       # Scattered clouds (3/8 - 4/8)
                'BKN': 75,       # Broken clouds (5/8 - 7/8)
                'OVC': 100,      # Overcast (8/8)
                'VV': 100        # Vertical Visibility (full coverage)
            }
            
            # Get the most severe cloud coverage
            max_coverage = 0
            for layer in cloud_layers:
                amount = layer.get('amount', 'CLR').upper()
                coverage = coverage_values.get(amount, 0)
                max_coverage = max(max_coverage, coverage)
            
            return max_coverage
            
        except Exception as e:
            logger.error(f"Error parsing cloud coverage: {str(e)}")
            return 0

    def _parse_precipitation(self, properties: Dict) -> float:
        """Parse precipitation data from NOAA properties"""
        try:
            # Try different precipitation fields
            precip_fields = [
                'precipitationLastHour',
                'precipitationLast3Hours',
                'precipitationLast6Hours'
            ]
            
            for field in precip_fields:
                value = properties.get(field, {}).get('value')
                if value is not None:
                    # Convert to hourly rate if needed
                    if field == 'precipitationLast3Hours':
                        value = value / 3
                    elif field == 'precipitationLast6Hours':
                        value = value / 6
                    return float(value)
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error parsing precipitation: {str(e)}")
            return 0.0

    def _celsius_to_fahrenheit(self, celsius_value: Optional[float]) -> float:
        """Convert Celsius temperature to Fahrenheit"""
        try:
            if celsius_value is not None:
                return (float(celsius_value) * 9/5) + 32
            return 68.0  # Default temperature (20°C) in Fahrenheit
        except (ValueError, TypeError):
            logger.warning("Invalid temperature value, using default")
            return 68.0

    def _ms_to_mph(self, ms_value: Optional[float]) -> float:
        """Convert meters per second to miles per hour"""
        try:
            if ms_value is not None:
                return float(ms_value) * 2.237  # 1 m/s = 2.237 mph
            return 0.0
        except (ValueError, TypeError):
            return 0.0

    def _m_to_miles(self, meters_value: Optional[float]) -> float:
        """Convert meters to miles"""
        try:
            if meters_value is not None:
                return float(meters_value) * 0.000621371  # 1 m = 0.000621371 miles
            return 10.0  # Default 10 miles visibility
        except (ValueError, TypeError):
            return 10.0

    def get_bulk_weather(self, airports: Dict[str, Dict], target_date: datetime = None) -> Dict[str, Dict]:
        """Get weather data for multiple airports for a specific date"""
        logger.info(f"Starting bulk weather data fetch for {len(airports)} airports")
        weather_data = {}

        for code, data in airports.items():
            try:
                logger.debug(f"Attempting to fetch weather for {code}")
                weather = self.get_weather(code, data, target_date)
                weather_data[code] = weather
                logger.debug(f"Successfully fetched weather for {code}")
            except Exception as e:
                logger.error(f"Error processing weather data for {code}: {str(e)}")
                logger.debug("Error details:", exc_info=True)
                weather_data[code] = self.default_weather

        if not weather_data:
            logger.error("Could not fetch weather data for any airport")
        else:
            logger.info(f"Successfully fetched weather data for {len(weather_data)} airports")

        return weather_data


# AIRPORT_COORDINATES = {
#     'SFO': {
#         'lat': 37.6213,
#         'lon': -122.3790
#     },  # San Francisco International Airport
#     'LAX': {
#         'lat': 33.9416,
#         'lon': -118.4085
#     },  # Los Angeles International Airport
#     'ORD': {
#         'lat': 41.9742,
#         'lon': -87.9073
#     },  # O'Hare International Airport
#     'DFW': {
#         'lat': 32.8998,
#         'lon': -97.0403
#     },  # Dallas/Fort Worth International Airport
#     'MIA': {
#         'lat': 25.7959,
#         'lon': -80.2870
#     }  # Miami International Airport
# }

AIRPORT_COORDINATES = {
    'SEA': {'lat': 47.4484, 'lon': -122.3790},  # Seattle International Airport
    'LAX': {'lat': 33.9416, 'lon': -118.4085},  # Los Angeles International Airport
    'LGA': {'lat': 40.7766, 'lon': -73.8742},   # LaGuarida (New York)
    'DFW': {'lat': 32.8998, 'lon': -97.0403},   # Dallas/Fort Worth International Airport
    'MIA': {'lat': 25.7959, 'lon': -80.2870}    # Miami International Airport
}

# Create a singleton instance
weather_service = WeatherService()