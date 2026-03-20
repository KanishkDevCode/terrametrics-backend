from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.schemas import SensorDataInput
from app.services.pothole_detection import detect_anomaly
from app.database.postgres import get_db
from app.models.db_models import RoadCondition
from pydantic import BaseModel

# Stores the live position of our ghost vehicle
live_vehicle_state = {"lat": 30.3244, "lon": 78.0339}

router = APIRouter()

class ManualReportInput(BaseModel):
    lat: float
    lon: float
    severity_score: float = 85.0 # High severity since a human is manually reporting it
    notes: str = "Manual Crowdsourced Report"


@router.post("/sensor-data", tags=["Telematics"])
async def process_sensor_data(data: SensorDataInput, db: Session = Depends(get_db)):
    # UPDATE THE LIVE TRACKER
    live_vehicle_state["lat"] = data.lat
    live_vehicle_state["lon"] = data.lon
    """
    Ingests live sensor data, runs anomaly detection, and stores potholes in Supabase.
    """
    analysis = detect_anomaly(data.acc_x, data.acc_y, data.acc_z, data.speed)
    
    # If the ML service flags a pothole, save it to PostgreSQL
    if analysis["is_anomaly"]:
        new_anomaly = RoadCondition(
            # Format the coordinates as a Well-Known Text (WKT) string for PostGIS
            location=f"SRID=4326;POINT({data.lon} {data.lat})", 
            severity_score=analysis["severity_score"],
            vibration_magnitude=analysis["vibration_magnitude"]
        )
        db.add(new_anomaly)
        db.commit()
        
    return {
        "status": "processed",
        "analysis": analysis,
        "database_insert": analysis["is_anomaly"]
    }

@router.get("/pothole-heatmap", tags=["Telematics"])
async def get_heatmap(db: Session = Depends(get_db)):
    """
    Queries Supabase and returns infrastructure damage in GeoJSON format.
    """
    # Use PostGIS functions ST_X and ST_Y to extract the longitude and latitude back out
    anomalies = db.query(
        RoadCondition.severity_score,
        func.ST_X(RoadCondition.location).label('lon'),
        func.ST_Y(RoadCondition.location).label('lat')
    ).all()

    features = []
    for point in anomalies:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [point.lon, point.lat] 
            },
            "properties": {
                "severity": point.severity_score
            }
        })
        
    return {
        "type": "FeatureCollection",
        "features": features
    }

@router.get("/live-vehicle", tags=["Telematics"])
async def get_live_vehicle():
    """Returns the current real-time GPS location of the active vehicle."""
    return live_vehicle_state

@router.post("/manual-report", tags=["Telematics"])
async def process_manual_report(data: ManualReportInput, db: Session = Depends(get_db)):
    """
    Ingests a manual pothole report from a user's smartphone camera/GPS.
    """
    try:
        new_anomaly = RoadCondition(
            location=f"SRID=4326;POINT({data.lon} {data.lat})", 
            severity_score=data.severity_score,
            vibration_magnitude=0.0 # 0 because it was a camera report, not an accelerometer
        )
        db.add(new_anomaly)
        db.commit()
        
        return {"status": "success", "message": "Manual hazard logged successfully."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))