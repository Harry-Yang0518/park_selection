from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def minmax_scale(values: Iterable[float]) -> pd.Series:
    series = pd.Series(values, dtype=float)
    min_value = series.min()
    max_value = series.max()
    if pd.isna(min_value) or pd.isna(max_value) or np.isclose(max_value, min_value):
        return pd.Series(np.zeros(len(series)), index=series.index)
    return (series - min_value) / (max_value - min_value)


def gaussian_decay(distances_m: np.ndarray, radius_m: float, sigma_m: float) -> np.ndarray:
    distances = np.asarray(distances_m, dtype=float)
    decay = np.exp(-0.5 * (distances / sigma_m) ** 2)
    return np.where(distances <= radius_m, decay, 0.0)


def find_column(df: pd.DataFrame, candidates: Iterable[str], required: bool = True) -> str | None:
    exact = {column: column for column in df.columns}
    lowered = {column.lower(): column for column in df.columns}
    for candidate in candidates:
        if candidate in exact:
            return exact[candidate]
        if candidate.lower() in lowered:
            return lowered[candidate.lower()]
    if required:
        raise KeyError(f"None of these columns were found: {list(candidates)}")
    return None


def ensure_metric_crs(gdf, epsg: int = 3857):
    if gdf.crs is None:
        raise ValueError("GeoDataFrame has no CRS. Assign the source CRS before running this pipeline.")
    if gdf.crs.to_epsg() == epsg:
        return gdf
    return gdf.to_crs(epsg=epsg)


def geometry_xy(gdf) -> np.ndarray:
    geom = gdf.geometry
    if not geom.geom_type.isin(["Point", "MultiPoint"]).all():
        geom = geom.centroid
    return np.column_stack([geom.x.to_numpy(dtype=float), geom.y.to_numpy(dtype=float)])


def write_geodataframe(gdf, path: Path, layer: str | None = None) -> None:
    ensure_parent(path)
    if path.suffix.lower() == ".gpkg":
        gdf.to_file(path, layer=layer or path.stem, driver="GPKG")
    else:
        gdf.to_file(path, encoding="utf-8")


def weighted_mean(values: np.ndarray, weights: np.ndarray) -> float:
    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)
    total = float(weights.sum())
    if total <= 0:
        return 0.0
    return float(np.dot(weights, values) / total)
