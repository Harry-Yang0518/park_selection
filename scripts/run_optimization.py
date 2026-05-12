#!/usr/bin/env python
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from park_selection import config
from park_selection.optimization import run_optimization


def default_parks_path() -> Path:
    return config.REPORT_PARKS_PATH if config.REPORT_PARKS_PATH.exists() else config.DEFAULT_PARKS_PATH


def default_candidates_path() -> Path:
    return config.REPORT_CANDIDATES_PATH if config.REPORT_CANDIDATES_PATH.exists() else config.DEFAULT_CANDIDATES_PATH


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run report-aligned single and multi budgeted optimization.")
    parser.add_argument("--demand", type=Path, default=config.DEFAULT_DEMAND_PATH)
    parser.add_argument("--parks", type=Path, default=default_parks_path())
    parser.add_argument("--candidates", type=Path, default=default_candidates_path())
    parser.add_argument("--output-dir", type=Path, default=config.OUTPUT_DIR)
    parser.add_argument("--budget", type=int, default=config.TOTAL_BUDGET)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    single_path, multi_path, summary_path = run_optimization(
        demand_path=args.demand,
        parks_path=args.parks,
        candidates_path=args.candidates,
        output_dir=args.output_dir,
        budget=args.budget,
    )
    print(f"Saved single-access actions to {single_path}")
    print(f"Saved multi-access actions to {multi_path}")
    print(f"Saved optimization summary to {summary_path}")


if __name__ == "__main__":
    main()
