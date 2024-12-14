import pandas as pd
import numpy as np
from scipy import stats
import logging
import pickle

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_basic_stats(df):
    """
    Calculate basic statistics 
    """
    stats = {
        'avg_delay': df['delay_minutes'].mean(),
        'total_flights': len(df),
        'weather_delay_pct': (df['weather_delay'].sum() / len(df)) * 100,
        'max_delay': df['delay_minutes'].max(),
        'min_delay': df['delay_minutes'].min()
    }
    
    return stats

def perform_weather_analysis(df):
    """
    Analyze weather impact on delays with enhanced statistical insights
    """
    # Calculate correlation coefficients with confidence intervals
    temp_corr = stats.pearsonr(df['temperature'], df['delay_minutes'])
    precip_corr = stats.pearsonr(df['precipitation'], df['delay_minutes'])
    
    # Calculate weather severity levels with handling for duplicate values
    try:
        severity_score = df['delay_minutes']
        severity_thresholds = pd.qcut(
            severity_score,
            q=4,
            labels=['Low', 'Moderate', 'High', 'Severe'],
            duplicates='drop'
        )
        df['weather_severity'] = severity_thresholds.astype(str)
    except Exception as e:
        logger.warning(f"Error calculating severity thresholds: {str(e)}")
        df['weather_severity'] = 'Low'  # Default value if calculation fails
    
    # Detailed weather impact analysis
    weather_impact = df.groupby(['weather_severity', 'weather_delay'])['delay_minutes'].agg([
        'mean',
        'count',
        'std',
        ('ci_lower', lambda x: stats.t.interval(0.95, len(x)-1, loc=x.mean(), scale=stats.sem(x))[0]),
        ('ci_upper', lambda x: stats.t.interval(0.95, len(x)-1, loc=x.mean(), scale=stats.sem(x))[1])
    ]).round(2)
    
    # Calculate additional weather metrics
    weather_metrics = {
        'avg_delay_by_severity': df.groupby('weather_severity')['delay_minutes'].mean(),
        'delay_probability': df.groupby('weather_severity')['weather_delay'].mean(),
    }
    
    return {
        'temperature_correlation': temp_corr,
        'precipitation_correlation': precip_corr,
        'weather_impact': weather_impact,
        'weather_metrics': weather_metrics
    }

def train_model(df):
    """
    Enhanced delay prediction using Random Forest with feature engineering,
    cross-validation, and comprehensive evaluation metrics
    """
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.model_selection import cross_val_score
    from sklearn.metrics import mean_squared_error, mean_absolute_error
    from sklearn.preprocessing import StandardScaler
    import numpy as np

    # Feature engineering
    def engineer_features(data):
        features = data.copy()
        # Time-based features
        features['day_of_week'] = pd.to_datetime(features['date']).dt.dayofweek
        features['month'] = pd.to_datetime(features['date']).dt.month
        
        # Weather interaction features
        features['temp_precip_interaction'] = features['temperature'] * features['precipitation']
        # severe weather is low temp and high precipitation
        features['severe_weather'] = (features['temperature'] < features['temperature'].quantile(0.2)) & \
                                   (features['precipitation'] > features['precipitation'].quantile(0.8))
        
        return features

    # Prepare features
    feature_df = engineer_features(df)
    feature_columns = ['temperature', 'precipitation', 'day_of_week', 'month',
                      'temp_precip_interaction', 'severe_weather']
    X = feature_df[feature_columns]
    y = feature_df['delay_minutes']

    # normalize the features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    X_scaled = pd.DataFrame(X_scaled, columns=X.columns)

   

    # Train Random Forest model
    rf_model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=42
    )
    rf_model.fit(X_scaled, y)

   
    # Cross-validation scores
    cv_scores = cross_val_score(rf_model, X_scaled, y, cv=5)
    cv_rmse = np.sqrt(-cv_scores.mean())

    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': feature_columns,
        'importance': rf_model.feature_importances_
    }).sort_values('importance', ascending=False)

   
    # Calculate metrics
    y_pred = rf_model.predict(X_scaled)
    rmse = np.sqrt(mean_squared_error(y, y_pred))
    mae = mean_absolute_error(y, y_pred)
    r2 = rf_model.score(X_scaled, y)



    results = {
        'model': rf_model,
        'feature_importance': feature_importance,
        'predict_with_interval': predict_with_interval,
        'metrics': {
            'rmse': rmse,
            'mae': mae,
            'r_squared': r2,
            'cv_rmse': cv_rmse
        },
        'scaler': scaler,
        'feature_columns': feature_columns
    }

    with open('results.pkl', 'wb') as file:
        pickle.dump(results, file)

    return results


def get_model():
    try:
        with open('results.pkl', 'rb')as file:
            results = pickle.load(file)
    except Exception as e:
        logger.error(f"Error accessing model from file: {str(e)}")
        
    return results


 # Prediction function with uncertainty
def predict_with_interval(df, model, temp, precip, date=None, confidence=0.95):
    if date is None:
        date = date(2024, 12, 11)
        
    # Create feature vector
    features = pd.DataFrame({
        'temperature': [temp],
        'precipitation': [precip],
        'day_of_week': [date.dayofweek],
        'month': [date.month],
        'temp_precip_interaction': [temp * precip],
        'severe_weather': [(temp > df['temperature'].quantile(0.8)) & 
                        (precip > df['precipitation'].quantile(0.8))]
    })
    
    # Scale features
    features_scaled = model['scaler'].transform(features)
    
    # Make prediction
    prediction = model['model'].predict(features_scaled)[0]
    
    # Calculate prediction interval using cross-validation error
    cv_rmse = model['metrics']['cv_rmse']
    margin = cv_rmse * 1.96  # 95% confidence interval
    
    return {
        'prediction': prediction,
        'lower_bound': max(0, prediction - margin),
        'upper_bound': prediction + margin,
        'confidence': confidence
    }
