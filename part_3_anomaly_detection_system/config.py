from pathlib import Path

class Settings:
    """Configuration settings for anomaly detection"""
    
    # Data paths
    parquet_dir = Path("data/parquet_output")
    output_dir = Path("data/outputs")
    
    # Filter criteria
    browser = "safari"
    os = "ios"
    device = "mobile"
    
    # Detection parameters
    sigma_threshold = 2
    consecutive_days = 3
    baseline_weeks = 4