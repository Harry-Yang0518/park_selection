# Data Policy and Expected Local Layout

Data files are not included in this GitHub submission. The repository only contains source code, documentation, and reproducibility scripts.

Place the project data locally under `dataset_structured/` when running the pipeline. This directory is ignored by git.

## Required Inputs

The default scripts expect these files:

```text
dataset_structured/
├── 01_tabular/
│   └── poi_converted_wgs/
│       └── splits/
│           └── poi_converted_wgs_part_*.csv
└── 05_processed/
    ├── cleaned_target_pois.csv
    └── standardized_layers/
        ├── elderly_demand_3857.shp
        ├── parks_poly_3857.shp
        ├── parks_with_quality_3857.shp
        ├── pois_3857.shp
        └── candidate_new_park_spots.shp
```

If a file is stored elsewhere, pass it explicitly with the relevant script arguments.

## Minimum Columns

Residential demand layer:

- geometry in a projected CRS, or source CRS that can be converted to `EPSG:3857`
- either `elderly_demand` or both `population` and `elder_rati`

Park layer:

- park geometry
- one quality column such as `park_quality`, `Qj_index`, or `norm_Qj`

POI table or layer:

- longitude/latitude columns for CSV standardization: `lon_wgs`, `lat_wgs`
- category text columns when rebuilding quality: `名称`, `大类`, `中类`

## Generated Files

Generated outputs go to `outputs/` and are also ignored by git.
