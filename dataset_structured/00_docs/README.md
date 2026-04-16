# Structured Dataset

This folder reorganizes the current `data/` exports into a cleaner package.

## Sections
- `00_docs`: human-readable overview files
- `01_tabular`: flat CSV datasets
- `02_vector_tables`: readable tables derived from vector GIS layers
- `03_raster`: raster metadata summaries
- `04_manifests`: machine-readable dataset catalog and source manifest

## Dataset List
- `poi_converted_wgs`: POI table with category labels and WGS84 longitude/latitude fields.
- `park_attributes`: Attribute table derived from the Shanghai park polygon shapefile.
- `elderly_population_attributes`: Attribute table derived from the filtered elderly population point shapefile.
- `accessibility_2sfca`: Point accessibility layer exported from GeoJSON into tabular form.
- `accessibility_e2sfca_optimized`: Optimized E2SFCA accessibility point layer exported into readable tables.
- `population_raster_metadata`: Metadata summary for the Shanghai population raster source.
