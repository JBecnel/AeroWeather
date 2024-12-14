import os
import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime, timedelta, date
import logging
from .weather_service import weather_service, AIRPORT_COORDINATES
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataCollector:
    def __init__(self):
        # Create data directory if it doesn't exist
        self.data_dir = Path('data')
        self.data_dir.mkdir(exist_ok=True)
        
        # set the data base path
        self.db_path = self.data_dir / 'aviation_data.db'
        #self.init_database()
        
    def initialize_historical_data(self, force=False):
        # grab the data for the time period (last year starting on 12/11)
        try:
            logger.info("Starting historical data initialization...")
            
            end_date = date(2024,12,13)  # "finish" date of project
            start_date = end_date - timedelta(days=369)  # 1 year of data
            
            
            # Always reinitialize database when force is True
            if force:
                logger.info("Force flag is True, reinitializing database...")
                self.init_database()
                logger.info("Database reinitialized successfully")
            
            
            
                logger.info(f"Collecting historical data from {start_date} to {end_date}")
                # Collect and store historical data
                self.collect_and_store_data(start_date, end_date)
                logger.info("Data collection completed")

            # Verify data was stored
            stored_data = self.get_stored_data(start_date, end_date)
            if stored_data.empty:
                raise Exception("No data was stored after collection")
                
            logger.info(f"Historical data initialization completed. Stored {len(stored_data)} records")
            return stored_data
            
        except Exception as e:
            logger.error(f"Error initializing historical data: {str(e)}")
            logger.debug("Stack trace:", exc_info=True)
            raise
    
    def init_database(self):
        """Initialize SQLite database with required tables"""
        try:
            # Ensure data directory exists
            self.data_dir.mkdir(parents=True, exist_ok=True)
            
            # Remove existing database if it exists
            if self.db_path.exists():
                self.db_path.unlink()
                logger.info("Removed existing database")
            
            logger.info(f"Creating new database at {self.db_path}")
            
            # Create database connection
            with sqlite3.connect(self.db_path) as conn:
                logger.info("Creating flight_data table")
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS flight_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date DATE,
                        airline TEXT,
                        origin TEXT,
                        destination TEXT,
                        delay_minutes FLOAT,
                        temperature FLOAT,
                        precipitation FLOAT,
                        weather_condition TEXT,
                        weather_delay BOOLEAN,
                        wind_speed FLOAT,
                        wind_direction FLOAT,
                        visibility FLOAT,
                        cloud_coverage INTEGER,
                        humidity INTEGER,
                        pressure FLOAT,
                        collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            logger.debug("Stack trace:", exc_info=True)
            raise  # Re-raise the exception to be handled by the caller
    
    def collect_and_store_data(self, start_date=None, end_date=None):
        #Collect weather and flight data and store in database for a date range
        try:
            # Set date range
            if start_date is None:
                start_date = date(2024,12,11)
            if end_date is None:
                end_date = date(2023,12,11)

            logger.info(f"Starting data collection process for date range: {start_date} to {end_date}")
            
            # Get weather data for all airports for the date range
            logger.info(f"Fetching weather data from {start_date} to {end_date}...")
            current_date = pd.Timestamp(start_date)
            end_date = pd.Timestamp(end_date)
            
            #if not AIRPORT_COORDINATES:
            #    logger.error("No airport coordinates available")
            #    raise ValueError("Airport coordinates not configured")
            
            all_data = []
            while current_date <= end_date:
                try:
                    logger.info(f"Processing data for date: {current_date.date()}")
                    weather_data = weather_service.get_bulk_weather(AIRPORT_COORDINATES, current_date)
                    
                    if not weather_data:
                        logger.warning(f"No weather data available for {current_date.date()}. Using default values.")
                        weather_data = {}
                        
                    #print()
                    #print('weather data')
                    # Generate flight data for this specific date
                    daily_data = self._generate_flight_data(weather_data, current_date.date())
                    #print('daily_data')
                    all_data.append(daily_data)
                    
                except Exception as e:
                    logger.error(f"Error processing data for {current_date.date()}: {str(e)}")
                    logger.debug("Processing error details:", exc_info=True)
                
                current_date += pd.Timedelta(days=1)
            
            if not all_data:
                logger.error("No data was collected for any date")
                return
                
            # Combine all daily data
            combined_data = pd.concat(all_data, ignore_index=True)
            
            # Clean data
            cleaned_data = self._clean_data(combined_data)
            
            # Store in database
            self._store_data(cleaned_data)
            logger.info("Data collection and storage completed successfully")
            
        except Exception as e:
            logger.error(f"Error in data collection process: {str(e)}")
            logger.debug("Stack trace:", exc_info=True)
    
    def _generate_flight_data(self, weather_data, target_date):
        ##Generate flight data incorporating real weather data for a specific date
        data = []
        
        # TODO: Make a constant in airport_analysis and get airport from constant
        

        airlines = ['Delta', 'United', 'American', 'Southwest', 'JetBlue']
        delay_params = {
            'Delta' : (15, 10),
            'United' : (20, 5),
            'American' : (10, 14),
            'Southwest' : (12, 8),
            'JetBlue' : (30, 7)
        }
        airport_params = {
            'SEA' : (30, 10),
            'LAX' : (15, 3.75),
            'LGA' : (10, 4),
            'DFW' : (15, 8),
            'MIA' : (12, 6)
        }
        
        for airline in airlines:
            for origin, origin_coords in AIRPORT_COORDINATES.items():
                for dest, dest_coords in AIRPORT_COORDINATES.items():
                    if origin != dest:
                        # Get weather info for origin airport with fallback values
                        weather = weather_data.get(origin, {})
                        
                        # Generate flight entries
                        num_flights = np.random.poisson(5)
                        for _ in range(num_flights):
                            # Base flight data
                            flight_data = {
                                'date': target_date,
                                'airline': airline,
                                'origin': origin,
                                'destination': dest,
                                'temperature': weather.get('temperature', np.random.normal(50, 15)),
                                'precipitation': weather.get('precipitation', np.random.beta(2, 5)),
                                'weather_condition': weather.get('weather_condition', 'Clear'),
                                'wind_speed': weather.get('wind_speed', np.random.uniform(0, 20)),
                                'wind_direction': weather.get('wind_direction', np.random.randint(0, 360)),
                                'visibility': weather.get('visibility', np.random.uniform(5, 15)),
                                'cloud_coverage': weather.get('cloud_coverage', np.random.randint(0, 100)),
                                'humidity': weather.get('humidity', np.random.randint(30, 90)),
                                'pressure': weather.get('pressure', np.random.normal(1013, 5))
                            }
                            try:
                                # simulation a delay
                                alpha = 0
                                if not flight_data['precipitation']:
                                    flight_data['precipitation'] = 0.0
                                if flight_data['precipitation'] >= .3:
                                    #flight_data['weather_condition'] = "Rain"
                                    alpha = np.random.normal(10,3)
                                    if flight_data['temperature'] <= 32 :
                                        alpha = np.random.normal(25,5)
                                        #flight_data['weather_condition'] = "Snow"
                                
                                airline_factor = np.random.normal(delay_params[airline][0], delay_params[airline][1])
                            except Exception as e:
                                logger.error(f"Failed to simulate delay: {str(e)}")
                            
                            
                            airport_factor = np.random.normal(airport_params[origin][0], airport_params[origin][1])
                            temp_factor = (100-flight_data['temperature'])*0.01
                            base_delay = 0.5*airline_factor  + 0.5*airport_factor + flight_data['precipitation']*20 + temp_factor + alpha
                        
                            
                            flight_data['delay_minutes'] = max(0, base_delay)
                            flight_data['weather_delay'] = flight_data['delay_minutes'] > 30 
                       
                                
                            data.append(flight_data)
        
        return pd.DataFrame(data)
    
    def _clean_data(self, df):
        """Clean and validate the data"""
        # Remove duplicates
        df = df.drop_duplicates()
        
        # Handle missing values
        df = df.fillna({
            'temperature': df['temperature'].mean(),
            'precipitation': 0,
            'weather_condition': 'Clear',
            'delay_minutes': 0,
            'weather_delay': False
        })
        
        # Ensure proper data types
        df['date'] = pd.to_datetime(df['date']).dt.date
        df['weather_delay'] = df['weather_delay'].astype(bool)
        
        return df
    
    def _store_data(self, df):
        """Store the cleaned data in SQLite database"""
        conn = sqlite3.connect(self.db_path)
        try:
            df.to_sql('flight_data', conn, if_exists='append', index=False)
            logger.info(f"Stored {len(df)} records in the database")
        except Exception as e:
            logger.error(f"Error storing data: {str(e)}")
            logger.debug("Stack trace:", exc_info=True)
        finally:
            conn.close()
    
    def get_stored_data(self, start_date=None, end_date=None):
        """Retrieve stored data from the database"""
        query = "SELECT * FROM flight_data"
        if start_date and end_date:
            query += f" WHERE date BETWEEN '{start_date}' AND '{end_date}'"
        
        conn = sqlite3.connect(self.db_path)
        try:
            df = pd.read_sql_query(query, conn)
            return df
        finally:
            conn.close()

# Create a singleton instance
data_collector = DataCollector()
