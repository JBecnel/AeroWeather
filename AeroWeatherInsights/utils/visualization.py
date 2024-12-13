import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_delay_overview(df):
    """
    Create enhanced delay overview visualization with airport-specific insights
    """
    fig = go.Figure()
    
    # Ensure date column is datetime and data is properly filtered
    df = df.copy()
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
        
        # Calculate daily averages by airport
        daily_delays = df.groupby(['date', 'origin'])['delay_minutes'].mean().reset_index()
        daily_delays = daily_delays.sort_values('date')  # Sort by date for proper line plotting
    else:
        # Return empty figure if no data
        return fig
    
    # Plot lines for each airport
    for airport in df['origin'].unique():
        airport_data = daily_delays[daily_delays['origin'] == airport]
        fig.add_trace(go.Scatter(
            x=airport_data['date'],
            y=airport_data['delay_minutes'],
            mode='lines',
            name=f'{airport} Delays',
            line=dict(width=2),
            opacity=0.7
        ))
    
    # Add overall trend line
    overall_delays = df.groupby('date')['delay_minutes'].mean().reset_index()
    fig.add_trace(go.Scatter(
        x=overall_delays['date'],
        y=overall_delays['delay_minutes'],
        mode='lines+markers',
        name='Network Average',
        line=dict(color='#00A5E5', width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        template='plotly_dark',
        title='Flight Delays and Weather Trends',
        xaxis_title='Date',
        yaxis_title='Average Delay (minutes)',
        showlegend=True,
        height=500
    )
    
    return fig

def create_weather_heatmap(df):
    """
    Create weather correlation heatmap with string labels and handle duplicate values
    """
    if df.empty:
        return go.Figure()  # Return empty figure if no data
        
    # Create quantile labels
    temp_labels = [f"T{i+1}" for i in range(10)]
    precip_labels = [f"P{i+1}" for i in range(10)]
    
    # Create a copy and handle temperature binning
    df = df.copy()
    
    try:
        # Handle temperature binning with unique values
        temp_unique = df['temperature'].drop_duplicates().sort_values()
        temp_bins = np.linspace(temp_unique.min(), temp_unique.max(), num=11)
        df['temp_bin'] = pd.cut(df['temperature'], 
                               bins=temp_bins, 
                               labels=temp_labels,
                               include_lowest=True)
        
        # Handle precipitation binning
        precip_unique = df['precipitation'].drop_duplicates().sort_values()
        precip_bins = np.linspace(precip_unique.min(), precip_unique.max(), num=11)
        df['precip_bin'] = pd.cut(df['precipitation'],
                                 bins=precip_bins,
                                 labels=precip_labels,
                                 include_lowest=True)
    except Exception as e:
        logger.error(f"Error in weather heatmap binning: {str(e)}")
        return go.Figure()  # Return empty figure on error
    
    # Create pivot table with string labels
    pivot_table = df.pivot_table(
        values='delay_minutes',
        index='temp_bin',
        columns='precip_bin',
        aggfunc='mean',
        observed=True
    )
    
    # Create heatmap
    fig = px.imshow(
        pivot_table,
        template='plotly_dark',
        color_continuous_scale='RdYlBu_r',
        aspect='auto'  # Maintain reasonable aspect ratio
    )
    
    # Update layout with better labels
    fig.update_layout(
        title='Delay Intensity by Weather Conditions',
        xaxis_title='Precipitation Level (P1=Lowest, P10=Highest)',
        yaxis_title='Temperature Level (T1=Lowest, T10=Highest)',
        coloraxis_colorbar_title='Average Delay (minutes)'
    )
    
    return fig
