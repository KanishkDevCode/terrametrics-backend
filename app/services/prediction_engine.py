import numpy as np
from sklearn.linear_model import LinearRegression
from typing import Dict, List
from app.services.geospatial_engine import get_landcover_data

def predict_future_urban_area(roi_coords: List[float], target_year: int) -> Dict:
    """
    Uses machine learning to predict future urban expansion based on historical 
    satellite data from Google Earth Engine.
    """
    # 1. Gather historical training data (Sampling recent years)
    # Note: We use 2015 to 2022 because MODIS V061 has reliable data up to 2022
    historical_years = [2015, 2018, 2020, 2022]
    areas = []
    
    print("Gathering historical data for ML model training...")
    for year in historical_years:
        data = get_landcover_data(roi_coords, year)
        areas.append(data["urban_area_sq_km"])
        
    # 2. Prepare data for Scikit-Learn
    # X must be a 2D array (features), y is a 1D array (target)
    X = np.array(historical_years).reshape(-1, 1)
    y = np.array(areas)
    
    # 3. Initialize and train the model
    # While Random Forest is great for classification, Linear Regression is 
    # mathematically more stable for extrapolating time-series trends into the future.
    model = LinearRegression()
    model.fit(X, y)
    
    # 4. Predict the future urban area
    X_future = np.array([[target_year]])
    predicted_area = model.predict(X_future)[0]
    
    # Calculate the estimated growth from the last known data point (2022)
    last_known_area = areas[-1]
    projected_growth_rate = ((predicted_area - last_known_area) / last_known_area) * 100
    
    return {
        "status": "success",
        "target_year": target_year,
        "historical_data_used": dict(zip(historical_years, areas)),
        "predicted_urban_area_sq_km": round(predicted_area, 2),
        "projected_growth_rate_percent": round(projected_growth_rate, 2),
        "model_used": "Linear Regression (Time-Series Extrapolation)"
    }