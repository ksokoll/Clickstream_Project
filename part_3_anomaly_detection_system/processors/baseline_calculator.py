import pandas as pd
import numpy as np
from datetime import timedelta

class BaselineCalculator:
    """Calculates baseline using Median + MAD"""
    
    def __init__(self, weeks: int = 4):
        self.weeks = weeks
    
    def calculate(self, daily_data: pd.DataFrame) -> pd.DataFrame:
        """Calculate baseline and sigma for each day using same-weekday median + MAD"""
        
        print(f"📈 Calculating baseline (last {self.weeks} weeks, same weekday, MAD)...")
        
        daily_data = daily_data.copy()
        daily_data['date'] = pd.to_datetime(daily_data['date'])
        daily_data['weekday'] = daily_data['date'].dt.weekday
        daily_data = daily_data.sort_values('date').reset_index(drop=True)
        
        baselines = []
        sigmas = []
        
        for idx, row in daily_data.iterrows():
            current_date = row['date']
            current_weekday = row['weekday']
            
            # Get same weekdays from last N weeks
            lookback_start = current_date - pd.Timedelta(days=self.weeks*7)
            
            same_weekdays = daily_data[
                (daily_data['weekday'] == current_weekday) &
                (daily_data['date'] < current_date) &
                (daily_data['date'] >= lookback_start)
            ]
            
            if len(same_weekdays) >= 2:
                # Use Median + MAD
                baseline = same_weekdays['conversion_rate'].median()
                mad = (same_weekdays['conversion_rate'] - baseline).abs().median()
                sigma = mad * 1.4826  # Scale to match StdDev
            else:
                # Fallback: overall stats
                baseline = daily_data['conversion_rate'].median()
                sigma = daily_data['conversion_rate'].std()
            
            baselines.append(baseline)
            sigmas.append(sigma)
        
        daily_data['baseline'] = baselines
        daily_data['sigma'] = sigmas
        
        print(f"   ✅ Calculated baselines for {len(daily_data)} days")
        
        return daily_data
    
    def get_baseline_for_date(
        self,
        historical_data: pd.DataFrame,
        target_date
    ) -> tuple[float, float]:
        """Get baseline and sigma for specific date's weekday"""
        
        historical_data = historical_data.copy()
        historical_data['date'] = pd.to_datetime(historical_data['date'])
        
        # Get weekday of target
        weekday = pd.to_datetime(target_date).weekday()
        
        # Get last N same weekdays
        same_weekdays = historical_data[
            historical_data['date'].dt.weekday == weekday
        ].tail(self.weeks)
        
        if len(same_weekdays) < 2:
            raise ValueError(f"Not enough historical data for weekday {weekday}")
        
        # Calculate baseline and sigma
        baseline = same_weekdays['conversion_rate'].median()
        mad = (same_weekdays['conversion_rate'] - baseline).abs().median()
        sigma = mad * 1.4826
        
        return float(baseline), float(sigma)