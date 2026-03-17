
# Dynamic Anomaly Detection Pipeline for E-Commerce Conversion Rates

## Overview

This project implements a business-oriented anomaly detection pipeline for e-commerce conversion rates and is part 3 of a multi-step project, that covers the whole business case from exploration until technical implementation.
Its primary goal is to detect statistically significant drops in conversion performance and escalate alerts based on consecutive anomaly patterns. No machine learning or AI this time! Just math. :)

The system is intentionally designed as a **decision engine**, not a UI or monitoring dashboard.

The project is inspired by a realistic industry scenario in which an e-commerce company experiences a sustained drop in online orders while traffic and offline sales remain stable. Traditional ERP- and order-centric reporting fails to explain *why* conversions decline, highlighting the need for behavioral, event-based analytics and automated anomaly detection.

---

## Business Case

A mid-sized electronics retailer observed a **persistent decline in online orders** over several weeks.
Despite stable traffic and healthy offline sales, the root cause remained unclear.

Existing BI reporting focused on transactional ERP data (orders, revenue, P2P/I2C flows) and offered **no visibility into user behavior before purchase**. As a result, the organization reacted late, relied on manual investigation, and lacked early-warning signals.

This project models the analytical response to that problem:

* introducing event-level data as a first-class analytical source
* deriving business-relevant metrics such as conversion rates
* automatically detecting statistically significant deviations
* escalating only when anomalies persist across multiple days

The anomaly detection pipeline represents the **decision layer** of such a system: it does not explain every detail, but reliably answers the question  
**“Is this a real business incident that requires action?”**

Typical real-world triggers include:

* frontend regressions
* broken checkout flows
* browser or device-specific bugs (e.g. mobile Safari)
* faulty deployments or tracking issues

---

## Core Concepts

### 1. Conversion-Based Anomaly Detection

* Conversion rate = transactions / views
* Daily conversion is compared against a **historical baseline**
* Deviations are evaluated using **sigma-based statistics**

### 2. Consecutive Anomaly Escalation

| Pattern                  | Business Interpretation           |
| ------------------------ | --------------------------------- |
| Single anomaly           | Possible noise or transient issue |
| 3+ consecutive anomalies | Critical incident                 |

This prevents overreaction to one-off outliers and mirrors how real operational teams assess risk.

### 3. Business-Oriented Outcomes

Instead of raw numbers, the pipeline returns explicit states:

* `OK`
* `ANOMALY`
* `CRITICAL`
* `NO_DATA`
* `INSUFFICIENT_DATA`

These states are designed for downstream automation such as alerting, ticket creation, or workflow orchestration.

---

## Architecture

```

data (parquet)
↓
AnomalyDetectionPipeline
↓
Statistical Baseline
↓
Anomaly Evaluation
↓
Consecutive Streak Analysis
↓
Decision Result

````

The pipeline returns a **structured result object**, not formatted text.

---

## Intentional Design Decisions

This project is part of a portfolio and focuses on **business logic correctness**.

### Included on purpose

* deterministic, synthetic test data
* strong unit test coverage
* explicit business semantics
* minimal CLI interface

### Explicitly out of scope

* structured logging
* centralized error handling
* formatted CLI output
* dashboards or visualization
* API entry points

> Operational concerns (logging, monitoring, production hardening) are intentionally excluded and demonstrated in a separate project.

---

## Testing

* Tests define the **business behavior**, not just implementation details
* I added fully synthetic datasets to ensure reproducibilit, fast execution and CI/CD readiness

Here is a lit of test-scenarios that I implemented:

1. Normal business periods
2. Single anomaly days
3. Critical periods with consecutive anomalies
4. Insufficient historical data
5. Target dates without events

Tests act as **executable documentation**.

---

## CLI Usage (Minimal by Design)

```bash
python main.py YYYY-MM-DD
````

The CLI:

* parses the date
* executes the pipeline
* exits with a status code

No formatted output is produced intentionally.
Behavior is validated via **tests and exit codes**, not console text.

---

## Example Use Cases

* Detecting conversion drops after deployments
* Monitoring checkout regressions
* Supporting incident escalation decisions
* Serving as a backend decision component in larger systems

---

## Additional Thougts
While creating the project, I purpusefully cared about the pragmatic application of statistical reasoning instead of ML, as ML would be overkill here.
Also since I used my pipeline-framework, clear separation of concerns is kept.
This time I took more time to create meaningful tests to validate correct business behavior of the system, while also avoiding overengineering it.

---

# Technical Overview

## Structure

```
📁 .pytest_cache
  📁 v
    📁 cache
        📄 lastfailed
        📄 nodeids
  📄 .gitignore
  📄 CACHEDIR.TAG
  📄 README.md
📁 anomaly_detection
📁 data
  📁 parquet_output
      📄 events_batch_0000.parquet
📁 processors
  📄 anomaly_detector.py
  📄 baseline_calculator.py
  📄 conversion_calculator.py
📁 tests
  📄 conftest.py
  📄 test_anomaly_detection.py
  📄 test_approach_and_results.md
📄 config.py
📄 data_loader.py
📄 main.py
📄 models.py
📄 pipeline.py
📄 requirements.txt
```

---


## Technical Overview

The project is organized into a clear, modular structure, making it easy to understand, maintain, and extend. At its core, the pipeline uses historical conversion data to establish a baseline and compares current performance against it. Deviations are measured statistically, and consecutive anomalies are flagged to identify truly significant business events rather than one-off noise.

The directory structure reflects this modular approach, separating data, processors, models, and tests. This separation ensures that each component has a single responsibility and can be tested in isolation.

Key technical highlights include:

* Historical conversion rates form a **robust baseline** using Median and MAD, reducing the impact of outliers.
* Anomalies are evaluated using **sigma-based thresholds**, providing a quantitative measure of significance.
* Multiple consecutive anomalies are aggregated into **critical alerts**, mimicking how real operational teams prioritize incidents.
* The pipeline is **fully testable**, with synthetic datasets enabling reproducible and fast tests.

---

## How the Pipeline Works

Conceptually, the pipeline proceeds in six main steps:

1. **Data Loading** – The system first gathers all relevant event data from Parquet files, filtering by device, browser, and operating system. It can fetch historical data leading up to a target date, or the events for a single target date, depending on the context.

2. **Conversion Calculation** – Once data is loaded, daily views, transactions, and conversion rates are calculated. This works both for historical summaries and the specific day being monitored.

3. **Baseline Calculation** – Using the last several weeks of data, the pipeline computes baseline conversion rates for each weekday. The Median and Median Absolute Deviation (MAD) provide a robust sigma estimate for evaluating deviations.

4. **Anomaly Detection** – The target day's conversion is compared against the baseline plus or minus a configurable sigma threshold. If the conversion falls outside this range, it is flagged as an anomaly. The system also tracks consecutive anomalies to detect critical incidents.

5. **Pipeline Orchestration** – The `AnomalyDetectionPipeline` brings all the components together. It runs the full workflow from loading data to calculating conversions, establishing baselines, detecting anomalies, and evaluating streaks, returning a structured `DailyCheckResult`.

6. **CLI Execution** – For simplicity, the pipeline can be executed via a minimal command-line interface by specifying a target date. The exit code reflects the status, enabling integration with monitoring or automation systems.

---

## Module Overview

The pipeline is composed of clearly defined modules, each focusing on a single responsibility:

* **Configuration (`config.py`)** – Centralizes project-wide settings like file paths, filters, and detection parameters.
* **Data Loader (`data_loader.py`)** – Handles importing and filtering raw event data from Parquet files, ensuring only relevant data reaches the pipeline.
* **Conversion Calculator (`processors/conversion_calculator.py`)** – Transforms raw event data into meaningful business metrics, computing daily conversions.
* **Baseline Calculator (`processors/baseline_calculator.py`)** – Establishes historical baselines using robust statistics, providing sigma thresholds for anomaly detection.
* **Anomaly Detector (`processors/anomaly_detector.py`)** – Compares actual conversions to the baseline, flags anomalies, and evaluates consecutive anomaly streaks for escalation.
* **Pipeline (`pipeline.py`)** – Orchestrates the entire workflow, connecting the loaders, calculators, and detectors into a cohesive decision engine.
* **Models (`models.py`)** – Defines structured data representations for daily conversions, baselines, anomalies, and results, ensuring consistency across the pipeline.
* **CLI Entry (`main.py`)** – Provides a minimal interface for running the pipeline by date. Its role is limited to execution; all output is structured rather than formatted.
* **Tests (`tests/`)** – Unit tests using synthetic datasets validate both business behavior and technical correctness, acting as executable documentation.


