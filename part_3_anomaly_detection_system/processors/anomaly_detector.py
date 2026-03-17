import pandas as pd
from datetime import timedelta, date
from models import AnomalyResult, ConsecutiveStreak

class AnomalyDetector:
    """Detects anomalies using statistical thresholds"""
    
    def __init__(self, sigma_threshold: int = 2):
        self.sigma_threshold = sigma_threshold
    
    def detect(
        self,
        conversion_rate: float,
        baseline: float,
        sigma: float,
        views: int,
        transactions: int,
        target_date: date
    ) -> AnomalyResult:
        """Check if conversion rate is anomalous"""
        
        # Calculate threshold
        threshold = max(baseline - (self.sigma_threshold * sigma), 0)
        
        # Check anomaly
        is_anomaly = conversion_rate <= threshold
        
        # Calculate deviation
        deviation_sigma = (conversion_rate - baseline) / sigma if sigma > 0 else 0
        
        return AnomalyResult(
            date=target_date,
            conversion_rate=conversion_rate,
            baseline=baseline,
            sigma=sigma,
            threshold=threshold,
            is_anomaly=is_anomaly,
            deviation_sigma=deviation_sigma,
            views=views,
            transactions=transactions
        )
    
    def check_consecutive(
        self,
        anomalies_df: pd.DataFrame,
        target_date: date,
        days: int = 3
    ) -> ConsecutiveStreak:
        """Check if target_date is part of consecutive anomaly streak"""
        
            # Convert to pandas Timestamp for comparison
        start_date_ts = pd.Timestamp(target_date - timedelta(days=days-1))
        target_date_ts = pd.Timestamp(target_date)
        
        recent = anomalies_df[
            (anomalies_df['date'] >= start_date_ts) &
            (anomalies_df['date'] <= target_date_ts)
        ].sort_values('date')
        
        if len(recent) < days:
            return ConsecutiveStreak(is_critical=False)
        
        if recent['is_anomaly'].all():
            return ConsecutiveStreak(
                is_critical=True,
                streak_start=recent.iloc[0]['date'],
                streak_end=recent.iloc[-1]['date'],
                streak_length=len(recent)
            )
        
        return ConsecutiveStreak(is_critical=False)