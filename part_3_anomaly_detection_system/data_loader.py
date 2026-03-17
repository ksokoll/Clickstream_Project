import pandas as pd
from pathlib import Path
from datetime import date
from config import Settings

class DataLoader:
    """Loads and filters parquet data"""
    
    def __init__(self):
        self.parquet_dir = Settings.parquet_dir
    
    def load_all(self) -> pd.DataFrame:
        """Load all parquet files"""
        parquet_files = list(self.parquet_dir.glob('*.parquet'))
        
        if not parquet_files:
            raise FileNotFoundError(f"No parquet files in {self.parquet_dir}")
        
        dfs = []
        for file_path in parquet_files:
            df = pd.read_parquet(file_path)
            dfs.append(df)
        
        combined_df = pd.concat(dfs, ignore_index=True)
        
        # Convert Arrow strings to native Python strings
        string_cols = combined_df.select_dtypes(include=['object', 'string']).columns
        for col in string_cols:
            combined_df[col] = combined_df[col].astype(str)
        
        print(f"✅ Loaded {len(combined_df):,} events from {len(parquet_files)} files")
        
        return combined_df
    
    def load_before(self, target_date: date) -> pd.DataFrame:
        """Load events before target_date (exclusive)"""
        df = self.load_all()
        df['date'] = pd.to_datetime(df['timestamp_readable']).dt.date
        df = df[df['date'] < target_date]
        
        print(f"✅ Loaded {len(df):,} events before {target_date}")
        
        return df
    
    def load_for_date(self, target_date: date) -> pd.DataFrame:
        """Load events for specific date only"""
        df = self.load_all()
        df['date'] = pd.to_datetime(df['timestamp_readable']).dt.date
        df = df[df['date'] == target_date]
        
        print(f"✅ Loaded {len(df):,} events for {target_date}")
        
        return df