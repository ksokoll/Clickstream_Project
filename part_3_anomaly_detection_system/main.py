from datetime import datetime, date
from pipeline import AnomalyDetectionPipeline
import sys

def main():
    """
    Minimal CLI entry point.

    As this project focuses on business logic and decision correctness, verbose print statements are avoided,
    as it is assumed that a integration of this engine into a larger system would handle logging and user interaction.
    """
    
    if len(sys.argv) < 2:
        sys.exit(1)

    target_date = datetime.strptime(sys.argv[1], "%Y-%m-%d").date()
    result = AnomalyDetectionPipeline().process(target_date)

    exit_codes = {
        "OK": 0,
        "ANOMALY": 1,
        "NO_DATA": 1,
        "INSUFFICIENT_DATA": 1,
        "CRITICAL": 2,
    }

    sys.exit(exit_codes[result.status])