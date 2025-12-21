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

class DataAcquisition:
    """Handle data download and first level organization."""
    
    def __init__(self):
        self.raw_dir = RAW_DATA_DIR
        self.study_bbox = STUDY_AREA['bbox']
        
    def download_admin_boundaries(self):
        """Download Uganda administrative boundaries from GADM."""
        print("Downloading Uganda administrative boundaries...")
        
        # GADM URL for Uganda (level 2 = districts)
        gadm_url = "https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_UGA_2.json"
        
        output_file = self.raw_dir / "uganda_districts.geojson"
        
        if output_file.exists():
            print(f"  Boundaries already exist: {output_file}")
            return gpd.read_file(output_file)
        
        try:
            gdf = gpd.read_file(gadm_url)
            
            # Filter to study area districts
            if STUDY_AREA['districts']:
                gdf = gdf[gdf['NAME_2'].isin(STUDY_AREA['districts'])]
            
            # Save
            gdf.to_file(output_file, driver='GeoJSON')
            print(f"  Saved to: {output_file}")
            
            return gdf
            
        except Exception as e:
            print(f"  Error downloading boundaries: {e}")
            return None
    
    def generate_sample_modis_data(self):
        """Generate sample MODIS-like NDVI data for demonstration."""
        print("Generating sample MODIS NDVI data...")
        
        # Create monthly data for the study period
        start = pd.to_datetime(TIME_PERIOD['start_date'])
        end = pd.to_datetime(TIME_PERIOD['end_date'])
        dates = pd.date_range(start, end, freq='MS')
        
        # Spatial grid
        lon = np.linspace(
            STUDY_AREA['bbox']['min_lon'],
            STUDY_AREA['bbox']['max_lon'],
            100
        )
        lat = np.linspace(
            STUDY_AREA['bbox']['min_lat'],
            STUDY_AREA['bbox']['max_lat'],
            80
        )
        
        modis_dir = self.raw_dir / "modis"
        modis_dir.mkdir(exist_ok=True)
        
        for date in tqdm(dates, desc="  Generating NDVI scenes"):
            # Simulate seasonal NDVI patterns
            month = date.month
            
            # Base NDVI with seasonal variation
            # Uganda has two rainy seasons: Mar-May and Sep-Nov
            if month in [3, 4, 5, 9, 10, 11]:
                base_ndvi = 0.6
            elif month in [12, 1, 2, 6, 7, 8]:
                base_ndvi = 0.4
            else:
                base_ndvi = 0.5
            
            # Add spatial variation
            lon_grid, lat_grid = np.meshgrid(lon, lat)
            ndvi = base_ndvi + 0.2 * np.sin(lon_grid * 3) * np.cos(lat_grid * 4)
            ndvi += np.random.normal(0, 0.05, ndvi.shape)
            
            # Add some drought areas (lower NDVI)
            if month in [1, 2, 7, 8]:
                drought_mask = (lon_grid > 32.5) & (lat_grid < 3.0)
                ndvi[drought_mask] *= 0.7
            
            # Clip to valid NDVI range
            ndvi = np.clip(ndvi, 0, 1)
            
            # Save as CSV, with coordinates
            data = {
                'lon': lon_grid.flatten(),
                'lat': lat_grid.flatten(),
                'ndvi': ndvi.flatten(),
                'date': date
            }
            df = pd.DataFrame(data)
            
            filename = f"MODIS_NDVI_{date.strftime('%Y%m')}.csv"
            df.to_csv(modis_dir / filename, index=False)
        
        print(f"  Generated {len(dates)} NDVI scenes")
        
    def generate_sample_climate_data(self):
        """Generate sample precipitation and temperature data."""
        print("Generating sample climate data...")
        
        start = pd.to_datetime(TIME_PERIOD['start_date'])
        end = pd.to_datetime(TIME_PERIOD['end_date'])
        dates = pd.date_range(start, end, freq='D')
        
        climate_dir = self.raw_dir / "climate"
        climate_dir.mkdir(exist_ok=True)
        
        # Generate daily data
        data = []
        for date in tqdm(dates, desc="  Generating climate data"):
            month = date.month
            
            # Precipitation (mm/day) - seasonal pattern
            if month in [3, 4, 5, 9, 10, 11]:
                precip = np.random.gamma(2, 3)  # Rainy season
            else:
                precip = np.random.gamma(0.5, 1)  # Dry season
            
            # Temperature (°C) - relatively stable in tropics
            temp = 25 + np.random.normal(0, 2) - 0.5 * (month in [6, 7, 8])
            
            data.append({
                'date': date,
                'precipitation': precip,
                'temperature': temp
            })
        
        df = pd.DataFrame(data)
        df.to_csv(climate_dir / "climate_data.csv", index=False)
        print(f"  Generated climate data: {len(df)} days")
        
    def run_all(self):
        """Execute all data acquisition tasks."""
        
        print("Data Acquisition")
        print("-"*60)
        
        # Download boundaries
        boundaries = self.download_admin_boundaries()
        
        # Generate sample satellite data
        self.generate_sample_modis_data()
        
        # Generate sample climate data
        self.generate_sample_climate_data()
        
        print("\nData acquisition complete!")
        print(f"Data saved to: {self.raw_dir}")
        

if __name__ == "__main__":
    acquirer = DataAcquisition()
    acquirer.run_all()