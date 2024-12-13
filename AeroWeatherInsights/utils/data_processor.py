import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from .weather_service import weather_service, AIRPORT_COORDINATES

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_sample_data():
    """
    Load stored data if available, otherwise generate sample data with graceful fallback
    """
    logger.info("Starting to load sample data")
    
    # Try to load stored data first
    try:
        from .data_collection import data_collector
        logger.info("Successfully imported data collector")
        
        try:
            logger.debug("Attempting to load stored data from database...")
            stored_data = data_collector.get_stored_data()
            
            if stored_data is not None and not stored_data.empty:
                logger.info(f"Successfully loaded {len(stored_data)} records from database")
                return stored_data
                
            logger.warning("No stored data available, will generate sample data")
            
        except Exception as e:
            logger.warning(f"Could not load stored data: {str(e)}")
            logger.debug("Database access error details:", exc_info=True)
            logger.info("Proceeding with sample data generation")
            
    except ImportError:
        logger.warning("Data collector not available, proceeding with sample data generation")
        
    # Generate sample data with default weather conditions if API fails
    logger.info("Generating sample data with default weather conditions")
    
    # # Use weather service with fallback to default values
    # try:
    #     weather_data = weather_service.get_bulk_weather(AIRPORT_COORDINATES)
    #     if not weather_data:
    #         logger.warning("Weather service unavailable, using default values")
    #         weather_data = {}
    # except Exception as e:
    #     logger.error(f"Error fetching weather data: {str(e)}")
    #     weather_data = {}
    
    # logger.info("Generating sample data as no stored data is available")
    # # Generate dates for the last 365 days
    # dates = [datetime.now() - timedelta(days=x) for x in range(365)]
    
    # # Sample data configuration
    # airlines = ['Delta', 'United', 'American', 'Southwest', 'JetBlue']
    # airports = list(AIRPORT_COORDINATES.keys())
    # weather_conditions = ['Clear', 'Rain', 'Snow', 'Fog', 'Thunderstorm']
    
    # # Create sample data
    # data = []
    # for date in dates:
    #     # Use real-time weather for current date, simulate for historical dates
    #     is_current_date = (datetime.now().date() == date.date())
        
    #     # Get weather data for each airport
    #     airport_weather = {
    #         airport: (
    #             weather_data.get(airport, {}) if is_current_date
    #             else {
    #                 'temperature': np.random.normal(
    #                     20 + (10 if airport in ['MIA', 'LAX'] else 0),
    #                     5
    #                 ),
    #                 'precipitation': np.random.beta(2, 5) if airport not in ['LAX', 'SFO'] else np.random.beta(1, 7),
    #                 'weather_condition': np.random.choice(
    #                     weather_conditions,
    #                     p=[0.6, 0.2, 0.1, 0.05, 0.05]
    #                 )
    #             }
    #         )
    #         for airport in airports
    #     }
        
    #     for airline in airlines:
    #         # Generate multiple flights per day per airline for each route
    #         for origin in airports:
    #             for destination in airports:
    #                 if origin != destination:
    #                     # More flights on popular routes
    #                     num_flights = np.random.poisson(5)
    #                     for _ in range(num_flights):
    #                         # Get weather condition and its severity multiplier
    #                         origin_weather = airport_weather[origin]
    #                         weather_condition = origin_weather.get('weather_condition', 'Clear')
    #                         weather_severity = {
    #                             'Clear': 1.0,
    #                             'Rain': 1.5,
    #                             'Snow': 2.5,
    #                             'Fog': 2.0,
    #                             'Thunderstorm': 3.0,
    #                             'Clouds': 1.2,
    #                             'Drizzle': 1.3,
    #                             'Mist': 1.8
    #                         }
                            
    #                         weather_multiplier = weather_severity.get(weather_condition, 1.0)
    #                         base_delay = np.random.normal(15, 10)
    #                         delay_minutes = max(0, base_delay * weather_multiplier)
                            
    #                         # Generate flight data
    #                         flight_data = {
    #                             'date': date.date(),
    #                             'airline': airline,
    #                             'origin': origin,
    #                             'destination': destination,
    #                             'delay_minutes': delay_minutes,
    #                             'temperature': origin_weather.get('temperature', np.random.normal(20, 5)),
    #                             'precipitation': origin_weather.get('precipitation', np.random.beta(2, 5)),
    #                             'weather_condition': weather_condition,
    #                             'weather_delay': delay_minutes > 30 and weather_multiplier > 1.0,
    #                             'wind_speed': origin_weather.get('wind_speed', np.random.uniform(0, 20)),
    #                             'wind_direction': origin_weather.get('wind_direction', np.random.randint(0, 360)),
    #                             'visibility': origin_weather.get('visibility', np.random.uniform(5, 15)),
    #                             'cloud_coverage': origin_weather.get('cloud_coverage', np.random.randint(0, 100)),
    #                             'humidity': origin_weather.get('humidity', np.random.randint(30, 90)),
    #                             'pressure': origin_weather.get('pressure', np.random.normal(1013, 5))
    #                         }
                            
    #                         data.append(flight_data)
    
    # return pd.DataFrame(data)

def process_delay_data(df):
    """
    Process delay data for analysis
    """
    df['delay_category'] = pd.cut(
        df['delay_minutes'],
        bins=[0, 10, 20, 40, float('inf')],
        labels=['No Delay', 'Minor', 'Significant', 'Severe']
    )
    
    return df

def calculate_weather_correlation(df):
    """
    Calculate correlation between weather conditions and delays
    """
    correlation = {
        'temp_correlation': df['temperature'].corr(df['delay_minutes']),
        'precip_correlation': df['precipitation'].corr(df['delay_minutes'])
    }
    
    return correlation