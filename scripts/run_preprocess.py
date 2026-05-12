#!/usr/bin/env python
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from park_selection import config
from park_selection.preprocess import (
    clean_target_pois,
    compute_elderly_demand_layer,
    report_parameters,
    standardize_park_polygons,
    standardize_poi_csv,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preprocess source data for the report-aligned pipeline.")
    sub = parser.add_subparsers(dest="command", required=True)

    clean = sub.add_parser("clean-pois", help="Filter target POIs from split CSV files.")
    clean.add_argument("--input-glob", default=config.POI_SPLITS_GLOB)
    clean.add_argument("--output", type=Path, default=config.DEFAULT_CLEANED_POI_CSV)

    poi = sub.add_parser("standardize-pois", help="Convert cleaned POI CSV to EPSG:3857 point layer.")
    poi.add_argument("--input", type=Path, default=config.DEFAULT_CLEANED_POI_CSV)
    poi.add_argument("--output", type=Path, default=config.DEFAULT_POIS_PATH)

    parks = sub.add_parser("standardize-parks", help="Convert park polygons to EPSG:3857 and add area.")
    parks.add_argument("--input", type=Path, required=True)
    parks.add_argument("--output", type=Path, default=config.DEFAULT_PARK_POLYGONS_PATH)

    demand = sub.add_parser("elderly-demand", help="Compute elderly demand from population and elderly ratio.")
    demand.add_argument("--input", type=Path, required=True)
    demand.add_argument("--output", type=Path, default=config.DEFAULT_DEMAND_PATH)
    demand.add_argument("--population-col", default=None)
    demand.add_argument("--ratio-col", default=None)

    params = sub.add_parser("parameters", help="Write report parameter table.")
    params.add_argument("--output", type=Path, default=config.OUTPUT_DIR / "report_parameters.csv")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "clean-pois":
        df = clean_target_pois(args.input_glob, args.output)
        print(f"Saved {len(df)} cleaned POIs to {args.output}")
    elif args.command == "standardize-pois":
        print(f"Saved POI layer to {standardize_poi_csv(args.input, args.output)}")
    elif args.command == "standardize-parks":
        print(f"Saved park polygon layer to {standardize_park_polygons(args.input, args.output)}")
    elif args.command == "elderly-demand":
        output = compute_elderly_demand_layer(args.input, args.output, args.population_col, args.ratio_col)
        print(f"Saved elderly demand layer to {output}")
    elif args.command == "parameters":
        args.output.parent.mkdir(parents=True, exist_ok=True)
        report_parameters().to_csv(args.output, index=False)
        print(f"Saved report parameters to {args.output}")


if __name__ == "__main__":
    main()
