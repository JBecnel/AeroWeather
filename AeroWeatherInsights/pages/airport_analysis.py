import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils.data_processor import load_sample_data

def airport_analysis_page():
    st.title("Airport Performance Analysis")
    st.markdown("### Detailed analysis of airport operations and weather impacts")
    
    # Load data
    df = load_sample_data()
    
    # Airport selection
    col1, col2 = st.columns([2, 1])
    with col1:
        selected_airport = st.selectbox(
            "Select Airport",
            options=sorted(df['origin'].unique()),
            help="Choose an airport to analyze its performance"
        )
    
    with col2:
        comparison_mode = st.checkbox("Enable Airport Comparison", 
                                    help="Compare selected airport with network average")
    
    # Filter data for selected airport
    airport_data = df[df['origin'] == selected_airport]
    airport_data.rename(columns = {'weather_condition' : 'Condition'}, inplace = True)
    
    # Calculate network averages for comparison
    network_stats = {
        'avg_delay': df['delay_minutes'].mean(),
        'weather_delay_pct': (df['weather_delay'].sum() / len(df)) * 100,
        'total_flights': len(df) / len(df['origin'].unique())
    }
    
    # Display key metrics
    st.subheader("Performance Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    avg_delay = airport_data['delay_minutes'].mean()
    total_flights = len(airport_data)
    weather_delay_pct = (airport_data['weather_delay'].sum() / len(airport_data)) * 100
    
    delta_delay = avg_delay - network_stats['avg_delay'] if comparison_mode else None
    delta_flights = total_flights - network_stats['total_flights'] if comparison_mode else None
    delta_weather = weather_delay_pct - network_stats['weather_delay_pct'] if comparison_mode else None
    
    col1.metric("Average Delay", f"{avg_delay:.1f} min", 
                delta=f"{delta_delay:+.1f} min" if comparison_mode else None,
                delta_color="inverse")
    col2.metric("Total Flights", f"{total_flights:,}", 
                delta=f"{delta_flights:+,.0f}" if comparison_mode else None)
    col3.metric("Weather Delays", f"{weather_delay_pct:.1f}%", 
                delta=f"{delta_weather:+.1f}%" if comparison_mode else None,
                delta_color="inverse")
    with col4:
        reliability_score = 100 - weather_delay_pct
        st.metric("Airport Reliability Score", 
                 f"{reliability_score:.1f}%",
                 help="Score based on weather resilience and delay patterns")
    
    
    # Weather condition breakdown
    st.subheader("Weather Impact Analysis")
    
    
    
    # table by weather conditions
    st.markdown("#### Weather Condition Impact")
    weather_impact = airport_data.groupby('Condition').agg({
        'delay_minutes': ['mean', 'count', 'std'],
        'weather_delay': 'sum'
    }).round(2)
    
    
    weather_impact.columns = ['Avg Delay', 'Flights', 'Delay Std', 'Weather Delays']
    st.dataframe(weather_impact, use_container_width=True)

    # col1, col2 = st.columns(2)
    # with col1:    
    #     # reliability score
    #     reliability_score = 100 - weather_delay_pct
    #     st.metric("Airport Reliability Score", 
    #              f"{reliability_score:.1f}%",
    #              help="Score based on weather resilience and delay patterns")
    

    st.markdown("#### Delay Distribution by Weather")
    fig = px.box(airport_data, 
                x='Condition', 
                y='delay_minutes',
                color='Condition',    
                template='plotly_dark')
    fig.update_layout(
        xaxis_title = "Condition",
        yaxis_title = "Delay Minutes",        
    )
    st.plotly_chart(fig, use_container_width=True)

    # Historical trends
    st.subheader("Historical Delay Trends")
    daily_delays = airport_data.groupby('date').agg({
        'delay_minutes': 'mean',
        'weather_delay': ['count', 'mean']
    }).round(2)
    
    daily_delays.columns = ['Avg Delay', 'Total Flights', 'Weather Delay Rate']
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily_delays.index,
        y=daily_delays['Avg Delay'],
        name='Average Delay',
        mode='lines',
        line=dict(color='#00A5E5', width=2)
    ))
    
    fig.add_trace(go.Bar(
        x=daily_delays.index,
        y=daily_delays['Weather Delay Rate'] * 100,
        name='Weather Delay %',
        yaxis='y2',
        marker_color='#FFFF00'
    ))
    
    fig.update_layout(
        template='plotly_dark',    
        xaxis_title='Date',
        yaxis_title='Average Delay (minutes)',
        yaxis2=dict(
            title='Weather Delay %',
            overlaying='y',
            side='right',
            range=[0, 100]
        ),
        legend=dict(
            x = 1.2,
            y = 1.0
        ),
        showlegend=True,
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

    # Route performance
    st.subheader("Route Performance Analysis")
    route_data = df[df['origin'] == selected_airport].groupby('destination').agg({
        'delay_minutes': ['mean', 'count', 'std'],
        'weather_delay': 'sum'
    }).round(2)
    
    # Calculate confidence intervals
    confidence_level = 0.95
    from scipy import stats
    
    route_stats = []
    for dest in route_data.index:
        dest_data = airport_data[airport_data['destination'] == dest]['delay_minutes']
        if len(dest_data) > 1:
            ci = stats.t.interval(
                confidence_level,
                len(dest_data)-1,
                loc=dest_data.mean(),
                scale=stats.sem(dest_data)
            )
        else:
            ci = (dest_data.mean(), dest_data.mean())
        
        route_stats.append({
            'destination': dest,
            'avg_delay': dest_data.mean(),
            'ci_lower': max(0, ci[0]),
            'ci_upper': ci[1],
            'total_flights': len(dest_data),
            'weather_delays': route_data.loc[dest, ('weather_delay', 'sum')]
        })
    
    route_stats_df = pd.DataFrame(route_stats)
    
    # Create dual-axis chart
    fig = go.Figure()
    
    # Add average delay bars with error bars
    fig.add_trace(go.Bar(
        x=route_stats_df['destination'],
        y=route_stats_df['avg_delay'],
        name='Average Delay',
        error_y=dict(
            type='data',
            symmetric=False,
            array=route_stats_df['ci_upper'] - route_stats_df['avg_delay'],
            arrayminus=route_stats_df['avg_delay'] - route_stats_df['ci_lower']
        ),
        marker_color='#00A5E5'
    ))
    
    # Add weather delay percentage line
    fig.add_trace(go.Scatter(
        x=route_stats_df['destination'],
        y=route_stats_df['weather_delays'] / route_stats_df['total_flights'] * 100,
        name='Weather Delay %',
        yaxis='y2',
        mode='lines+markers',
        line=dict(color='#FFA500', width=2),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        template='plotly_dark',        
        xaxis_title='Destination',
        yaxis_title='Average Delay (minutes)',
        yaxis2=dict(
            title='Weather Delay %',
            overlaying='y',
            side='right',
            range=[0, 100]
        ),
        legend=dict(
            x = 1.2,
            y = 1.0
        ),
        showlegend=True,
        height=500,
        barmode='group'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Display detailed route statistics
    st.markdown("#### Detailed Route Statistics")
    st.markdown(f"*Showing {confidence_level*100:.0f}% confidence intervals for delay estimates*")
    
    detailed_stats = route_stats_df.copy()
    detailed_stats['confidence_interval'] = detailed_stats.apply(
        lambda x: f"({x['ci_lower']:.1f}, {x['ci_upper']:.1f})",
        axis=1
    )
    
    display_cols = {
        'destination': 'Route',
        'avg_delay': 'Avg Delay (min)',
        'confidence_interval': 'Confidence Interval',
        'total_flights': 'Total Flights',
        'weather_delays': 'Weather Delays'
    }
    
    detailed_stats = detailed_stats[display_cols.keys()].rename(columns=display_cols)
    st.dataframe(detailed_stats.set_index('Route'), use_container_width=True)
    
    # Seasonal Analysis
    st.subheader("Seasonal Patterns and Capacity Analysis")
    
    # Convert date to month and season
    airport_data['month'] = pd.to_datetime(airport_data['date']).dt.month
    airport_data['season'] = pd.to_datetime(airport_data['date']).dt.month.map({
        12: 'Winter', 1: 'Winter', 2: 'Winter',
        3: 'Spring', 4: 'Spring', 5: 'Spring',
        6: 'Summer', 7: 'Summer', 8: 'Summer',
        9: 'Fall', 10: 'Fall', 11: 'Fall'
    })
    
    col1, col2 = st.columns(2)
    
    with col1:    
        seasonal_delays = airport_data.groupby('season').agg({
            'delay_minutes': ['mean', 'std'],
            'weather_delay': ['sum', 'count']
        }).round(2)
        
        seasonal_delays.columns = ['Avg Delay', 'Delay Std', 'Weather Delays', 'Total Flights']
        seasonal_delays['Weather Delay %'] = (seasonal_delays['Weather Delays'] / 
                                            seasonal_delays['Total Flights'] * 100).round(1)
        
        fig = px.bar(
            seasonal_delays.reset_index(),
            x='season',
            y='Avg Delay',
            error_y='Delay Std',
            title='Average Delays by Season',
            template='plotly_dark'
        )
        st.plotly_chart(fig, use_container_width=True)
        
         #st.dataframe(seasonal_delays, use_container_width=True)
    
    with col2:
        st.markdown("#### Flight Metrics")
        
        # Calculate daily flight counts
        daily_flights = airport_data.groupby('date').size()
        capacity_metrics = {
            'Peak Daily Flights': daily_flights.max(),
            'Average Daily Flights': daily_flights.mean()
            #'Capacity Utilization': (daily_flights.mean() / daily_flights.max() * 100),
            #'Days at >90% Capacity': (daily_flights >= 0.9 * daily_flights.max()).sum()
        }
        
        # Display capacity metrics
        for metric, value in capacity_metrics.items():
            st.metric(
                metric,
                f"{value:.1f}" if 'Utilization' in metric or 'Average' in metric else f"{int(value)}"
            )
        
        # # Plot daily capacity utilization
        # fig = px.line(
        #     x=daily_flights.index,
        #     y=(daily_flights / daily_flights.max() * 100),
        #     title='Daily Capacity Utilization',
        #     template='plotly_dark'
        # )
        # fig.update_layout(
        #     xaxis_title='Date',
        #     yaxis_title='Capacity Utilization (%)',
        #     showlegend=False
        # )
        # st.plotly_chart(fig, use_container_width=True)

    # Display seasonal statistics
    st.dataframe(seasonal_delays, use_container_width=True)
    

if __name__ == "__main__":
    airport_analysis_page()
