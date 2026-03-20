import math
from typing import Dict

def detect_anomaly(acc_x: float, acc_y: float, acc_z: float, speed: float = None) -> Dict:
    """
    Analyzes 3-axis accelerometer data to detect pavement irregularities.
    """
    # Calculate the resultant vibration vector magnitude
    vibration_magnitude = math.sqrt(acc_x**2 + acc_y**2 + acc_z**2)
    
    # Baseline gravity is ~9.81 m/s^2. 
    # A threshold of 14.0 or higher typically indicates a severe jolt (pothole).
    THRESHOLD = 14.0 
    
    is_anomaly = vibration_magnitude > THRESHOLD
    
    # Calculate a normalized severity score between 0.0 and 1.0 for the frontend heatmap
    severity = 0.0
    if is_anomaly:
        # Scale severity based on how far past the baseline gravity it spiked
        severity = min(1.0, (vibration_magnitude - 9.8) / 10.0)
        
    return {
        "vibration_magnitude": round(vibration_magnitude, 2),
        "is_anomaly": is_anomaly,
        "severity_score": round(severity, 2)
    }