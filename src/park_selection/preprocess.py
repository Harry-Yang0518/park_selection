from __future__ import annotations

from glob import glob
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

from . import config
from .utils import find_column, minmax_scale, write_geodataframe


def clean_target_pois(
    input_glob: str = config.POI_SPLITS_GLOB,
    output_csv: Path = config.DEFAULT_CLEANED_POI_CSV,
    central_districts: list[str] | None = None,
) -> pd.DataFrame:
    districts = central_districts or config.CENTRAL_DISTRICTS
    frames = []
    for file_path in sorted(glob(input_glob)):
        df = pd.read_csv(file_path)
        for column in ["名称", "大类", "中类", "区县"]:
            if column not in df.columns:
                df[column] = ""
            df[column] = df[column].fillna("").astype(str)

        df = df.loc[df["区县"].isin(districts)].copy()
        if df.empty:
            continue

        text = df["名称"] + "|" + df["大类"] + "|" + df["中类"]
        transit = df["中类"].isin(config.TRANSIT_SUBCATEGORIES) | text.str.contains("公交|地铁", regex=True)
        toilet = df["中类"].isin(config.TOILET_SUBCATEGORIES) | text.str.contains("公厕|厕所|卫生间", regex=True)
        health = text.str.contains("|".join(config.HEALTH_KEYWORDS), regex=True)
        elderly = text.str.contains("|".join(config.ELDERLY_SERVICE_INCLUDE_KEYWORDS), regex=True)
        elderly = elderly & ~text.str.contains("|".join(config.ELDERLY_SERVICE_EXCLUDE_KEYWORDS), regex=True)

        filtered = df.loc[transit | toilet | health | elderly].copy()
        filtered["category_group"] = np.select(
            [transit.loc[filtered.index], toilet.loc[filtered.index], health.loc[filtered.index], elderly.loc[filtered.index]],
            ["Transport", "Toilet", "Health_Service", "Elderly_Service"],
            default="Other",
        )
        frames.append(filtered)

    if frames:
        result = pd.concat(frames, ignore_index=True)
        dedupe_cols = [column for column in ["lon_wgs", "lat_wgs", "名称"] if column in result.columns]
        if dedupe_cols:
            result = result.drop_duplicates(subset=dedupe_cols)
    else:
        result = pd.DataFrame()

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_csv, index=False, encoding="utf_8_sig")
    return result


def standardize_poi_csv(
    input_csv: Path = config.DEFAULT_CLEANED_POI_CSV,
    output_path: Path = config.DEFAULT_POIS_PATH,
    lon_col: str = "lon_wgs",
    lat_col: str = "lat_wgs",
) -> Path:
    df = pd.read_csv(input_csv)
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df[lon_col], df[lat_col]),
        crs="EPSG:4326",
    ).to_crs(epsg=3857)
    write_geodataframe(gdf, output_path)
    return output_path


def standardize_park_polygons(input_path: Path, output_path: Path = config.DEFAULT_PARK_POLYGONS_PATH) -> Path:
    parks = gpd.read_file(input_path).to_crs(epsg=3857)
    parks["real_area_m2"] = parks.geometry.area
    write_geodataframe(parks, output_path)
    return output_path


def compute_elderly_demand_layer(
    input_path: Path,
    output_path: Path = config.DEFAULT_DEMAND_PATH,
    population_col: str | None = None,
    ratio_col: str | None = None,
) -> Path:
    gdf = gpd.read_file(input_path).to_crs(epsg=3857)
    population = population_col or find_column(gdf, config.POPULATION_COLUMNS, required=True)
    ratio = ratio_col or find_column(gdf, config.ELDERLY_RATIO_COLUMNS, required=True)
    gdf["elderly_demand"] = (
        pd.to_numeric(gdf[population], errors="coerce").fillna(0)
        * pd.to_numeric(gdf[ratio], errors="coerce").fillna(0)
    )
    gdf["demand_index"] = minmax_scale(gdf["elderly_demand"]).to_numpy()
    write_geodataframe(gdf, output_path)
    return output_path


def report_parameters() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"parameter": "catchment_m", "value": config.REPORT_CATCHMENT_M},
            {"parameter": "decay_sigma_m", "value": config.REPORT_DECAY_SIGMA_M},
            {"parameter": "alpha_upgrade", "value": config.UPGRADE_DELTA},
            {"parameter": "beta_support", "value": config.SUPPORT_DELTA},
            {"parameter": "gamma_new_park", "value": config.NEW_PARK_DELTA},
            {"parameter": "cost_upgrade", "value": config.UPGRADE_COST},
            {"parameter": "cost_support", "value": config.SUPPORT_COST},
            {"parameter": "cost_new_park", "value": config.NEW_PARK_COST},
            {"parameter": "total_budget", "value": config.TOTAL_BUDGET},
        ]
    )
