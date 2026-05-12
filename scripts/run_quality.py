#!/usr/bin/env python
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from park_selection import config
from park_selection.quality import run_quality


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rebuild report-aligned five-component park quality.")
    parser.add_argument("--parks", type=Path, default=config.DEFAULT_PARK_POLYGONS_PATH)
    parser.add_argument("--pois", type=Path, default=config.DEFAULT_POIS_PATH)
    parser.add_argument("--output", type=Path, default=config.REPORT_PARKS_PATH)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = run_quality(args.parks, args.pois, args.output)
    print(f"Saved park quality layer to {output}")


if __name__ == "__main__":
    main()
