#!/usr/bin/env python
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from park_selection import config
from park_selection.baselines import run_baselines
from park_selection.optimization import run_optimization


def main() -> None:
    parks_path = config.REPORT_PARKS_PATH if config.REPORT_PARKS_PATH.exists() else config.DEFAULT_PARKS_PATH
    run_baselines(
        demand_path=config.DEFAULT_DEMAND_PATH,
        parks_path=parks_path,
        output_path=config.OUTPUT_DIR / "accessibility_baselines.gpkg",
        summary_path=config.OUTPUT_DIR / "baseline_summary.csv",
        candidates_path=config.REPORT_CANDIDATES_PATH,
    )
    run_optimization(
        demand_path=config.DEFAULT_DEMAND_PATH,
        parks_path=parks_path,
        candidates_path=config.REPORT_CANDIDATES_PATH,
        output_dir=config.OUTPUT_DIR,
    )


if __name__ == "__main__":
    main()
