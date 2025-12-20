"""Data acquisition module for satellite and climate data."""

import os
from pathlib import Path
from datetime import datetime, timedelta
import requests
import geopandas as gpd
import pandas as pd
import numpy as np
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

from config import (
    RAW_DATA_DIR, STUDY_AREA, TIME_PERIOD, 
    MODIS_CONFIG, CLIMATE_CONFIG
)