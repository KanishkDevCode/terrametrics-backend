from fastapi import APIRouter
from pydantic import BaseModel
from app.services.economic_model import calculate_infrastructure_depreciation

router = APIRouter()

# Schema for the data coming from the frontend or other internal services
class EconomicMetricsInput(BaseModel):
    urban_growth_rate: float
    forest_loss_sq_km: float
    road_damage_count: int

@router.post("/infrastructure-depreciation", tags=["Economics"])
async def get_depreciation_costs(data: EconomicMetricsInput):
    """
    Analyzes indicators to estimate municipal maintenance costs.
    """
    analysis = calculate_infrastructure_depreciation(
        urban_growth_rate=data.urban_growth_rate,
        forest_loss_sq_km=data.forest_loss_sq_km,
        road_damage_count=data.road_damage_count
    )
    
    return {
        "status": "success",
        "data": analysis
    }