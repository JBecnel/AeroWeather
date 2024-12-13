FORCE_GET_DATA = True

import logging
import sys
import pandas as pd
import streamlit as st
import plotly.express as px
from utils.data_processor import load_sample_data
from datetime import date

# configure basic logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('aviation_analytics.log')
    ]
)
logger = logging.getLogger(__name__)


logger.info("Starting Aviation Analytics Platform")

try:
    from utils.visualization import create_delay_overview
    logger.info("Successfully imported visualization module")
except ImportError as e:
    # default scatterplaot
    logger.error(f"Failed to import visualization module: {str(e)}")
    create_delay_overview = lambda df: px.scatter(df, x='date', y='delay_minutes', title='Delay Overview')

from utils.analysis import calculate_basic_stats
from utils.weather_service import AIRPORT_COORDINATES
from utils.data_collection import data_collector

def init_application():
    #Initialize application data and handle errors
    try:
        logger.info("Starting application initialization")
        
        # Initialize data collector and fetch historical data
        logger.info("Initializing data ....")
        initial_data = data_collector.initialize_historical_data(force=FORCE_GET_DATA)  # Force reinitialization
        
        if initial_data is not None and not initial_data.empty:
            logger.info(f"Successfully loaded {len(initial_data)} records from {initial_data['date'].min()} to {initial_data['date'].max()}")
            return initial_data
        else:
            logger.error("Data initialization returned empty dataset")
            return pd.DataFrame()
            
    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}")
        logger.debug("Stack trace:", exc_info=True)
        return pd.DataFrame()

# Initialize error handler for streamlit
st.set_option('client.showErrorDetails', True)

# Page configuration
st.set_page_config(
    page_title="Aviation Analytics Platform",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .stApp {
        background-color: #1F2937;
    }
    .stMetric {
        background-color: #374151;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

def main():
    st.title("✈️ Aviation Analytics Platform")
    st.markdown("### Flight Delays & Weather Correlation Analysis")

    logger.info("Starting to load application data")
    
    # Initialize application data
    with st.spinner("Loading application data..."):
        df = init_application()
        if df.empty:
            st.error("No data available. Please check the logs for details.")
            logger.error("No data available after initialization")
            return
        else:
            st.success(f"Successfully loaded {len(df)} records!")
            logger.info(f"Successfully loaded data with {len(df)} records")
    
    # Date range filter
    try:
        # defaults
        max_date = date(2024, 12, 11) #pd.Timestamp.now().date()
        min_date = (pd.Timestamp.now() - pd.DateOffset(years=1)).date()
        
        if not df.empty and 'date' in df.columns:
            data_min_date = pd.to_datetime(df['date']).min().date()
            data_max_date = pd.to_datetime(df['date']).max().date()
            min_date = min(min_date, data_min_date)
            max_date = max(max_date, data_max_date)
        
        date_range = st.sidebar.date_input(
            "Select Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
                
        start_date, end_date = date_range
        
    except Exception as e:
        logger.error(f"Error setting date range: {str(e)}")
        start_date = end_date = date(2024, 12, 11) #pd.Timestamp.now().date()
    
    # Airline filter
    try:
        available_airlines = sorted(df['airline'].unique()) if not df.empty else []
        selected_airlines = st.sidebar.multiselect(
            "Select Airlines",
            options=available_airlines,
            default=available_airlines[:len(available_airlines)] if available_airlines else []
        )
    except Exception as e:
        logger.error(f"Error setting airline filter: {str(e)}")
        selected_airlines = []
    
    # Filter data based on selections
    try:
        filtered_df = df.copy()
        if not filtered_df.empty:
            filtered_df['date'] = pd.to_datetime(filtered_df['date'])
            mask = (
                (filtered_df['date'].dt.date >= start_date) &
                (filtered_df['date'].dt.date <= end_date)
            )
            if selected_airlines:
                mask &= filtered_df['airline'].isin(selected_airlines)
            filtered_df = filtered_df[mask]
            
        if filtered_df.empty:
            st.warning("No data available for the selected filters.")
            return
            
    except Exception as e:
        logger.error(f"Error filtering data: {str(e)}")
        st.error("An error occurred while filtering the data.")
        return
    
    # Overview metrics
    col1, col2, col3 = st.columns(3)
    stats = calculate_basic_stats(filtered_df)
    
    col1.metric("Average Delay", f"{stats['avg_delay']:.1f} min")
    col2.metric("Total Flights", f"{stats['total_flights']:,}")
    col3.metric("Weather Delay %", f"{stats['weather_delay_pct']:.1f}%")
    
    # Main visualization
    st.subheader("Delay Overview")
    fig = create_delay_overview(filtered_df)
    st.plotly_chart(fig, use_container_width=True)
    
    # Additional insights
    st.subheader("Key Insights")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Delay Distribution by Airline")
        fig = px.box(filtered_df, 
                     x='airline', 
                     y='delay_minutes',
                    color='airline', labels = {"airline" : "Airline", "delay_minutes" : "Delay (min)"},  template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Delay Distribution by Origin")
        fig = px.box(filtered_df, 
                         x='origin', 
                         y='delay_minutes',
                        color='origin', 
                        labels = {"origin" : "Origin", "delay_minutes" : "Delay (min)"},
                        template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()