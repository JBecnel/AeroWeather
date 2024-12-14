import streamlit as st
import plotly.express as px
from datetime import date
from utils.data_processor import load_sample_data
from utils.visualization import create_weather_heatmap
from utils.analysis import perform_weather_analysis

def weather_correlation_page():
    st.title("Weather Impact Analysis")
    st.markdown("### Analyzing how weather conditions affect flight delays")
    
    # Load data
    df = load_sample_data()
    
    # Perform weather analysis
    weather_analysis = perform_weather_analysis(df)
    
    # Display correlation metrics
    st.subheader("Weather Correlation Analysis")
    col1, col2 = st.columns(2)
    
    # Format correlation values with specific format to handle PearsonRResult
    temp_corr = weather_analysis['temperature_correlation']
    precip_corr = weather_analysis['precipitation_correlation']
    
    with col1:
        st.metric(
            "Temperature Correlation",
            f"{float(temp_corr[0]):.3f}",
            help=f"p-value: {float(temp_corr[1]):.3f}"
        )
    with col2:
        st.metric(
            "Precipitation Correlation",
            f"{float(precip_corr[0]):.3f}",
            help=f"p-value: {float(precip_corr[1]):.3f}"
        )
    
    # Weather severity analysis
    st.subheader("Delay Analysis by Weather Severity")
    col1, col2 = st.columns(2)
    
    with col1:
        # Average delays by severity
        fig = px.bar(
            weather_analysis['weather_metrics']['avg_delay_by_severity'].reset_index(),
            x='weather_severity',
            y='delay_minutes',
            title='Average Delay by Weather Severity',
            template='plotly_dark'
        )
        fig.update_layout(
            xaxis_title='Weather Severity',
            yaxis_title='Delay Minutes',
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Delay probability by severity
        fig = px.bar(
            weather_analysis['weather_metrics']['delay_probability'].reset_index(),
            x='weather_severity',
            y='weather_delay',
            title='Delay Probability by Weather Severity',
            template='plotly_dark'
        )
        fig.update_layout(
            xaxis_title='Weather Severity',
            yaxis_title='Chance of Delay',
        )
        fig.update_layout(yaxis_title='Probability of Delay')
        st.plotly_chart(fig, use_container_width=True)
    
        
    # Weather impact heatmap
    # st.subheader("Historical Weather Conditions Impact")
    # fig = create_weather_heatmap(df)
    # st.plotly_chart(fig, use_container_width=True)
    
    # Detailed statistics
    st.subheader("Detailed Weather Impact Statistics")
    st.markdown("Statistics include mean delay, count of flights, and 95% confidence intervals")
    st.dataframe(weather_analysis['weather_impact'])

if __name__ == "__main__":
    weather_correlation_page()
