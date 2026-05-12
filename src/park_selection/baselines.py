from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from . import config
from .utils import (
    ensure_metric_crs,
    find_column,
    gaussian_decay,
    geometry_xy,
    minmax_scale,
    weighted_mean,
    write_geodataframe,
)


@dataclass
class BaselineArrays:
    residential_coords: np.ndarray
    park_coords: np.ndarray
    park_quality: np.ndarray
    demand: np.ndarray
    multi_access: np.ndarray
    single_access: np.ndarray
    nearest_distance_m: np.ndarray
    reachable_park_count: np.ndarray


def add_elderly_demand(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    result = gdf.copy()
    demand_col = find_column(result, config.DEMAND_COLUMNS, required=False)
    if demand_col:
        result["elderly_demand"] = pd.to_numeric(result[demand_col], errors="coerce").fillna(0)
        return result

    population_col = find_column(result, config.POPULATION_COLUMNS, required=True)
    ratio_col = find_column(result, config.ELDERLY_RATIO_COLUMNS, required=True)
    result["elderly_demand"] = (
        pd.to_numeric(result[population_col], errors="coerce").fillna(0)
        * pd.to_numeric(result[ratio_col], errors="coerce").fillna(0)
    )
    return result


def add_park_quality(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    result = gdf.copy()
    quality_col = find_column(result, config.QUALITY_COLUMNS, required=True)
    result["park_quality"] = pd.to_numeric(result[quality_col], errors="coerce").fillna(0)
    return result


def compute_accessibility_arrays(
    residential: gpd.GeoDataFrame,
    parks: gpd.GeoDataFrame,
    radius_m: float = config.REPORT_CATCHMENT_M,
    sigma_m: float = config.REPORT_DECAY_SIGMA_M,
) -> BaselineArrays:
    residential_3857 = ensure_metric_crs(add_elderly_demand(residential))
    parks_3857 = ensure_metric_crs(add_park_quality(parks))

    res_coords = geometry_xy(residential_3857)
    park_coords = geometry_xy(parks_3857)
    park_quality = parks_3857["park_quality"].to_numpy(dtype=float)
    demand = residential_3857["elderly_demand"].to_numpy(dtype=float)

    tree = cKDTree(park_coords)
    neighbors_by_residential = tree.query_ball_point(res_coords, r=radius_m)

    multi_access = np.zeros(len(res_coords), dtype=float)
    single_access = np.zeros(len(res_coords), dtype=float)
    nearest_distance_m = np.full(len(res_coords), np.nan, dtype=float)
    reachable_park_count = np.zeros(len(res_coords), dtype=int)

    for idx, neighbors in enumerate(neighbors_by_residential):
        if not neighbors:
            continue
        neighbor_idx = np.asarray(neighbors, dtype=int)
        distances = np.linalg.norm(park_coords[neighbor_idx] - res_coords[idx], axis=1)
        terms = park_quality[neighbor_idx] * gaussian_decay(distances, radius_m, sigma_m)
        multi_access[idx] = float(terms.sum())
        single_access[idx] = float(terms.max())
        nearest_distance_m[idx] = float(distances.min())
        reachable_park_count[idx] = int(len(neighbor_idx))

    return BaselineArrays(
        residential_coords=res_coords,
        park_coords=park_coords,
        park_quality=park_quality,
        demand=demand,
        multi_access=multi_access,
        single_access=single_access,
        nearest_distance_m=nearest_distance_m,
        reachable_park_count=reachable_park_count,
    )


def attach_accessibility_columns(
    residential: gpd.GeoDataFrame,
    arrays: BaselineArrays,
) -> gpd.GeoDataFrame:
    result = ensure_metric_crs(add_elderly_demand(residential)).copy()
    result["multi_access"] = arrays.multi_access
    result["single_access"] = arrays.single_access
    result["nearest_distance_m"] = arrays.nearest_distance_m
    result["reachable_park_count"] = arrays.reachable_park_count
    result["weighted_multi_access"] = result["elderly_demand"] * result["multi_access"]
    result["weighted_single_access"] = result["elderly_demand"] * result["single_access"]
    result["demand_norm"] = minmax_scale(result["elderly_demand"]).to_numpy()
    result["multi_access_norm"] = minmax_scale(result["multi_access"]).to_numpy()
    result["single_access_norm"] = minmax_scale(result["single_access"]).to_numpy()
    result["gap_score"] = result["demand_norm"] * (1.0 - result["multi_access_norm"])
    return result


def baseline_summary(gdf: gpd.GeoDataFrame) -> pd.DataFrame:
    demand = gdf["elderly_demand"].to_numpy(dtype=float)
    rows = [
        {
            "model": "single_access_baseline",
            "score": weighted_mean(gdf["single_access"].to_numpy(dtype=float), demand),
            "weighted_total": float(gdf["weighted_single_access"].sum()),
        },
        {
            "model": "multi_access_baseline",
            "score": weighted_mean(gdf["multi_access"].to_numpy(dtype=float), demand),
            "weighted_total": float(gdf["weighted_multi_access"].sum()),
        },
    ]
    return pd.DataFrame(rows)


def candidate_sites_from_gap(gdf: gpd.GeoDataFrame, top_fraction: float = 0.01) -> gpd.GeoDataFrame:
    if "gap_score" not in gdf.columns:
        raise KeyError("Run attach_accessibility_columns before deriving gap candidates.")
    n = max(1, int(round(len(gdf) * top_fraction)))
    candidates = gdf.sort_values("gap_score", ascending=False).head(n).copy()
    candidates["candidate_rank"] = np.arange(1, len(candidates) + 1)
    return candidates


def run_baselines(
    demand_path: Path,
    parks_path: Path,
    output_path: Path,
    summary_path: Path,
    candidates_path: Path | None = None,
    candidate_fraction: float = 0.01,
) -> tuple[Path, Path]:
    residential = gpd.read_file(demand_path)
    parks = gpd.read_file(parks_path)
    arrays = compute_accessibility_arrays(residential, parks)
    result = attach_accessibility_columns(residential, arrays)
    write_geodataframe(result, output_path)

    summary = baseline_summary(result)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(summary_path, index=False)

    if candidates_path is not None:
        candidates = candidate_sites_from_gap(result, top_fraction=candidate_fraction)
        write_geodataframe(candidates, candidates_path)

    return output_path, summary_path
