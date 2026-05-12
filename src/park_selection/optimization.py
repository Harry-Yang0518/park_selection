"""Budgeted intervention optimization.

Single-access and multi-access portfolios are solved independently and reported
without cross-model score adjustment.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point

from . import config
from .baselines import add_elderly_demand, add_park_quality, compute_accessibility_arrays
from .utils import ensure_metric_crs, find_column, gaussian_decay, geometry_xy, weighted_mean, write_geodataframe


@dataclass
class ActionItem:
    action_id: str
    action_type: str
    site_name: str
    source_kind: str
    site_index: int
    x: float
    y: float
    cost: int
    quality_delta: float
    multi_gain: float
    single_gain: float


def _site_name(gdf: gpd.GeoDataFrame, idx: int, prefix: str) -> str:
    column = find_column(gdf, config.PARK_NAME_COLUMNS, required=False)
    if column is None:
        return f"{prefix}_{idx}"
    value = gdf.iloc[idx][column]
    if pd.isna(value) or str(value).strip() == "":
        return f"{prefix}_{idx}"
    return str(value)


def _weighted_action_gain(coords: np.ndarray, demand: np.ndarray, action_coord: np.ndarray, delta: float) -> float:
    distances = np.linalg.norm(coords - action_coord, axis=1)
    impact = delta * gaussian_decay(distances, config.REPORT_CATCHMENT_M, config.REPORT_DECAY_SIGMA_M)
    return float(np.dot(demand, impact))


def _single_action_gain(
    current_best: np.ndarray,
    coords: np.ndarray,
    demand: np.ndarray,
    action_coord: np.ndarray,
    action_quality: float,
) -> float:
    distances = np.linalg.norm(coords - action_coord, axis=1)
    candidate = action_quality * gaussian_decay(distances, config.REPORT_CATCHMENT_M, config.REPORT_DECAY_SIGMA_M)
    gain = np.maximum(current_best, candidate) - current_best
    return float(np.dot(demand, gain))


def build_action_pool(
    residential: gpd.GeoDataFrame,
    parks: gpd.GeoDataFrame,
    candidates: gpd.GeoDataFrame,
) -> list[ActionItem]:
    residential_3857 = ensure_metric_crs(add_elderly_demand(residential))
    parks_3857 = ensure_metric_crs(add_park_quality(parks))
    candidates_3857 = ensure_metric_crs(candidates)
    arrays = compute_accessibility_arrays(residential_3857, parks_3857)

    res_coords = arrays.residential_coords
    demand = arrays.demand
    park_coords = arrays.park_coords
    park_quality = arrays.park_quality
    candidate_coords = geometry_xy(candidates_3857)
    current_best = arrays.single_access

    actions: list[ActionItem] = []
    for idx, coord in enumerate(park_coords):
        site_name = _site_name(parks_3857, idx, "park")
        upgraded_quality = park_quality[idx] + config.UPGRADE_DELTA
        support_quality = park_quality[idx] + config.SUPPORT_DELTA
        actions.append(
            ActionItem(
                action_id=f"upgrade_{idx}",
                action_type="upgrade_existing_park",
                site_name=site_name,
                source_kind="existing_park",
                site_index=idx,
                x=float(coord[0]),
                y=float(coord[1]),
                cost=config.UPGRADE_COST,
                quality_delta=config.UPGRADE_DELTA,
                multi_gain=_weighted_action_gain(res_coords, demand, coord, config.UPGRADE_DELTA),
                single_gain=_single_action_gain(current_best, res_coords, demand, coord, upgraded_quality),
            )
        )
        actions.append(
            ActionItem(
                action_id=f"support_{idx}",
                action_type="add_support_facility",
                site_name=site_name,
                source_kind="existing_park",
                site_index=idx,
                x=float(coord[0]),
                y=float(coord[1]),
                cost=config.SUPPORT_COST,
                quality_delta=config.SUPPORT_DELTA,
                multi_gain=_weighted_action_gain(res_coords, demand, coord, config.SUPPORT_DELTA),
                single_gain=_single_action_gain(current_best, res_coords, demand, coord, support_quality),
            )
        )

    for idx, coord in enumerate(candidate_coords):
        actions.append(
            ActionItem(
                action_id=f"new_park_{idx}",
                action_type="build_new_park",
                site_name=f"candidate_new_park_{idx}",
                source_kind="gap_candidate",
                site_index=idx,
                x=float(coord[0]),
                y=float(coord[1]),
                cost=config.NEW_PARK_COST,
                quality_delta=config.NEW_PARK_DELTA,
                multi_gain=_weighted_action_gain(res_coords, demand, coord, config.NEW_PARK_DELTA),
                single_gain=_single_action_gain(current_best, res_coords, demand, coord, config.NEW_PARK_DELTA),
            )
        )
    return actions


def solve_budgeted_actions(
    actions: list[ActionItem],
    model: str,
    budget: int = config.TOTAL_BUDGET,
) -> list[ActionItem]:
    if model not in {"single", "multi"}:
        raise ValueError("model must be 'single' or 'multi'")
    value_attr = "single_gain" if model == "single" else "multi_gain"

    dp: list[tuple[float, list[int]]] = [(0.0, []) for _ in range(budget + 1)]
    for item_idx, item in enumerate(actions):
        cost = int(item.cost)
        value = float(getattr(item, value_attr))
        for current_budget in range(budget, cost - 1, -1):
            candidate_value = dp[current_budget - cost][0] + value
            if candidate_value > dp[current_budget][0] + 1e-12:
                dp[current_budget] = (candidate_value, dp[current_budget - cost][1] + [item_idx])

    selected = [actions[idx] for idx in dp[budget][1]]
    selected.sort(key=lambda action: getattr(action, value_attr), reverse=True)
    return selected


def actions_to_gdf(actions: list[ActionItem], model: str) -> gpd.GeoDataFrame:
    value_attr = "single_gain" if model == "single" else "multi_gain"
    rows = []
    for rank, action in enumerate(actions, start=1):
        rows.append(
            {
                "rank": rank,
                "optimization_model": f"{model}_access",
                "action_id": action.action_id,
                "action_type": action.action_type,
                "site_name": action.site_name,
                "source_kind": action.source_kind,
                "site_index": action.site_index,
                "cost": action.cost,
                "quality_delta": action.quality_delta,
                "objective_gain": getattr(action, value_attr),
                "multi_gain": action.multi_gain,
                "single_gain": action.single_gain,
                "geometry": Point(action.x, action.y),
            }
        )
    return gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:3857")


def _multi_final_access(arrays, selected: list[ActionItem]) -> np.ndarray:
    final = arrays.multi_access.copy()
    for action in selected:
        coord = np.array([action.x, action.y], dtype=float)
        distances = np.linalg.norm(arrays.residential_coords - coord, axis=1)
        final += action.quality_delta * gaussian_decay(
            distances,
            config.REPORT_CATCHMENT_M,
            config.REPORT_DECAY_SIGMA_M,
        )
    return final


def _single_final_access(parks: gpd.GeoDataFrame, arrays, selected: list[ActionItem]) -> np.ndarray:
    quality = arrays.park_quality.copy()
    new_terms = []
    for action in selected:
        coord = np.array([action.x, action.y], dtype=float)
        distances = np.linalg.norm(arrays.residential_coords - coord, axis=1)
        decay = gaussian_decay(distances, config.REPORT_CATCHMENT_M, config.REPORT_DECAY_SIGMA_M)
        if action.source_kind == "existing_park":
            quality[action.site_index] += action.quality_delta
        else:
            new_terms.append(action.quality_delta * decay)

    scores = []
    for idx, coord in enumerate(arrays.park_coords):
        distances = np.linalg.norm(arrays.residential_coords - coord, axis=1)
        decay = gaussian_decay(distances, config.REPORT_CATCHMENT_M, config.REPORT_DECAY_SIGMA_M)
        scores.append(quality[idx] * decay)
    scores.extend(new_terms)
    if not scores:
        return np.zeros(len(arrays.residential_coords))
    return np.vstack(scores).max(axis=0)


def optimization_summary(
    residential: gpd.GeoDataFrame,
    parks: gpd.GeoDataFrame,
    selected_single: list[ActionItem],
    selected_multi: list[ActionItem],
) -> pd.DataFrame:
    arrays = compute_accessibility_arrays(residential, parks)
    demand = arrays.demand
    single_final = _single_final_access(parks, arrays, selected_single)
    multi_final = _multi_final_access(arrays, selected_multi)
    single_current = weighted_mean(arrays.single_access, demand)
    multi_current = weighted_mean(arrays.multi_access, demand)
    rows = [
        {
            "model": "single_access",
            "current_score": single_current,
            "optimized_score": weighted_mean(single_final, demand),
            "absolute_gain": weighted_mean(single_final, demand) - single_current,
            "percent_gain": (weighted_mean(single_final, demand) / single_current - 1.0) if single_current > 0 else 0.0,
            "selected_actions": len(selected_single),
            "total_cost": sum(action.cost for action in selected_single),
        },
        {
            "model": "multi_access",
            "current_score": multi_current,
            "optimized_score": weighted_mean(multi_final, demand),
            "absolute_gain": weighted_mean(multi_final, demand) - multi_current,
            "percent_gain": (weighted_mean(multi_final, demand) / multi_current - 1.0) if multi_current > 0 else 0.0,
            "selected_actions": len(selected_multi),
            "total_cost": sum(action.cost for action in selected_multi),
        },
    ]
    return pd.DataFrame(rows)


def run_optimization(
    demand_path: Path,
    parks_path: Path,
    candidates_path: Path,
    output_dir: Path,
    budget: int = config.TOTAL_BUDGET,
) -> tuple[Path, Path, Path]:
    residential = gpd.read_file(demand_path)
    parks = gpd.read_file(parks_path)
    candidates = gpd.read_file(candidates_path)

    actions = build_action_pool(residential, parks, candidates)
    selected_single = solve_budgeted_actions(actions, "single", budget=budget)
    selected_multi = solve_budgeted_actions(actions, "multi", budget=budget)

    output_dir.mkdir(parents=True, exist_ok=True)
    single_path = output_dir / "optimization_actions_single.gpkg"
    multi_path = output_dir / "optimization_actions_multi.gpkg"
    summary_path = output_dir / "optimization_summary.csv"

    write_geodataframe(actions_to_gdf(selected_single, "single"), single_path, layer="actions")
    write_geodataframe(actions_to_gdf(selected_multi, "multi"), multi_path, layer="actions")
    optimization_summary(residential, parks, selected_single, selected_multi).to_csv(summary_path, index=False)
    return single_path, multi_path, summary_path
