#!/usr/bin/env python
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from park_selection import config
from park_selection.baselines import run_baselines


def default_parks_path() -> Path:
    return config.REPORT_PARKS_PATH if config.REPORT_PARKS_PATH.exists() else config.DEFAULT_PARKS_PATH


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run report-aligned single and multi accessibility baselines.")
    parser.add_argument("--demand", type=Path, default=config.DEFAULT_DEMAND_PATH)
    parser.add_argument("--parks", type=Path, default=default_parks_path())
    parser.add_argument("--output", type=Path, default=config.OUTPUT_DIR / "accessibility_baselines.gpkg")
    parser.add_argument("--summary", type=Path, default=config.OUTPUT_DIR / "baseline_summary.csv")
    parser.add_argument("--candidates", type=Path, default=config.REPORT_CANDIDATES_PATH)
    parser.add_argument("--candidate-fraction", type=float, default=0.01)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output, summary = run_baselines(
        demand_path=args.demand,
        parks_path=args.parks,
        output_path=args.output,
        summary_path=args.summary,
        candidates_path=args.candidates,
        candidate_fraction=args.candidate_fraction,
    )
    print(f"Saved accessibility baselines to {output}")
    print(f"Saved baseline summary to {summary}")


if __name__ == "__main__":
    main()
