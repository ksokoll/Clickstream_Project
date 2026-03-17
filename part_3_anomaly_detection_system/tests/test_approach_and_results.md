# Test Suite - Anomaly Detection System
Business Logic Tests

## Overview

Comprehensive PyTest suite validating the anomaly detection pipeline across 5 critical scenarios. Tests use synthetic data mimicking real Safari iOS bug patterns with realistic event distributions and conversion rates.

---

## Test Architecture

### Test Data Strategy

**Historical Baseline (45 days)**
- Period: 2015-07-01 → 2015-08-14
- Daily events: 4,800 views, 38-42 transactions
- Conversion rate: ~0.8% (normal range)
- Purpose: Establishes reliable baseline for same-weekday comparison

**Target Dates**
- Normal period: 2015-08-15 (Saturday)
- Anomaly period: 2015-09-01 (Tuesday) - first bug day
- Critical period: 2015-09-05 (Saturday) - third consecutive bug day

---

## Test Cases

### Test 1: Normal Period (No Anomaly)

**Scenario:** Typical Saturday with healthy conversion rate

**Test Data:**
- Date: 2015-08-15
- Views: 5,000
- Transactions: 40
- Conversion: 0.8%

**Expected Result:**
- Status: OK
- Alert Level: NONE
- is_anomaly: False
- Deviation: Within ±2σ

**Validates:**
- Baseline calculation accuracy
- Normal variance tolerance
- No false positives on healthy days

---

### Test 2: Single Anomaly Day

**Scenario:** First day of Safari iOS bug - conversion drops but no streak yet

**Test Data:**
- Date: 2015-09-01
- Views: 4,500
- Transactions: 18
- Conversion: 0.4%

**Expected Result:**
- Status: ANOMALY
- Alert Level: MEDIUM
- is_anomaly: True
- consecutive.is_critical: False
- Deviation: < -2σ

**Validates:**
- Statistical threshold detection (±2σ)
- Single-day anomaly flagging
- Correct alert level (MEDIUM, not CRITICAL)
- Consecutive streak logic (requires 3+ days)

---

### Test 3: Critical Period (3 Consecutive Days)

**Scenario:** Third consecutive bug day triggers critical alert

**Test Data:**
- Dates: 2015-09-03, 09-04, 09-05
- Day 1: 4,000 views, 8 transactions (0.2%)
- Day 2: 4,000 views, 8 transactions (0.2%)
- Day 3: 4,000 views, 4 transactions (0.1%)

**Expected Result:**
- Status: CRITICAL
- Alert Level: HIGH
- consecutive.is_critical: True
- streak_length: 3
- streak_start: 2015-09-03
- streak_end: 2015-09-05

**Validates:**
- Consecutive day detection
- Critical alert escalation
- Streak period identification
- Multi-day anomaly tracking

---

### Test 4: Insufficient Historical Data

**Scenario:** Not enough baseline data for reliable detection

**Test Data:**
- Only 1 day of events (no historical baseline)

**Expected Result:**
- Status: INSUFFICIENT_DATA
- Alert Level: NONE

**Validates:**
- Minimum data requirements (4 weeks)
- Graceful degradation
- Edge case handling
- Prevents unreliable detections

---

### Test 5: No Events for Target Date

**Scenario:** Target date exists in timeline but has no events

**Test Data:**
- Historical: 45 days of data
- Target: 2015-09-15 (no events)

**Expected Result:**
- Status: NO_DATA
- Alert Level: NONE

**Validates:**
- Missing data handling
- Data availability checks
- Correct error status differentiation

---

## Test Results
```
✅ Test 1: Normal Period - PASSED
   Conversion: 0.80% | Baseline: 0.84% | Deviation: -1.4σ

✅ Test 2: Single Anomaly - PASSED
   Conversion: 0.40% | Threshold: 0.50% | Deviation: -3.9σ

✅ Test 3: Critical Period - PASSED
   Conversion: 0.10% | Streak: 3 days | Deviation: -6.5σ

✅ Test 4: Insufficient Data - PASSED
   Correctly handled missing baseline

✅ Test 5: No Events - PASSED
   Correctly handled missing target date

5 passed in 4.39s
```

---

## Design Decisions

### Why These Scenarios?

**Coverage Matrix:**
- Happy path (normal operation)
- Single failure (isolated anomaly)
- Critical failure (systematic issue)
- Data quality issues (insufficient/missing data)

**Realistic Thresholds:**
- Normal: 0.8% conversion (baseline)
- Anomaly: 0.4% conversion (-2.5σ)
- Critical: 0.1% conversion (-6σ)

**Consecutive Rule Rationale:**
- 1 day: Could be random variance, server issue
- 2 days: Still potentially temporary
- 3+ days: Systematic problem requiring immediate action

### Statistical Rigor

**Median + MAD Baseline:**
- Robust against outliers (contaminated lookback window)
- Same-weekday comparison (accounts for day-of-week effects)
- ±2σ threshold (95% confidence, industry standard)

**Test Data Variability:**
- Slight variation in daily conversions (38-42 transactions)
- Realistic view counts (4,000-5,000)
- Weekday patterns reflected in baseline

---

## Key Takeaways

✅ **Comprehensive Coverage:** All pipeline paths tested  
✅ **Production Scenarios:** Real-world failure modes  
✅ **Statistical Validation:** Threshold accuracy verified  
✅ **Edge Case Handling:** Graceful degradation confirmed  
✅ **Type Safety:** Pydantic models prevent runtime errors  

**Test suite validates system reliability before production deployment.**