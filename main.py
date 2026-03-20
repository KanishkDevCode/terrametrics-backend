from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.routes import geospatial, telemetry, economics
import ee
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import httpx
import random

from app.database.postgres import engine
from app.models import db_models
from app.services.scheduler import scheduler

# This generates the tables in Supabase based on your db_models
db_models.Base.metadata.create_all(bind=engine)

# Initialize Earth Engine
try:
    ee.Initialize(project="terrametrics-project")
    print("✅ Earth Engine initialized successfully.")
except Exception as e:
    print("❌ Earth Engine initialization failed:", e)

# --- THE NEW INTERNAL SIMULATOR ---
async def run_traffic_simulator():
    """Simulates a vehicle continuously patrolling up and down Rajpur Road."""
    print("🚗 Internal Ghost Vehicle Simulator automatically started...")
    
    # PERFECTLY MAPPED TO RAJPUR ROAD (Clock Tower to Rajpur)
    rajpur_waypoints = [
        (30.3245, 78.0416), (30.3275, 78.0435), (30.3300, 78.0456),
        (30.3335, 78.0483), (30.3365, 78.0505), (30.3385, 78.0515),
        (30.3420, 78.0535), (30.3460, 78.0558), (30.3495, 78.0583),
        (30.3520, 78.0601), (30.3550, 78.0620), (30.3585, 78.0645),
        (30.3620, 78.0665), (30.3660, 78.0685), (30.3700, 78.0705),
        (30.3750, 78.0725), (30.3800, 78.0750)
    ]
    
    # Create the infinite patrol loop (Drive UP, then turn around and drive DOWN)
    patrol_route = rajpur_waypoints + rajpur_waypoints[::-1]

    async with httpx.AsyncClient() as client:
        while True:
            # Drive point-to-point along the physical road
            for i in range(len(patrol_route) - 1):
                start_lat, start_lon = patrol_route[i]
                end_lat, end_lon = patrol_route[i+1]

                # Take 4 smooth steps between each physical road curve
                steps = 4
                for step in range(steps):
                    current_lat = start_lat + (end_lat - start_lat) * (step / steps)
                    current_lon = start_lon + (end_lon - start_lon) * (step / steps)

                    # 10% chance of hitting a pothole
                    is_pothole = random.random() < 0.10
                    z_axis = random.uniform(15.1, 25.0) if is_pothole else random.uniform(8.0, 11.0)

                    payload = {
                        "lat": current_lat,
                        "lon": current_lon,
                        "acc_x": random.uniform(-2.0, 2.0),
                        "acc_y": random.uniform(-2.0, 2.0),
                        "acc_z": z_axis,
                        "speed": random.uniform(30.0, 50.0)
                    }

                    try:
                        # THE FIX 1: Point the simulator to the LIVE Render database!
                        await client.post("https://terrametrics-api.onrender.com/api/v1/telemetry/sensor-data", json=payload)
                    except Exception:
                        pass
                    
                    await asyncio.sleep(1.5)


# Define the startup and shutdown events for the background jobs
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    print("🚀 Starting TerraMetrics Background Tasks...")
    scheduler.start()
    
    # Start the traffic simulator as an async background task
    simulator_task = asyncio.create_task(run_traffic_simulator())
    
    yield
    
    # --- Shutdown ---
    print("🛑 Shutting down tasks...")
    scheduler.shutdown()
    simulator_task.cancel()

# Initialize the application
app = FastAPI(
    title="TerraMetrics API",
    description="Backend engine for urban infrastructure monitoring and economic analytics.",
    version="1.0.0",
    lifespan=lifespan  
)

# THE FIX 2: Allow all origins so Vercel and Localhost both work seamlessly
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"], 
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
# Option 1: Explicit Origins (Safe and allows credentials)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5174",            # Your local Vite/React frontend
        "https://terrametrics-frontend.vercel.app"   # Add your production frontend URL here
    ], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Include modular routers
app.include_router(geospatial.router, prefix="/api/v1/geo")
app.include_router(telemetry.router, prefix="/api/v1/telemetry")
app.include_router(economics.router, prefix="/api/v1/eco")

# Health check endpoint
@app.get("/", tags=["Health"])
async def health_check():
    return {
        "system_status": "Operational",
        "platform": "TerraMetrics API"
    }
