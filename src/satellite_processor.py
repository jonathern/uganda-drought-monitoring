"""Process satellite imagery and calculate vegetation indices."""

import numpy as np
import pandas as pd
import geopandas as gpd
from pathlib import Path
from tqdm import tqdm
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from config import RAW_DATA_DIR, PROCESSED_DATA_DIR, STUDY_AREA

class SatelliteProcessor:
    """Process MODIS data and calculate derived indices."""
    
    def __init__(self):
        self.raw_dir = RAW_DATA_DIR / "modis"
        self.processed_dir = PROCESSED_DATA_DIR
        self.processed_dir.mkdir(exist_ok=True)
        
    def load_boundaries(self):
        """Load administrative boundaries."""
        boundary_file = RAW_DATA_DIR / "uganda_districts.geojson"
        return gpd.read_file(boundary_file)
    
    def process_ndvi_files(self):
        """Process all NDVI files."""
        print("Processing NDVI files...")
        
        ndvi_files = sorted(self.raw_dir.glob("MODIS_NDVI_*.csv"))
        
        if not ndvi_files:
            print("  No NDVI files found!")
            return None
        
        all_data = []
        
        for file in tqdm(ndvi_files, desc="  Processing"):
            df = pd.read_csv(file)
            df['date'] = pd.to_datetime(df['date'])
            all_data.append(df)
        
        # Combine all data
        combined = pd.concat(all_data, ignore_index=True)
        
        # Convert to GeoDataFrame
        gdf = gpd.GeoDataFrame(
            combined,
            geometry=gpd.points_from_xy(combined.lon, combined.lat),
            crs='EPSG:4326'
        )
        
        # Save processed data
        output_file = self.processed_dir / "ndvi_timeseries.parquet"
        gdf.to_parquet(output_file)
        
        print(f"  Processed {len(ndvi_files)} files")
        print(f"  Total pixels: {len(gdf):,}")
        print(f"  Date range: {gdf['date'].min()} to {gdf['date'].max()}")
        
        return gdf
    
    def calculate_district_statistics(self, ndvi_gdf):
        """Calculate district-level NDVI statistics."""
        print("\nCalculating district statistics...")
        
        boundaries = self.load_boundaries()
        
        # Spatial join
        joined = gpd.sjoin(
            ndvi_gdf,
            boundaries[['NAME_2', 'geometry']],
            how='left',
            predicate='within'
        )
        
        # Group by district and date
        stats = joined.groupby(['NAME_2', 'date']).agg({
            'ndvi': ['mean', 'std', 'min', 'max', 'count']
        }).reset_index()
        
        stats.columns = ['district', 'date', 'ndvi_mean', 'ndvi_std', 
                        'ndvi_min', 'ndvi_max', 'pixel_count']
        
        # Save
        output_file = self.processed_dir / "district_ndvi_stats.csv"
        stats.to_csv(output_file, index=False)
        
        print(f"  Districts processed: {stats['district'].nunique()}")
        print(f"  Saved to: {output_file}")
        
        return stats
    
    def calculate_ndvi_anomaly(self, stats_df):
        """Calculate NDVI anomalies from long-term mean."""
        print("\nCalculating NDVI anomalies...")
        
        # Calculate climatology (long-term mean by month)
        stats_df['month'] = pd.to_datetime(stats_df['date']).dt.month
        
        climatology = stats_df.groupby(['district', 'month'])['ndvi_mean'].mean()
        climatology = climatology.reset_index()
        climatology.columns = ['district', 'month', 'ndvi_climatology']
        
        # Merge and calculate anomaly
        stats_df = stats_df.merge(climatology, on=['district', 'month'])
        stats_df['ndvi_anomaly'] = stats_df['ndvi_mean'] - stats_df['ndvi_climatology']
        
        # Save
        output_file = self.processed_dir / "ndvi_anomalies.csv"
        stats_df.to_csv(output_file, index=False)
        
        print(f"  Saved to: {output_file}")
        
        return stats_df
    
    def run_all(self):
        """Execute all processing steps."""
        print("\n")
        print("SATELLITE DATA PROCESSING")
        print("_"*60)
        
        # Process NDVI
        ndvi_gdf = self.process_ndvi_files()
        
        if ndvi_gdf is not None:
            # Calculate district statistics
            stats = self.calculate_district_statistics(ndvi_gdf)
            
            # Calculate anomalies
            stats_with_anomalies = self.calculate_ndvi_anomaly(stats)
        
        print("\nSatellite processing complete!")


if __name__ == "__main__":
    processor = SatelliteProcessor()
    processor.run_all()