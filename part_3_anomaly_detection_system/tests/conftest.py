import pytest
import pandas as pd
from datetime import date, datetime, timedelta
from pathlib import Path

# ============================================================================
# TEST DATA SETUP - PyTest Fixtures
# ============================================================================

# First, I define fixtures for the test data with the pytest.fixture decorator.
# Fixtures are reusable setup functions that provide data or resources to tests.
# They have the advantage that temporary test data is cleaned up automatically 
# after the test run.

# ============================================================================
# WHY SYNTHETIC DATA INSTEAD OF PRODUCTION DATA?
# ============================================================================

# 1. PORTABILITY: Tests must run anywhere (CI/CD, different machines)
#    - Production data (2.7M events, 150MB) not in Git repository
#    - GitHub Actions would fail: FileNotFoundError
#    - Other developers wouldn't have the data files
#
# 2. SPEED: Synthetic data is 100x faster
#    - Production: Load 2.7M events = ~10 seconds per test
#    - Synthetic: Create 5,000 events = ~0.1 seconds per test
#    - 5 tests: 50 seconds vs 0.5 seconds
#
# 3. CONTROL: Exact test scenarios
#    - Normal day: Exactly 0.8% conversion (40/5000)
#    - Anomaly day: Exactly 0.4% conversion (18/4500)
#    - Critical day: Exactly 0.1% conversion (4/4000)
#    - Production data: Unclear which dates have which patterns
#
# 4. EDGE CASES: Test scenarios that might not exist in production
#    - Zero events for a specific date
#    - Exactly 3 consecutive anomalies
#    - Specific conversion rates for statistical validation
#
# 5. ISOLATION: Tests remain stable when production data changes
#    - Production data modifications don't break tests
#    - Each test creates its own independent dataset
#    - No shared state between tests
#
# 6. READABILITY: Test expectations are clear from fixture code
#    - Can see exactly what data is being tested
#    - No need to inspect external parquet files
#    - Self-contained test suite

# ============================================================================
# FIXTURE EXPLANATION: mock_parquet_dir
# ============================================================================

# The mock_parquet_dir fixture simulates the data loading process without 
# actually needing to access production data.
#
# - tmp_path: Built-in pytest fixture providing a temporary directory unique 
#   to each test invocation (e.g., /tmp/pytest-123/test0/)
# - This fixture itself uses another fixture (fixture composition)
# - Creates a subdirectory "parquet_output" inside the temporary path
# - Returns the path for use in tests
# - PyTest automatically deletes tmp_path after test completion

# ============================================================================
# OVERALL TEST ARCHITECTURE GOALS
# ============================================================================

# 1. ISOLATION: Each test is isolated from:
#    - Production data (uses synthetic data instead)
#    - Other tests (each gets unique tmp_path)
#    - External dependencies (no reliance on data/ directory)
#
# 2. AUTOMATIC CLEANUP: 
#    - Temporary files deleted after test run
#    - No manual cleanup required
#    - Clean environment for each test execution
#
# 3. REPRODUCIBILITY:
#    - Tests produce identical results every run
#    - No dependency on external data state
#    - Can run in any order without side effects
#
# 4. PARALLELIZABILITY:
#    - Tests can run in parallel (pytest -n auto)
#    - Each test has isolated temporary directory
#    - No conflicts between concurrent test executions
#
# 5. CI/CD COMPATIBILITY:
#    - Tests run on GitHub Actions without data files
#    - Fast execution for quick feedback loops
#    - Reliable results across different environments

# ============================================================================
# DATA GENERATION APPROACH
# ============================================================================

# Historical Baseline (45 days):
# - Period: 2015-07-01 → 2015-08-14
# - Purpose: Establish normal conversion baseline (~0.83%)
# - Pattern: 4,800 views/day, 38-42 transactions/day
# - Used by all tests for baseline calculation
#
# Normal Events (1 day):
# - Date: 2015-08-15
# - Purpose: Test normal operation detection
# - Pattern: 5,000 views, 40 transactions (0.8%)
# - Expected: Status = OK, no anomaly
#
# Single Anomaly (1 day):
# - Date: 2015-09-01
# - Purpose: Test single-day anomaly detection
# - Pattern: 4,500 views, 18 transactions (0.4%)
# - Expected: Status = ANOMALY, alert_level = MEDIUM
#
# Critical Period (3 days):
# - Dates: 2015-09-03, 09-04, 09-05
# - Purpose: Test consecutive anomaly detection
# - Pattern: 4,000 views, 4-8 transactions (0.1-0.2%)
# - Expected: Status = CRITICAL, alert_level = HIGH

# ============================================================================
# NOTE ON INTEGRATION TESTING
# ============================================================================

# These are UNIT tests with synthetic data (fast, isolated).
# For END-TO-END validation with real production data, see:
# tests/integration/test_real_data.py (runs with pytest -m integration)

@pytest.fixture
def mock_parquet_dir(tmp_path):
    """Create temporary parquet directory with test data"""
    parquet_dir = tmp_path / "parquet_output"
    parquet_dir.mkdir()
    return parquet_dir

# The purpose of historical_baseline_events fixture is to create a DataFrame that simulates 6 weeks of historical event data while using
# a simulated 6 weeks of daily data to ensure that the baseline calculation has sufficient data to work with.
# This historical data is crucial for establishing a reliable baseline for all the following tests.
# Important: The test lie before the anomaly period.

@pytest.fixture
def historical_baseline_events():
    """Historical events - 6 weeks of daily data"""
    events = [] # This is a seemingly minor step, but here I had the decision between list and DataFrame. I decided for list first, because appending to lists is more efficient than creating a new df each time.
    start = pd.Timestamp('2015-07-01') # Start date for historical data, far away from the anomaly period.
    
    for days in range(45):  # 6+ weeks
        date_str = (start + timedelta(days=days)).strftime('%Y-%m-%d')
        
        # Views
        for i in range(5000):
            events.append({
                'timestamp_readable': f'{date_str} 10:00:00',
                'event': 'view',
                'browser': 'safari',
                'os': 'ios',
                'device': 'mobile',
                'visitor_id': f'v_{date_str}_{i}',
                'item_id': f'item_{i%100}',
                'transaction_id': None
            })
        
        # Transactions (38-42, ~0.8% conversion in relation to the views)
        num_trans = 38 + (days % 5)  # Slight variation to simulate normal variance, as some days we have more transactions, some days less.
        for i in range(num_trans):
            events.append({
                'timestamp_readable': f'{date_str} 10:00:00',
                'event': 'transaction',
                'browser': 'safari',
                'os': 'ios',
                'device': 'mobile',
                'visitor_id': f'v_{date_str}_{i}',
                'item_id': f'item_{i}',
                'transaction_id': f't_{date_str}_{i}'
            })

    # I am skipping the last event, "addtocard", as it is not relevant for conversion calculation.
    
    # 'events' is now a list of 216.000+ entries with a variable mix of views and transactions over 45 days.
    return pd.DataFrame(events)

# The next fixture creates a dataframe for a single day with normal event data (no anomaly).
# It is used to simulate the normal operation of the system and to verify that no false positives are detected.
@pytest.fixture
def normal_events():
    """Events for normal period (no anomaly) - 2015-08-15"""
    events = []
    date_str = '2015-08-15'
    
    # views
    for i in range(5000):
        events.append({
            'timestamp_readable': f'{date_str} 10:00:00',
            'event': 'view',
            'browser': 'safari',
            'os': 'ios',
            'device': 'mobile',
            'visitor_id': f'visitor_{i}',
            'item_id': f'item_{i % 100}',
            'transaction_id': None
        })
    
    # 40 transactions (0.8% - normal)
    for i in range(40):
        events.append({
            'timestamp_readable': f'{date_str} 10:00:00',
            'event': 'transaction',
            'browser': 'safari',
            'os': 'ios',
            'device': 'mobile',
            'visitor_id': f'visitor_{i}',
            'item_id': f'item_{i}',
            'transaction_id': f'trans_{i}'
        })
    
    return pd.DataFrame(events)

# Next, we have a anomaly flag, which is the second type of flag after "normal" by simulating the first day of the anomaly period.
# This fixture creates a DataFrame that simulates a day with a significant drop in conversion rate for a specific browser, OS, and device combination.
# This is crucial for testing the anomaly detection capabilities of the system by testing if it is able to identify this sudden change correctly.
@pytest.fixture
def single_anomaly_events():
    """Events for single anomaly day - 2015-09-01"""
    events = []
    date_str = '2015-09-01' # The first day, that the "safari" bug occurs
    
    # views
    for i in range(5000):
        events.append({
            'timestamp_readable': f'{date_str} 10:00:00',
            'event': 'view',
            'browser': 'safari',
            'os': 'ios',
            'device': 'mobile',
            'visitor_id': f'visitor_{i}',
            'item_id': f'item_{i % 100}',
            'transaction_id': None
        })
    
    # 18 transactions (0.4% - anomaly)
    for i in range(18):
        events.append({
            'timestamp_readable': f'{date_str} 10:00:00',
            'event': 'transaction',
            'browser': 'safari',
            'os': 'ios',
            'device': 'mobile',
            'visitor_id': f'visitor_{i}',
            'item_id': f'item_{i}',
            'transaction_id': f'trans_{i}'
        })
    
    return pd.DataFrame(events)

# Following is the critical period fixture, which simulates a multi-day period of significantly reduced conversion rates.
# This fixture creates DataFrames for three consecutive days where the conversion rates are critically low.
@pytest.fixture
def critical_period_day1_and_2_events():
    """Events for first 2 days of critical period (for historical)"""
    events = []
    dates = ['2015-09-03', '2015-09-04']
    
    for date_str in dates:
        # views
        for i in range(5000):
            events.append({
                'timestamp_readable': f'{date_str} 10:00:00',
                'event': 'view',
                'browser': 'safari',
                'os': 'ios',
                'device': 'mobile',
                'visitor_id': f'visitor_{date_str}_{i}',
                'item_id': f'item_{i % 100}',
                'transaction_id': None
            })
        
        # 8 transactions (0.2% - anomaly)
        for i in range(8):
            events.append({
                'timestamp_readable': f'{date_str} 10:00:00',
                'event': 'transaction',
                'browser': 'safari',
                'os': 'ios',
                'device': 'mobile',
                'visitor_id': f'visitor_{date_str}_{i}',
                'item_id': f'item_{i}',
                'transaction_id': f'trans_{date_str}_{i}'
            })
    
    return pd.DataFrame(events)

# And finally we have the third day of the critical period fixture. This fixture creates a DataFrame for the third day of the critical period,
# continuing the pattern of significantly reduced conversion rates.
@pytest.fixture
def critical_period_day3_events():
    """Events for ONLY the 3rd day of critical period (2015-09-05)"""
    events = []
    date_str = '2015-09-05'
    
    # 5000 views
    for i in range(5000):
        events.append({
            'timestamp_readable': f'{date_str} 10:00:00',
            'event': 'view',
            'browser': 'safari',
            'os': 'ios',
            'device': 'mobile',
            'visitor_id': f'visitor_{date_str}_{i}',
            'item_id': f'item_{i % 100}',
            'transaction_id': None
        })
    
    # 4 transactions (0.1% - critical!)
    for i in range(4):
        events.append({
            'timestamp_readable': f'{date_str} 10:00:00',
            'event': 'transaction',
            'browser': 'safari',
            'os': 'ios',
            'device': 'mobile',
            'visitor_id': f'visitor_{date_str}_{i}',
            'item_id': f'item_{i}',
            'transaction_id': f'trans_{date_str}_{i}'
        })
    
    return pd.DataFrame(events)

# This last function is a helper to create parquet files from DataFrames.
def create_parquet_file(df, filepath):
    """Helper to create parquet file"""
    df.to_parquet(filepath, engine='pyarrow', index=False)