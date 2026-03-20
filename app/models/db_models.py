from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
from app.database.postgres import Base

class RoadCondition(Base):
    __tablename__ = "road_conditions"

    id = Column(Integer, primary_key=True, index=True)
    # Store the exact spatial point using PostGIS Geometry type (SRID 4326 is standard GPS coordinates)
    location = Column(Geometry('POINT', srid=4326), nullable=False)
    severity_score = Column(Float, nullable=False)
    vibration_magnitude = Column(Float)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class LandCover(Base):
    __tablename__ = "land_cover_stats"

    id = Column(Integer, primary_key=True, index=True)
    city_name = Column(String, index=True)
    year = Column(Integer, nullable=False)
    urban_area_sq_km = Column(Float, nullable=False)
    forest_area_sq_km = Column(Float)