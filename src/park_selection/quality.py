from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

from . import config
from .utils import ensure_metric_crs, find_column, minmax_scale, write_geodataframe


QUALITY_COMPONENTS = [
    "area_norm",
    "transit_norm",
    "toilet_norm",
    "health_norm",
    "elderly_service_norm",
]


def classify_pois(gdf_pois: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    pois = gdf_pois.copy()
    name_col = find_column(pois, ["名称", "name", "NAME"], required=False)
    middle_col = find_column(pois, ["中类", "mid_category", "category"], required=False)
    major_col = find_column(pois, ["大类", "major_category"], required=False)

    empty = pd.Series("", index=pois.index)
    name = pois[name_col].fillna("").astype(str) if name_col else empty
    middle = pois[middle_col].fillna("").astype(str) if middle_col else empty
    major = pois[major_col].fillna("").astype(str) if major_col else empty
    text = name + "|" + middle + "|" + major

    transit = middle.isin(config.TRANSIT_SUBCATEGORIES) | text.str.contains("公交|地铁", regex=True)
    toilet = middle.isin(config.TOILET_SUBCATEGORIES) | text.str.contains("公厕|厕所|卫生间", regex=True)
    health = text.str.contains("|".join(config.HEALTH_KEYWORDS), regex=True)
    elderly_service = text.str.contains("|".join(config.ELDERLY_SERVICE_INCLUDE_KEYWORDS), regex=True)
    elderly_service = elderly_service & ~text.str.contains("|".join(config.ELDERLY_SERVICE_EXCLUDE_KEYWORDS), regex=True)

    pois["quality_category"] = np.select(
        [transit, toilet, health, elderly_service],
        ["transit", "toilet", "health", "elderly_service"],
        default="other",
    )
    return pois.loc[pois["quality_category"] != "other"].copy()


def compute_park_quality(
    parks: gpd.GeoDataFrame,
    pois: gpd.GeoDataFrame,
    support_buffer_m: float = config.QUALITY_SUPPORT_BUFFER_M,
) -> gpd.GeoDataFrame:
    parks_3857 = ensure_metric_crs(parks).copy()
    pois_3857 = ensure_metric_crs(pois).copy()

    if "real_area_m2" not in parks_3857.columns:
        parks_3857["real_area_m2"] = parks_3857.geometry.area

    classified = classify_pois(pois_3857)
    buffers = parks_3857[["geometry"]].copy()
    buffers["geometry"] = buffers.geometry.buffer(support_buffer_m)

    joined = gpd.sjoin(
        classified[["quality_category", "geometry"]],
        buffers,
        how="inner",
        predicate="within",
    )
    counts = joined.groupby(["index_right", "quality_category"]).size().unstack(fill_value=0)

    result = parks_3857.join(counts, how="left")
    for column in ["transit", "toilet", "health", "elderly_service"]:
        if column not in result.columns:
            result[column] = 0
        result[column] = result[column].fillna(0)

    result["area_norm"] = minmax_scale(result["real_area_m2"]).to_numpy()
    result["transit_norm"] = minmax_scale(result["transit"]).to_numpy()
    result["toilet_norm"] = minmax_scale(result["toilet"]).to_numpy()
    result["health_norm"] = minmax_scale(result["health"]).to_numpy()
    result["elderly_service_norm"] = minmax_scale(result["elderly_service"]).to_numpy()
    result["park_quality"] = result[QUALITY_COMPONENTS].mean(axis=1)
    result["Qj_index"] = result["park_quality"]
    return result


def run_quality(parks_path: Path, pois_path: Path, output_path: Path) -> Path:
    parks = gpd.read_file(parks_path)
    pois = gpd.read_file(pois_path)
    result = compute_park_quality(parks, pois)
    write_geodataframe(result, output_path)
    return output_path
