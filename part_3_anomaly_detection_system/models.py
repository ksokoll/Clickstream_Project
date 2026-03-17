from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional

class DailyConversion(BaseModel):
    """Daily conversion metrics"""
    date: date
    views: int
    transactions: int
    conversion_rate: float

class BaselineMetrics(BaseModel):
    """Baseline and sigma for anomaly detection"""
    date: date
    baseline: float
    sigma: float
    weekday: int

class AnomalyResult(BaseModel):
    """Result from anomaly detection"""
    date: date
    conversion_rate: float
    baseline: float
    sigma: float
    threshold: float
    is_anomaly: bool
    deviation_sigma: float
    views: int
    transactions: int

class ConsecutiveStreak(BaseModel):
    """Consecutive anomaly streak information"""
    is_critical: bool
    streak_start: Optional[date] = None
    streak_end: Optional[date] = None
    streak_length: Optional[int] = None

class DailyCheckResult(BaseModel):
    """Final result from daily check pipeline"""
    date: date
    status: str  # OK, ANOMALY, CRITICAL, NO_DATA, INSUFFICIENT_DATA
    alert_level: str  # NONE, MEDIUM, HIGH
    anomaly: Optional[AnomalyResult] = None  # ← Optional!
    consecutive: Optional[ConsecutiveStreak] = None  # ← Optional!