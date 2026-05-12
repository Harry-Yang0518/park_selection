# Beyond Nearest-Park Access

Final course project for **Beyond Nearest-Park Access: Multi-Park and Park-Quality Assessment for Elderly-Friendly Planning in Shanghai**.

## Project Summary

The project evaluates elderly-friendly urban park accessibility in Shanghai. Instead of treating accessibility as a nearest-park problem, the model combines elderly demand, park quality, distance decay, and multiple reachable parks within an elderly-friendly walking catchment. It then solves a budgeted intervention problem to compare a single-access baseline with a multi-access model.

The implemented methodology follows the final report:

- Elderly demand: `D_i = population_i * elderly_ratio_i`
- Park quality: average of five min-max normalized components: area, transit, toilet, health service, elderly service
- Walking catchment: `1,500 m`
- Distance decay: Gaussian decay with `sigma = 750 m`
- Single-access baseline: best one park link per residential unit
- Multi-access baseline: sum of all reachable quality-weighted parks
- Optimization actions: upgrade existing park, add support facility, build new park
- Optimization parameters: `alpha = 0.10`, `beta = 0.07`, `gamma = 0.18`
- Unit costs: upgrade `3`, support facility `2`, new park `5`
- Budget: `100`

## Repository Structure

```text
.
├── README.md
├── docs/
│   ├── INPUTS.md
│   └── METHODOLOGY.md
├── pyproject.toml
├── requirements.txt
├── scripts/
│   ├── run_all.py
│   ├── run_baselines.py
│   ├── run_optimization.py
│   ├── run_preprocess.py
│   └── run_quality.py
└── src/
    └── park_selection/
        ├── baselines.py
        ├── config.py
        ├── optimization.py
        ├── preprocess.py
        ├── quality.py
        └── utils.py
```

## Method and Code Mapping

- `src/park_selection/preprocess.py`: prepares POIs, standardized spatial layers, and elderly demand
- `src/park_selection/quality.py`: computes the five-component park quality index
- `src/park_selection/baselines.py`: computes single-access and multi-access baselines
- `src/park_selection/optimization.py`: solves the budgeted intervention problem
- `docs/METHODOLOGY.md`: gives the formulas used by the code
- `docs/INPUTS.md`: describes the expected input layout and columns

## Implementation Scope

The single-access and multi-access models are evaluated independently from the input data, formulas, selected actions, and budget constraint. Summary tables are written directly from those calculations, with no cross-model score adjustment.

## Setup

Use a clean Python environment because the project depends on geospatial packages:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## Reproduce the Pipeline

With the required inputs under `dataset_structured/`, run:

```bash
python scripts/run_all.py
```

Equivalent step-by-step commands:

```bash
python scripts/run_baselines.py
python scripts/run_optimization.py
```

To rebuild park quality from standardized park polygons and POIs:

```bash
python scripts/run_quality.py \
  --parks dataset_structured/05_processed/standardized_layers/parks_poly_3857.shp \
  --pois dataset_structured/05_processed/standardized_layers/pois_3857.shp
```

Optional preprocessing commands:

```bash
python scripts/run_preprocess.py clean-pois
python scripts/run_preprocess.py standardize-pois
python scripts/run_preprocess.py standardize-parks --input /path/to/park_polygons.shp
python scripts/run_preprocess.py elderly-demand --input /path/to/elderly_population.shp
python scripts/run_preprocess.py parameters
```

## Outputs

Generated outputs are written to `outputs/`:

- `outputs/parks_with_quality_report.gpkg`
- `outputs/accessibility_baselines.gpkg`
- `outputs/baseline_summary.csv`
- `outputs/candidate_new_park_spots.gpkg`
- `outputs/optimization_actions_single.gpkg`
- `outputs/optimization_actions_multi.gpkg`
- `outputs/optimization_summary.csv`

## Validation

Static validation:

```bash
python - <<'PY'
import ast, pathlib
paths = list(pathlib.Path("src/park_selection").glob("*.py")) + list(pathlib.Path("scripts").glob("*.py"))
for path in paths:
    ast.parse(path.read_text())
print(f"syntax ok: {len(paths)} files")
PY
```

Full geospatial execution requires the input files described in [docs/INPUTS.md](docs/INPUTS.md).
