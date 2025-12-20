"""Configuration settings for the drought monitoring system."""

import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

# Make sure directories exist
for directory in [RAW_DATA_DIR, PROCESSED_DATA_DIR, OUTPUTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
    
# Study area configuration (Northern Uganda)
STUDY_AREA = {
    "name": "Northern Uganda",
    "districts": ["Gulu", "Kitgum", "Lira", "Pader", "Alebtong"],
    "bbox": {
        "min_lon": 31.5,
        "max_lon": 34.0,
        "min_lat": 2.0,
        "max_lat": 4.0
    },
    "epsg": 32636  # UTM Zone 36N
}

# Time period for analysis
TIME_PERIOD = {
    "start_date": "2020-01-01",
    "end_date": "2023-12-31"
}