import pandas as pd
from datetime import date
from config import Settings
from data_loader import DataLoader
from processors.conversion_calculator import ConversionCalculator
from processors.baseline_calculator import BaselineCalculator
from processors.anomaly_detector import AnomalyDetector
from models import DailyCheckResult

class AnomalyDetectionPipeline:
    """Orchestrates daily anomaly detection workflow"""
    
    def __init__(self):
        print("\n🔍 Initializing Anomaly Detection Pipeline...\n")
        
        self.data_loader = DataLoader()
        self.conv_calculator = ConversionCalculator()
        self.baseline_calculator = BaselineCalculator(weeks=Settings.baseline_weeks)
        self.anomaly_detector = AnomalyDetector(sigma_threshold=Settings.sigma_threshold)
    
    def process(self, target_date: date) -> DailyCheckResult:
        """Run anomaly detection for target date"""
        
        print(f"\n--- Starting pipeline for {target_date} ---\n")
        
        # Step 1: Load historical data
        historical_df = self.data_loader.load_before(target_date)
        
        # Step 2: Calculate historical conversions
        historical_daily = self.conv_calculator.calculate_daily(
            historical_df,
            Settings.browser,
            Settings.os,
            Settings.device
        )
        
        if len(historical_daily) < Settings.baseline_weeks * 7:
            return DailyCheckResult(
                date=target_date,
                status="INSUFFICIENT_DATA",
                alert_level="NONE",
                anomaly=None,
                consecutive=None
            )
        
        # Step 3: Load new events for target date
        new_events = self.data_loader.load_for_date(target_date)
        
        # Step 4: Calculate conversion for target date
        new_conversion = self.conv_calculator.calculate_for_single_day(
            new_events,
            Settings.browser,
            Settings.os,
            Settings.device
        )
        
        if new_conversion is None:
            return DailyCheckResult(
                date=target_date,
                status="NO_DATA",
                alert_level="NONE",
                anomaly=None,
                consecutive=None
            )
        
        # Step 5: Get baseline for target date's weekday
        baseline, sigma = self.baseline_calculator.get_baseline_for_date(
            historical_daily,
            target_date
        )
        
        # Step 6: Detect anomaly
        anomaly_result = self.anomaly_detector.detect(
            conversion_rate=new_conversion.conversion_rate,
            baseline=baseline,
            sigma=sigma,
            views=new_conversion.views,
            transactions=new_conversion.transactions,
            target_date=target_date
        )
        
        # Step 7: Check consecutive streak
        # Build full dataset including today
        historical_with_baseline = self.baseline_calculator.calculate(historical_daily)
        
        # Add today's result
        today_df = pd.DataFrame([{
            'date': pd.Timestamp(target_date),
            'conversion_rate': new_conversion.conversion_rate,
            'baseline': baseline,
            'sigma': sigma,
            'is_anomaly': anomaly_result.is_anomaly
        }])
        
        all_data = pd.concat([historical_with_baseline, today_df], ignore_index=True)
        
        consecutive = self.anomaly_detector.check_consecutive(
            all_data,
            target_date,
            Settings.consecutive_days
        )
        
        # Determine status and alert level
        if consecutive.is_critical:
            status = "CRITICAL"
            alert_level = "HIGH"
        elif anomaly_result.is_anomaly:
            status = "ANOMALY"
            alert_level = "MEDIUM"
        else:
            status = "OK"
            alert_level = "NONE"
        
        print("Pipeline completed.\n")
        
        return DailyCheckResult(
            date=target_date,
            status=status,
            alert_level=alert_level,
            anomaly=anomaly_result,
            consecutive=consecutive
        )