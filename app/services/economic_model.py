from typing import Dict

def calculate_infrastructure_depreciation(
    urban_growth_rate: float, 
    forest_loss_sq_km: float, 
    road_damage_count: int
) -> Dict:
    """
    Calculates the estimated infrastructure maintenance cost based on environmental 
    and structural degradation metrics.
    """
    
    # Define baseline cost coefficients (These can be adjusted based on real municipal data)
    # alpha: Cost per 1% of urban growth (e.g., ₹5,000,000 for new drainage/utilities)
    ALPHA_COST = 5000000  
    
    # beta: Cost per sq km of forest loss (e.g., ₹2,000,000 for flood mitigation/runoff management)
    BETA_COST = 2000000   
    
    # gamma: Cost per detected pothole/anomaly (e.g., ₹15,000 for road patching)
    GAMMA_COST = 15000    

    # Calculate individual factor costs
    cost_urban_growth = (urban_growth_rate * 100) * ALPHA_COST
    cost_forest_loss = forest_loss_sq_km * BETA_COST
    cost_road_damage = road_damage_count * GAMMA_COST

    # Total estimated infrastructure deficit
    total_estimated_cost = cost_urban_growth + cost_forest_loss + cost_road_damage

    # Format into readable strings for the dashboard (e.g., "₹2.34 Crore")
    def format_crores(amount: float) -> str:
        crores = amount / 10000000
        return f"₹{round(crores, 2)} Crore"

    return {
        "raw_cost_inr": total_estimated_cost,
        "formatted_total_cost": format_crores(total_estimated_cost),
        "breakdown": {
            "urban_growth_impact": format_crores(cost_urban_growth),
            "forest_loss_impact": format_crores(cost_forest_loss),
            "road_damage_impact": format_crores(cost_road_damage)
        }
    }