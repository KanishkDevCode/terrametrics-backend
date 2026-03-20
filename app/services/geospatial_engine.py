import ee
from typing import Dict, List

try:
    ee.Initialize()
except Exception as e:
    print("Warning: Earth Engine not initialized. Please authenticate.")

def get_landcover_data(roi_coords: List[float], year: int) -> Dict:
    """
    Fetches land cover classification for a given year using MODIS (MCD12Q1 V061).
    roi_coords: [longitude, latitude]
    """
    point = ee.Geometry.Point(roi_coords)
    roi = point.buffer(10000) # 10km radius around the point

    # 1. UPDATED DATASET ID TO VERSION 061
    dataset_col = ee.ImageCollection('MODIS/061/MCD12Q1').filterDate(f'{year}-01-01', f'{year}-12-31')
    
    # 2. SAFETY CHECK: Ensure data exists for the requested year
    if dataset_col.size().getInfo() == 0:
        raise ValueError(f"No MODIS land cover data available for the year {year}. The dataset typically covers 2001 to 2022.")

    dataset = dataset_col.first()
    
    # Select the IGBP classification band
    landcover = dataset.select('LC_Type1')

    # Calculate area of Urban class (IGBP class 13 is 'Urban and Built-up')
    urban_area_img = landcover.eq(13).multiply(ee.Image.pixelArea())
    
    urban_stats = urban_area_img.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=roi,
        scale=500,
        maxPixels=1e9
    ).getInfo()

    # Convert square meters to square kilometers
    urban_sq_km = urban_stats.get('LC_Type1', 0) / 1e6

    return {
        "year": year,
        "urban_area_sq_km": round(urban_sq_km, 2)
    }

def calculate_urban_growth_rate(roi_coords: List[float], past_year: int, current_year: int) -> Dict:
    """
    Calculates the growth rate between two time periods.
    """
    past_data = get_landcover_data(roi_coords, past_year)
    current_data = get_landcover_data(roi_coords, current_year)
    
    past_area = past_data["urban_area_sq_km"]
    current_area = current_data["urban_area_sq_km"]
    
    # Prevent division by zero
    if past_area == 0:
        raise ValueError("Past urban area is zero, cannot calculate growth rate.")

    # Core Formula
    growth_rate = (current_area - past_area) / past_area
    
    return {
        "past_year": past_year,
        "current_year": current_year,
        "past_area_sq_km": past_area,
        "current_area_sq_km": current_area,
        "growth_rate_percentage": round(growth_rate * 100, 2)
    }

def get_map_tile(roi_coords: List[float], year: int, layer_type: str = "urban") -> Dict:
    """
    Generates a map tile URL for Urban Sprawl, Vegetation (NDVI), or Urban Heat (LST).
    """
    point = ee.Geometry.Point(roi_coords)
    roi = point.buffer(10000) 

    if layer_type == "urban":
        # Original: MODIS Land Cover (Class 13 - Urban)
        dataset_col = ee.ImageCollection('MODIS/061/MCD12Q1').filterDate(f'{year}-01-01', f'{year}-12-31')
        if dataset_col.size().getInfo() == 0: raise ValueError(f"No map data for {year}.")
        
        landcover = dataset_col.first().select('LC_Type1')
        urban_mask = landcover.eq(13)
        image = urban_mask.updateMask(urban_mask)
        vis_params = {'min': 1, 'max': 1, 'palette': ['FF0000']} # Solid Red

    elif layer_type == "ndvi":
        # NEW: MODIS NDVI (Vegetation Index)
        dataset_col = ee.ImageCollection('MODIS/061/MOD13A1').filterDate(f'{year}-01-01', f'{year}-12-31')
        if dataset_col.size().getInfo() == 0: raise ValueError(f"No NDVI data for {year}.")
        
        # Take the median of the year to avoid cloud cover, clip to our 10km radius
        image = dataset_col.median().select('NDVI').clip(roi)
        # Palette: Brown (barren/urban) to Dark Green (dense forest)
        vis_params = {'min': 0, 'max': 8000, 'palette': ['FFFFFF', 'CE7E45', 'DF923D', 'F1B555', 'FCD163', '99B718', '74A901', '66A000', '529400', '3E8601', '207401', '056201']}

    elif layer_type == "lst":
        # NEW: MODIS Land Surface Temperature (Urban Heat Island effect)
        dataset_col = ee.ImageCollection('MODIS/061/MOD11A2').filterDate(f'{year}-01-01', f'{year}-12-31')
        if dataset_col.size().getInfo() == 0: raise ValueError(f"No LST data for {year}.")
        
        image = dataset_col.median().select('LST_Day_1km').clip(roi)
        # Palette: Blue (Cool) to Red/Black (Extremely Hot)
        vis_params = {'min': 14000, 'max': 16000, 'palette': ['040274', '040281', '0502a3', '0502b8', '0502ce', '0502e6', '0602ff', '235cb1', '307ef3', '269db1', '30c8e2', '32d3ef', '3be285', '3ff38f', '86e26f', '3ae237', 'b5e22e', 'd6e21f', 'fff705', 'ffd611', 'ffb613', 'ff8b13', 'ff6e08', 'ff500d', 'ff0000', 'de0101', 'c21301']}

    else:
        raise ValueError("Invalid layer_type. Choose 'urban', 'ndvi', or 'lst'.")

    # Generate the tile URL
    map_id_dict = ee.Image(image).getMapId(vis_params)
    
    return {
        "year": year,
        "layer_type": layer_type,
        "tile_url": map_id_dict['tile_fetcher'].url_format
    }