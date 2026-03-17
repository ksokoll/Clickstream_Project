import pandas as pd
from models import DailyConversion
from typing import Optional

class ConversionCalculator:
    """Calculates conversion rates from event data"""
    
    def calculate_daily(
        self, 
        df: pd.DataFrame, 
        browser: str, 
        os: str, 
        device: str
    ) -> pd.DataFrame:
        """Calculate daily conversion rates for browser/OS/device combination"""
        
        # Filter for specific combination
        filtered = df[
            (df['browser'] == browser) &
            (df['os'] == os) &
            (df['device'] == device)
        ].copy()  
        
        print(f"   Filtered to {len(filtered):,} events")
        
        # Check if we have data
        if len(filtered) == 0:
            print("   ⚠️  No events found for this combination")
            return pd.DataFrame()
        
        # Extract date - jetzt sicher weil wir .copy() haben
        filtered['date'] = pd.to_datetime(filtered['timestamp_readable']).dt.date
        
        # Count views and transactions per day
        views_per_day = filtered[filtered['event'] == 'view'].groupby('date').size()
        trans_per_day = filtered[filtered['event'] == 'transaction'].groupby('date').size()
        
        # Combine into DataFrame
        daily = pd.DataFrame({
            'views': views_per_day,
            'transactions': trans_per_day
        }).fillna(0).reset_index()
        
        # Calculate conversion rate
        daily['conversion_rate'] = (
            daily['transactions'] / daily['views'].replace(0, 1)
        ) * 100
        
        print(f"   ✅ Calculated conversion for {len(daily)} days")
        
        return daily
        
    def calculate_for_single_day(
        self,
        df: pd.DataFrame,
        browser: str,
        os: str,
        device: str
    ) -> Optional[DailyConversion]:
        """Calculate conversion for single day's events"""
        
        filtered = df[
            (df['browser'] == browser) &
            (df['os'] == os) &
            (df['device'] == device)
        ].copy()
        
        if len(filtered) == 0:
            return None
        
        views = (filtered['event'] == 'view').sum()
        transactions = (filtered['event'] == 'transaction').sum()
        
        if views == 0:
            return None
        
        conversion_rate = (transactions / views) * 100
        
        # Get date from first event
        target_date = pd.to_datetime(filtered.iloc[0]['timestamp_readable']).date()
        
        return DailyConversion(
            date=target_date,
            views=int(views),
            transactions=int(transactions),
            conversion_rate=float(conversion_rate)
        )