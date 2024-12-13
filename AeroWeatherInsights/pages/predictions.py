RETRAIN = True

import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import date
from utils.data_processor import load_sample_data
from utils.analysis import train_model, predict_with_interval, get_model

def predictions_page():
    st.title("Delay Predictions")
    
    
    df = load_sample_data()
    
    # Get prediction model
    if (RETRAIN):
        prediction_model = train_model(df)
    else:
        prediction_model = get_model()

    
    # Display model metrics
    metrics = prediction_model['metrics']
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("R-squared", f"{metrics['r_squared']:.3f}")
    col2.metric("RMSE", f"{metrics['rmse']:.1f} min")
    col3.metric("MAE", f"{metrics['mae']:.1f} min")
    col4.metric("CV RMSE", f"{metrics['cv_rmse']:.1f} min")
    
    # Feature importance plot
    st.subheader("Feature Importance")
    fig = px.bar(
        prediction_model['feature_importance'],
        x='importance',
        y='feature',
        orientation='h',
        template='plotly_dark',
        title='Model Feature Importance'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Interactive prediction
    st.subheader("Delay Prediction Tool")
    
    col1, col2 = st.columns(2)
    with col1:
        temperature = st.slider(
            "Temperature (°F)",
            min_value=-30.0,
            max_value=100.0,
            value=75.0
        )
    
    with col2:
        precipitation = st.slider(
            "Precipitation Probability",
            min_value=0.0,
            max_value=1.0,
            value=0.5
        )
    
    # Date selection for prediction
    selected_date = st.date_input(
        "Select Date for Prediction",
        value=date(2024, 12, 11)
    )
    
    # Calculate prediction with confidence intervals
    #prediction = prediction_model['predict_with_interval'](
    prediction = predict_with_interval(
        df, 
        prediction_model,
        temperature,
        precipitation,
        pd.Timestamp(selected_date)
    )
    
    # Display prediction results
    col1, col2, col3 = st.columns(3)
    
    col1.metric(
        "Predicted Delay",
        f"{prediction['prediction']:.1f} minutes"
    )
    
    col2.metric(
        "Lower Bound",
        f"{prediction['lower_bound']:.1f} minutes"
    )
    
    col3.metric(
        "Upper Bound",
        f"{prediction['upper_bound']:.1f} minutes"
    )
    
    # Model insights
    st.subheader("Model Insights")
    st.info("""
        This prediction is based on a Random Forest model that considers:
        - Temperature and precipitation
        - Day of week and seasonal patterns
        - Weather severity indicators
        - Interactive effects between weather conditions
        
        The confidence interval is calculated using cross-validation error estimates.
    """)
    
    # Historical comparison
    st.subheader("Historical Delay Distribution")
    fig = px.histogram(
        df,
        x='delay_minutes',
        template='plotly_dark',
        title='Historical Delay Distribution'
    )
    # Add vertical line for prediction
    pred_value = float(prediction['prediction'])
    fig.add_vline(
        x=pred_value,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Predicted Delay: {pred_value:.1f} min"
    )
    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    predictions_page()
