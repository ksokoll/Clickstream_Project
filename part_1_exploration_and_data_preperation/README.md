# Stage 1: Data Preparation & Root Cause Analysis
> **Foundation work: Dataset contamination, statistical analysis, and Safari iOS bug identification**

**Repository:** `Clickstream_Project/part_1_exploration_and_data_preperation`  
**Duration:** January 22-31, 2026  
**Status:** ✅ Completed

---

## Overview

This stage lays the groundwork for the entire project. We take a clean e-commerce dataset, inject a realistic browser bug, and conduct statistical analysis to identify the root cause of conversion rate drops. Three distinct steps: data enrichment (add device/browser/OS), bug injection (contaminate Safari iOS transactions), and root cause analysis (prove it's Safari iOS).

---

## What We Built

### Part 1: Data Enrichment (`01_data_enrichment.py`)

**The Problem:** Retail Rocket dataset has 2.7M e-commerce events but no device/browser/OS data. Real clickstream data always includes this.

**The Solution:** Assign realistic device/browser/OS combinations using conditional probability:
- Device first (45% desktop, 50% mobile, 5% tablet)
- Browser depends on device (Safari only on iOS/macOS, Edge only on Windows)
- OS depends on browser (Chrome/Firefox cross-platform)

Each visitor stays consistent - no switching between iPhone and Windows mid-session. Vectorized NumPy operations process 1.4M unique visitors in minutes instead of hours.

**Output:** `df_enriched.csv` - 2.7M events with device/browser/OS columns

---

### Part 2: Bug Injection (`02_data_contamination.py`)

**The Scenario:** Safari iOS update breaks checkout JavaScript. Users browse and add to cart but can't complete purchase.

**Contamination strategy:**
- Target: Last 14 days, Safari iOS Mobile transactions only
- Found: 572 transactions
- Contaminated: 458 (80% - real bugs don't affect everyone)
- Method: Change event from "transaction" to "addtocart", clear transaction ID

Why 80%? Some users have cached JavaScript, older iOS versions, or different timing - real bugs are messy.

**Output:** `df_contaminated.csv` - Same 2.7M events, 458 transactions now abandoned carts

---

### Part 3: Statistical Analysis (`03_static_anomaly_detection.ipynb`)

**The Analysis Pipeline:**

1. **Calculate daily conversion rates** - Aggregate 2.7M events → 107 days per combination
2. **Calculate baseline using Median + MAD** - Compare each Saturday to last 4 Saturdays (normalizes weekly patterns)
3. **Detect anomalies** - Flag days where conversion < baseline - 2σ
4. **Find consecutive streaks** - 3+ consecutive days = CRITICAL alert
5. **Multi-combination validation** - Test 5 browser/OS/device combinations

**Why Median + MAD instead of Mean?**

Initial Mean/StdDev approach failed - lookback window contaminated with bug days created negative thresholds. Median ignores outliers, MAD (Median Absolute Deviation) provides robust spread measurement even with contaminated data.

**Multi-Combination Results:**

| Combination | Anomalous Days | Critical Periods |
|-------------|----------------|------------------|
| **Safari iOS Mobile** | **24 (22.4%)** | **2 (12d + 3d)** |
| Safari macOS Desktop | 16 (15.0%) | 0 |
| Chrome Android Mobile | 6 (5.6%) | 0 |
| Chrome Windows Desktop | 7 (6.5%) | 0 |
| Firefox Windows Desktop | 16 (15.0%) | 0 |

Only Safari iOS shows critical periods - proves isolated platform-specific bug.

---

## Results

**Root Cause:** Safari iOS Mobile checkout failure
- Normal conversion: 0.74%
- Bug period: 0.42%
- **Drop: 43 percentage points**
- Statistical deviation: **-4σ** (astronomically unlikely to be random)

**Detection speed:** 3 days (automated) vs 2 weeks (manual) = **79% faster**

**Critical periods:** Sept 1-12 (12 days), Sept 16-18 (3 days)

---

## Key Technical Decisions

✅ **Conditional device/browser assignment** - Prevents impossible combinations (Safari on Android)  
✅ **80% contamination rate** - Realistic bug behavior (not 100% of users affected)  
✅ **Median + MAD over Mean/StdDev** - Robust against contaminated lookback windows  
✅ **Same-weekday baseline** - Handles e-commerce cyclical patterns without holiday calendars  
✅ **±2σ threshold** - Tested 1σ/2σ/3σ manually, 2σ balanced false positives vs negatives  

---
 Refactor analysis into production-ready OOP system with comprehensive testing

---

**This stage proves the concept through systematic statistical analysis. Safari iOS bug identified with 95% confidence using robust statistics and multi-combination validation.**
