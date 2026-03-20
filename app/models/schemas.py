from pydantic import BaseModel
from typing import Optional

# Schema for the Telematics Dashboard (Phase B)
class SensorDataInput(BaseModel):
    lat: float
    lon: float
    acc_x: float
    acc_y: float
    acc_z: float
    speed: Optional[float] = None
    
# Schema for Economic Analytics (Phase C)
class EconomicImpactResponse(BaseModel):
    estimated_cost_inr: float
    urban_growth_factor: float
    forest_loss_factor: float