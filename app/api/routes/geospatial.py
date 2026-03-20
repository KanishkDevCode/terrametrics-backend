from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.prediction_engine import predict_future_urban_area
from app.services.geospatial_engine import (
    get_landcover_data, 
    calculate_urban_growth_rate, 
    get_map_tile # <-- UPDATED: Now imports the multi-layer function
)

router = APIRouter()

# Schema for incoming coordinate requests
class RegionRequest(BaseModel):
    lon: float
    lat: float

@router.post("/landcover/{year}", tags=["Geospatial"])
async def fetch_landcover(year: int, payload: RegionRequest):
    try:
        data = get_landcover_data([payload.lon, payload.lat], year)
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/urban-growth", tags=["Geospatial"])
async def fetch_urban_growth(past_year: int, current_year: int, payload: RegionRequest):
    try:
        growth_data = calculate_urban_growth_rate(
            [payload.lon, payload.lat], 
            past_year, 
            current_year
        )
        return {"status": "success", "data": growth_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- UPDATED ROUTE: Now handles Urban, NDVI, and LST ---

@router.post("/map-layer", tags=["Geospatial"])
async def fetch_map_layer(year: int, payload: RegionRequest, layer_type: str = "urban"):
    """
    Returns a tile URL for Urban Sprawl, NDVI, or LST.
    """
    try:
        map_data = get_map_tile([payload.lon, payload.lat], year, layer_type)
        return {"status": "success", "data": map_data}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))    

# -------------------------------------------------------

@router.post("/predict-urban-expansion", tags=["Advanced ML"])
async def fetch_urban_prediction(target_year: int, payload: RegionRequest):
    """
    Predicts future urban sprawl for a given target year (e.g., 2030).
    Warning: This fetches multiple years of historical data from GEE synchronously, 
    so it may take 10-15 seconds to return a response.
    """
    # Ensure the target year is actually in the future
    if target_year <= 2022:
        raise HTTPException(status_code=400, detail="Target year must be in the future (> 2022).")
        
    try:
        prediction_data = predict_future_urban_area([payload.lon, payload.lat], target_year)
        return prediction_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))