# Park Selection

Python implementation of the methodology in `Urban_Computing_Report.pdf`:

- Elderly demand: `D_i = population_i * elderly_ratio_i`
- Park quality: mean of five min-max normalized components: area, transit, toilet, health service, elderly service
- Catchment: 1.5 km walking threshold
- Distance decay: Gaussian decay with `sigma = 750 m`
- Multi-access baseline: sum of all reachable quality-weighted parks
- Single-access baseline: one best park link per residential unit
- Optimization: binary actions for upgrades, support facilities, and new parks with `alpha=0.10`, `beta=0.07`, `gamma=0.18`, costs `3/2/5`, and budget `100`

The original notebooks are preserved under `legacy/notebooks/`. The reproducible code now lives in `src/park_selection/` with command-line entry points in `scripts/`.

## Setup

Use a clean environment because the project needs compatible geospatial wheels:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## Run the report-aligned pipeline

Optional preprocessing entry points replace the original data-preparation notebooks:

```bash
python scripts/run_preprocess.py clean-pois
python scripts/run_preprocess.py standardize-pois
python scripts/run_preprocess.py standardize-parks --input /path/to/park_polygons.shp
python scripts/run_preprocess.py elderly-demand --input /path/to/elderly_population.shp
python scripts/run_preprocess.py parameters
```

If `parks_with_quality_3857` already reflects the report quality formula, run baselines and optimization directly:

```bash
python scripts/run_baselines.py
python scripts/run_optimization.py
```

To rebuild park quality from park polygons and POIs:

```bash
python scripts/run_quality.py \
  --parks dataset_structured/05_processed/standardized_layers/parks_poly_3857.shp \
  --pois dataset_structured/05_processed/standardized_layers/pois_3857.shp
```

Then rerun:

```bash
python scripts/run_baselines.py
python scripts/run_optimization.py
```

Default outputs are written to:

- `outputs/parks_with_quality_report.gpkg`
- `outputs/accessibility_baselines.gpkg`
- `outputs/baseline_summary.csv`
- `outputs/candidate_new_park_spots.gpkg`
- `outputs/optimization_actions_single.gpkg`
- `outputs/optimization_actions_multi.gpkg`
- `outputs/optimization_summary.csv`

## Notes

The old notebooks used a mix of `2,000 m` radius, exponential decay, weighted/log area quality, and hard-coded local Windows paths. The Python implementation intentionally follows the report instead: `1,500 m` radius, Gaussian decay with `sigma=750`, equal five-component quality, and budgeted binary intervention parameters from the final report.
