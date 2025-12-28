"""Calculate drought indices (VCI, TCI, VHI)."""

import numpy as np
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

from config import PROCESSED_DATA_DIR, DROUGHT_THRESHOLDS


class DroughtIndices:
    """Calculate vegetation and temperature condition indices."""
    
    def __init__(self):
        self.processed_dir = PROCESSED_DATA_DIR
        
    def load_data(self):
        """Load processed NDVI and climate data."""
        print("Loading processed data...")
        
        # NDVI data
        ndvi_file = self.processed_dir / "district_ndvi_stats.csv"
        ndvi_df = pd.read_csv(ndvi_file)
        ndvi_df['date'] = pd.to_datetime(ndvi_df['date'])
        
        # Climate data
        climate_file = PROCESSED_DATA_DIR.parent / "data" / "raw" / "climate" / "climate_data.csv"
        climate_df = pd.read_csv(climate_file)
        climate_df['date'] = pd.to_datetime(climate_df['date'])
        
        # Resample climate data to monthly
        climate_monthly = climate_df.set_index('date').resample('MS').agg({
            'precipitation': 'sum',
            'temperature': 'mean'
        }).reset_index()
        
        print(f"  NDVI records: {len(ndvi_df):,}")
        print(f"  Climate records: {len(climate_monthly):,}")
        
        return ndvi_df, climate_monthly
    
    def calculate_vci(self, ndvi_df):
        """
        Calculate Vegetation Condition Index (VCI).
        VCI = 100 * (NDVI - NDVI_min) / (NDVI_max - NDVI_min)
        """
        print("\nCalculating VCI (Vegetation Condition Index)...")
        
        # Calculate min/max NDVI for each district across all time
        ndvi_stats = ndvi_df.groupby('district')['ndvi_mean'].agg(['min', 'max'])
        ndvi_stats.columns = ['ndvi_absolute_min', 'ndvi_absolute_max']
        
        # Merge back
        df = ndvi_df.merge(ndvi_stats, on='district')
        
        # Calculate VCI
        df['VCI'] = 100 * (
            (df['ndvi_mean'] - df['ndvi_absolute_min']) / 
            (df['ndvi_absolute_max'] - df['ndvi_absolute_min'])
        )
        
        # Classify drought severity
        df['drought_category'] = pd.cut(
            df['VCI'],
            bins=[0, 10, 20, 30, 40, 100],
            labels=['Extreme', 'Severe', 'Moderate', 'Mild', 'Normal']
        )
        
        print(f"  VCI range: {df['VCI'].min():.1f} - {df['VCI'].max():.1f}")
        
        return df
    
    def calculate_tci(self, climate_df):
        """
        Calculate Temperature Condition Index (TCI).
        TCI = 100 * (T_max - T) / (T_max - T_min)
        """
        print("\nCalculating TCI (Temperature Condition Index)...")
        
        # Calculate temperature extremes
        t_min = climate_df['temperature'].min()
        t_max = climate_df['temperature'].max()
        
        # Calculate TCI (inverted - high temp = stress)
        climate_df['TCI'] = 100 * (
            (t_max - climate_df['temperature']) / (t_max - t_min)
        )
        
        print(f"  TCI range: {climate_df['TCI'].min():.1f} - {climate_df['TCI'].max():.1f}")
        
        return climate_df
    
    def calculate_vhi(self, vci_df, tci_df):
        """
        Calculate Vegetation Health Index (VHI).
        VHI = α * VCI + (1-α) * TCI
        where α = 0.5 (equal weighting)
        """
        print("\nCalculating VHI (Vegetation Health Index)...")
        
        # Merge VCI and TCI data
        vci_df['year_month'] = vci_df['date'].dt.to_period('M')
        tci_df['year_month'] = tci_df['date'].dt.to_period('M')
        
        # Aggregate TCI to monthly
        tci_monthly = tci_df.groupby('year_month')['TCI'].mean().reset_index()
        
        # Merge
        vhi_df = vci_df.merge(tci_monthly, on='year_month', how='left')
        
        # Calculate VHI (equal weights)
        alpha = 0.5
        vhi_df['VHI'] = alpha * vhi_df['VCI'] + (1 - alpha) * vhi_df['TCI']
        
        # Classify drought severity based on VHI
        vhi_df['vhi_drought_category'] = pd.cut(
            vhi_df['VHI'],
            bins=[0, 10, 20, 30, 40, 100],
            labels=['Extreme', 'Severe', 'Moderate', 'Mild', 'Normal']
        )
        
        print(f"  VHI range: {vhi_df['VHI'].min():.1f} - {vhi_df['VHI'].max():.1f}")
        
        return vhi_df
    
    def save_indices(self, indices_df):
        """Save calculated indices."""
        output_file = self.processed_dir / "drought_indices.csv"
        
        # Select relevant columns
        output_cols = [
            'district', 'date', 'ndvi_mean', 'VCI', 'TCI', 'VHI',
            'drought_category', 'vhi_drought_category'
        ]
        
        indices_df[output_cols].to_csv(output_file, index=False)
        print(f"\nSaved indices to: {output_file}")
        
        # Summary statistics
        print("\nDrought Index Summary:")
        print(indices_df[['VCI', 'TCI', 'VHI']].describe())
        
        # Drought occurrence
        print("\nDrought Category Distribution:")
        print(indices_df['vhi_drought_category'].value_counts(normalize=True) * 100)
    
    def run_all(self):
        """Execute all drought index calculations."""
        print("\n")
        print("DROUGHT INDICES CALCULATION")
        print("-"*60)
        
        # Load data
        ndvi_df, climate_df = self.load_data()
        
        # Calculate VCI
        vci_df = self.calculate_vci(ndvi_df)
        
        # Calculate TCI
        tci_df = self.calculate_tci(climate_df)
        
        # Calculate VHI
        vhi_df = self.calculate_vhi(vci_df, tci_df)
        
        # Save results
        self.save_indices(vhi_df)
        
        print("\nDrought indices calculation complete!")


if __name__ == "__main__":
    calculator = DroughtIndices()
    calculator.run_all()