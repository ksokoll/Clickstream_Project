import pytest
import pandas as pd
from datetime import date
from pathlib import Path
import sys

# ============================================================================
# TEST SUITE INTRODUCTION – Anomaly Detection Pipeline
# ============================================================================
#
# This test module validates the behavior of the AnomalyDetectionPipeline
# end-to-end using **synthetic parquet data** created at test runtime.
#
# The goal of this file is NOT to test individual helper functions in isolation,
# but to verify that the full pipeline:
#
#   - loads event data correctly
#   - computes historical baselines
#   - detects anomalies based on statistical deviation
#   - tracks consecutive anomaly streaks
#   - emits correct status and alert levels
#
# under a variety of realistic and edge-case scenarios.
#
# ============================================================================
# WHY THESE TESTS EXIST
# ============================================================================
#
# The anomaly detection logic is business-critical:
# - False positives cause unnecessary alerts
# - False negatives delay detection of real production issues
#
# Therefore, these tests focus on **behavioral correctness**, not implementation
# details. Each test describes a concrete business scenario with a clearly
# defined expected outcome.
#
# ============================================================================
# TESTING STRATEGY
# ============================================================================
#
# 1. SYNTHETIC DATA ONLY
#    - No dependency on production parquet files
#    - Tests run in CI/CD (GitHub Actions) without external data
#    - Deterministic and reproducible results
#
# 2. TEMPORARY FILE SYSTEM ISOLATION
#    - Each test uses a pytest tmp_path-based parquet directory
#    - Settings.parquet_dir is overridden per test
#    - Automatic cleanup after test execution
#
# 3. FULL PIPELINE EXECUTION
#    - Tests call pipeline.process(date)
#    - This includes:
#        * data loading
#        * filtering by date
#        * baseline computation
#        * anomaly classification
#        * consecutive anomaly evaluation
#
# 4. CLEAR BUSINESS SEMANTICS
#    - Each test corresponds to a real-world scenario:
#        * normal operation
#        * first anomaly
#        * critical multi-day failure
#        * insufficient data
#        * missing data for target date
#
# ============================================================================
# RELATION TO OTHER TESTS
# ============================================================================
#
# - This file contains FAST unit-style tests with synthetic data
# - Integration tests with real production data (slow, optional) live in:
#       tests/integration/
#
# ============================================================================
# IMPORTANT DESIGN PRINCIPLE
# ============================================================================
#
# These tests intentionally assert on:
#   - status strings (OK / ANOMALY / CRITICAL / NO_DATA / INSUFFICIENT_DATA)
#   - alert levels (NONE / MEDIUM / HIGH)
#   - statistical properties (conversion rate, sigma deviation)
#
# This ensures that refactorings of internal logic do not silently change
# externally visible behavior.
#
# ============================================================================

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline import AnomalyDetectionPipeline
from config import Settings
from conftest import create_parquet_file, mock_parquet_dir

class TestAnomalyDetection:
    """Test anomaly detection pipeline with different scenarios"""
    
    def setup_method(self):
        """Setup test environment before each test"""
        # Store original settings
        self.original_parquet_dir = Settings.parquet_dir
    
    def teardown_method(self):
        """Restore settings after each test"""
        Settings.parquet_dir = self.original_parquet_dir
    
    # ========================================================================
    # TEST 1: Normal Period (No Anomaly)
    # ========================================================================
    
    def test_normal_period_no_anomaly(
        self,
        mock_parquet_dir,
        historical_baseline_events,
        normal_events
    ):
        """
        Test Case: Normal Saturday (2015-08-15)
        Expected: No anomaly detected
        """
        # Setup test data
        Settings.parquet_dir = mock_parquet_dir
        
        # Combine historical + normal events
        all_events = pd.concat([historical_baseline_events, normal_events], ignore_index=True)
        
        # Save to parquet
        create_parquet_file(all_events, mock_parquet_dir / "events.parquet")
        
        # Run pipeline
        pipeline = AnomalyDetectionPipeline()
        result = pipeline.process(date(2015, 8, 15))
        
        # Assertions
        assert result.status == "OK", f"Expected OK, got {result.status}"
        assert result.alert_level == "NONE"
        assert result.anomaly.is_anomaly == False
        assert result.consecutive.is_critical == False
        
        # Check conversion rate is normal (~0.8%)
        assert 0.6 <= result.anomaly.conversion_rate <= 1, \
            f"Conversion rate {result.anomaly.conversion_rate}% outside normal range"
        
        # Check baseline is reasonable
        assert 0.3 <= result.anomaly.baseline <= 1, \
            f"Baseline {result.anomaly.baseline}% outside expected range"
        
        # Check deviation is small (within ±2σ)
        assert -2.0 <= result.anomaly.deviation_sigma <= 2.0, \
            f"Deviation {result.anomaly.deviation_sigma}σ too large for normal day"
        
        print(f"\n✅ Test 1 PASSED: Normal period correctly identified")
        print(f"   Conversion: {result.anomaly.conversion_rate:.2f}%")
        print(f"   Baseline: {result.anomaly.baseline:.2f}%")
        print(f"   Deviation: {result.anomaly.deviation_sigma:+.1f}σ")
    
    # ========================================================================
    # TEST 2: Single Anomaly Day
    # ========================================================================
    
    def test_single_anomaly_day(
        self,
        mock_parquet_dir,
        historical_baseline_events,
        single_anomaly_events
    ):
        """
        Test Case: First bug day (2015-09-01)
        Expected: Anomaly detected, but not critical (only 1 day)
        """
        # Setup test data
        Settings.parquet_dir = mock_parquet_dir
        
        # Combine historical + anomaly events
        all_events = pd.concat([historical_baseline_events, single_anomaly_events], ignore_index=True)
        
        # Save to parquet
        create_parquet_file(all_events, mock_parquet_dir / "events.parquet")
        
        # Run pipeline
        pipeline = AnomalyDetectionPipeline()
        result = pipeline.process(date(2015, 9, 1))
        
        # Assertions
        assert result.status == "ANOMALY", f"Expected ANOMALY, got {result.status}"
        assert result.alert_level == "MEDIUM"
        assert result.anomaly.is_anomaly == True
        assert result.consecutive.is_critical == False, \
            "Should not be critical with only 1 anomalous day"
        
        # Check conversion rate is low (~0.4%)
        assert result.anomaly.conversion_rate < 0.5, \
            f"Conversion rate {result.anomaly.conversion_rate}% too high for anomaly"
        
        # Check it's below threshold
        assert result.anomaly.conversion_rate <= result.anomaly.threshold, \
            "Anomaly conversion should be below threshold"
        
        # Check deviation is significant (< -2σ)
        assert result.anomaly.deviation_sigma < -2.0, \
            f"Deviation {result.anomaly.deviation_sigma}σ not significant enough"
        
        print(f"\n✅ Test 2 PASSED: Single anomaly correctly detected")
        print(f"   Conversion: {result.anomaly.conversion_rate:.2f}%")
        print(f"   Threshold: {result.anomaly.threshold:.2f}%")
        print(f"   Deviation: {result.anomaly.deviation_sigma:+.1f}σ")
    
    # ========================================================================
    # TEST 3: Critical Period (3+ Consecutive Anomalies)
    # ========================================================================
    
    def test_critical_period_consecutive_anomalies(
        self,
        mock_parquet_dir,
        historical_baseline_events,
        critical_period_day1_and_2_events,
        critical_period_day3_events
    ):
        """
        Test Case: Third consecutive bug day (2015-09-05)
        Expected: Critical alert triggered
        """
        Settings.parquet_dir = mock_parquet_dir
        
        # Combine: Historical + Day 1&2 + Day 3
        all_events = pd.concat([
            historical_baseline_events,
            critical_period_day1_and_2_events,
            critical_period_day3_events
        ], ignore_index=True)
        
        create_parquet_file(all_events, mock_parquet_dir / "events.parquet")
        
        pipeline = AnomalyDetectionPipeline()
        result = pipeline.process(date(2015, 9, 5))
        
        # Assertions
        assert result.status == "CRITICAL", f"Expected CRITICAL, got {result.status}"
        assert result.alert_level == "HIGH"
        assert result.anomaly.is_anomaly == True
        assert result.consecutive.is_critical == True
        
        assert result.consecutive.streak_length == 3
        assert result.consecutive.streak_start == date(2015, 9, 3)
        assert result.consecutive.streak_end == date(2015, 9, 5)
        
        assert result.anomaly.conversion_rate < 0.3, \
            f"Conversion {result.anomaly.conversion_rate}% too high for critical"
        
        assert result.anomaly.deviation_sigma < -2.0, \
            f"Deviation {result.anomaly.deviation_sigma}σ not severe enough"
        
        print(f"\n✅ Test 3 PASSED: Critical period correctly identified")
        print(f"   Conversion: {result.anomaly.conversion_rate:.2f}%")
        print(f"   Streak: {result.consecutive.streak_length} days")
        print(f"   Period: {result.consecutive.streak_start} → {result.consecutive.streak_end}")
        print(f"   Deviation: {result.anomaly.deviation_sigma:+.1f}σ")
    
    # ========================================================================
    # TEST 4: Edge Case - Insufficient Historical Data
    # ========================================================================
    
    def test_insufficient_historical_data(
        self,
        mock_parquet_dir,
        normal_events
    ):
        """
        Test Case: Not enough historical data for baseline
        Expected: INSUFFICIENT_DATA status
        """
        # Setup test data (only 1 day of data)
        Settings.parquet_dir = mock_parquet_dir
        
        # Save only normal events (no historical baseline)
        create_parquet_file(normal_events, mock_parquet_dir / "events.parquet")
        
        # Run pipeline
        pipeline = AnomalyDetectionPipeline()
        result = pipeline.process(date(2015, 8, 15))
        
        # Assertions
        assert result.status == "INSUFFICIENT_DATA", \
            f"Expected INSUFFICIENT_DATA, got {result.status}"
        assert result.alert_level == "NONE"
        
        print(f"\n✅ Test 4 PASSED: Insufficient data correctly handled")
    
    # ========================================================================
    # TEST 5: Edge Case - No Events for Target Date
    # ========================================================================
    
    def test_no_events_for_target_date(
        self,
        mock_parquet_dir,
        historical_baseline_events
    ):
        """
        Test Case: Target date has no events
        Expected: NO_DATA status
        """
        # Setup test data
        Settings.parquet_dir = mock_parquet_dir

            # Create events for 2015-08-10 (not target)
        other_day_events = pd.DataFrame([{
            'timestamp_readable': '2015-08-10 10:00:00',
            'event_type': 'view',
            'browser': 'safari',
            'os': 'ios',
            'device': 'mobile',
            'visitor_id': 'test',
            'item_id': 'test',
            'transaction_id': None
        }])
        
        all_events = pd.concat([historical_baseline_events, other_day_events], ignore_index=True)
        create_parquet_file(all_events, mock_parquet_dir / "events.parquet")
        
        # Run pipeline for date with no events
        pipeline = AnomalyDetectionPipeline()
        result = pipeline.process(date(2015, 9, 15))
        
        # Assertions
        assert result.status == "NO_DATA", \
            f"Expected NO_DATA, got {result.status}"
        assert result.alert_level == "NONE"
        
        print(f"\n✅ Test 5 PASSED: No data correctly handled")

# ============================================================================
# Run tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])