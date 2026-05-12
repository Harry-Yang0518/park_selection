# Input Layout

The default pipeline reads spatial and tabular inputs from `dataset_structured/`. The paths can also be overridden with command-line arguments.

## Expected Inputs

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

## Generated Outputs

Generated outputs go to `outputs/`.
