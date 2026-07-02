# %%
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import matplotlib as mpl
import matplotlib.patheffects as path_effects
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter

# %%
ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = ROOT / "Enerdata_Odyssee_260702_122358.xlsx"
FIGURES = ROOT / "figures"
GISCO_URL = "https://gisco-services.ec.europa.eu/distribution/v2/countries/geojson/CNTR_RG_10M_2024_3035.geojson"
SOURCE_LABEL = "ODYSSEE/Enerdata export, 2026-07-02"
MAP_EXTENT = (2_150_000, 6_650_000, 1_300_000, 5_650_000)

COUNTRY_CODES = {
    "Austria": "AT",
    "Belgium": "BE",
    "Bulgaria": "BG",
    "Croatia": "HR",
    "Cyprus": "CY",
    "Czechia": "CZ",
    "Denmark": "DK",
    "Estonia": "EE",
    "Finland": "FI",
    "France": "FR",
    "Germany": "DE",
    "Greece": "EL",
    "Hungary": "HU",
    "Ireland": "IE",
    "Italy": "IT",
    "Latvia": "LV",
    "Lithuania": "LT",
    "Luxembourg": "LU",
    "Malta": "MT",
    "Netherlands": "NL",
    "Poland": "PL",
    "Portugal": "PT",
    "Romania": "RO",
    "Slovakia": "SK",
    "Slovenia": "SI",
    "Spain": "ES",
    "Sweden": "SE",
}

MAP_BINS = [-0.1, 1, 50, 150, 400, 800, np.inf]
MAP_LABELS = ["0", "1–50", "50–150", "150–400", "400–800", "800+"]
MAP_COLORS = [mpl.colormaps["Blues"](value) for value in np.linspace(0.18, 0.92, len(MAP_LABELS))]

# %%
def read_workbook(path: Path) -> tuple[pd.DataFrame, list[int], str, str]:
    frame = pd.read_excel(path, sheet_name="Odyssee_export")
    year_columns = [column for column in frame.columns if isinstance(column, int)]
    data = frame.loc[frame["Zone Name"].notna()].copy()
    data[year_columns] = data[year_columns].replace("n.a.", pd.NA).apply(pd.to_numeric, errors="coerce")
    data = data.rename(columns={"Zone Name": "country", "Title": "metric", "Unit": "unit"})
    data["country_code"] = data["country"].map(COUNTRY_CODES)
    metric = data["metric"].dropna().iloc[0]
    unit = data["unit"].dropna().iloc[0]
    return data, year_columns, metric, unit


def complete_history(frame: pd.DataFrame, years: list[int]) -> pd.DataFrame:
    start_year = years[0]
    end_year = years[-1]
    data = frame.loc[frame[years].notna().all(axis=1)].copy()
    data["start"] = data[start_year]
    data["end"] = data[end_year]
    data["change"] = data["end"] - data["start"]
    return data.sort_values("end", ascending=False)


def latest_snapshot(frame: pd.DataFrame, year: int) -> pd.DataFrame:
    data = frame.loc[frame[year].notna(), ["country", "country_code", year]].copy()
    data = data.rename(columns={year: "value"})
    missing_codes = data.loc[data["country_code"].isna(), "country"].tolist()
    if missing_codes:
        raise ValueError(f"Missing GISCO country codes: {missing_codes}")
    return data

# %%
def kwh_formatter(value: float, position: int) -> str:
    if value >= 1000:
        return f"{value / 1000:.1f}k"
    return f"{value:,.0f}"


def value_label(value: float) -> str:
    return f"{value:,.0f}"


def change_label(value: float) -> str:
    return f"{value:+,.0f}"


def save_figure(fig: plt.Figure, stem: str) -> None:
    FIGURES.mkdir(exist_ok=True)
    fig.savefig(FIGURES / f"{stem}.png", dpi=240, bbox_inches="tight")
    fig.savefig(FIGURES / f"{stem}.svg", bbox_inches="tight")
    plt.close(fig)

# %%
def plot_dumbbell_change(frame: pd.DataFrame, years: list[int], metric: str, unit: str) -> None:
    start_year = years[0]
    end_year = years[-1]
    data = complete_history(frame, years)
    y = np.arange(len(data))
    max_value = max(data["start"].max(), data["end"].max())

    fig, ax = plt.subplots(figsize=(11.5, 9.5))

    ax.hlines(y, data["start"], data["end"], color="#c5ccd3", linewidth=2.4, zorder=1)
    ax.scatter(data["start"], y, s=42, color="#a2a9b0", edgecolor="white", linewidth=0.8, zorder=3)
    ax.scatter(data["end"], y, s=58, color="#1f5f85", edgecolor="white", linewidth=0.8, zorder=4)

    for position, row in enumerate(data.itertuples(index=False)):
        label = f"{value_label(row.end)} ({change_label(row.change)})"
        x = max(row.start, row.end) + max_value * 0.016
        ax.text(x, position, label, va="center", ha="left", fontsize=8.8, color="#202124")

    ax.set_yticks(y)
    ax.set_yticklabels(data["country"], fontsize=9.5)
    ax.invert_yaxis()
    ax.set_xlabel(unit, fontsize=10)
    ax.xaxis.set_major_formatter(FuncFormatter(kwh_formatter))
    ax.grid(axis="x", color="#e8eaed", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color("#dadce0")
    ax.tick_params(axis="y", length=0)
    ax.set_xlim(0, max_value * 1.18)

    handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor="#a2a9b0", markeredgecolor="white", markersize=7, label=str(start_year)),
        Line2D([0], [0], marker="o", color="none", markerfacecolor="#1f5f85", markeredgecolor="white", markersize=8, label=str(end_year)),
    ]
    ax.legend(handles=handles, loc="lower right", frameon=False, fontsize=9)

    fig.text(0.01, 0.985, f"Air-cooling electricity per dwelling: {start_year} vs {end_year}", ha="left", va="top", fontsize=18, weight="bold", color="#202124")
    fig.text(0.01, 0.947, f"Complete country histories only; sorted by {end_year} value. Labels show {end_year} value and absolute change.", ha="left", va="top", fontsize=10.5, color="#5f6368")
    fig.text(0.01, 0.012, f"Metric: {metric}. Source: {SOURCE_LABEL}.", ha="left", va="bottom", fontsize=8.5, color="#5f6368")

    save_figure(fig, "air_cooling_change_dumbbell")

# %%
def map_bucket(value: float) -> str:
    index = int(np.searchsorted(MAP_BINS, value, side="right") - 1)
    index = max(0, min(index, len(MAP_LABELS) - 1))
    return MAP_LABELS[index]


def read_gisco() -> gpd.GeoDataFrame:
    return gpd.read_file(GISCO_URL)


def plot_map(frame: pd.DataFrame, year: int, metric: str, unit: str) -> int:
    snapshot = latest_snapshot(frame, year)
    world = read_gisco()
    merged = world.merge(snapshot, left_on="CNTR_ID", right_on="country_code", how="left")
    missing_geometry = sorted(set(snapshot["country_code"]) - set(world["CNTR_ID"]))
    if missing_geometry:
        raise ValueError(f"Missing GISCO geometries: {missing_geometry}")

    data = merged.loc[merged["value"].notna()].copy()
    data["bucket"] = data["value"].map(map_bucket)
    data["color"] = data["bucket"].map(dict(zip(MAP_LABELS, MAP_COLORS)))

    fig, ax = plt.subplots(figsize=(10.8, 9.2))

    world.plot(ax=ax, color="#f1f3f4", edgecolor="white", linewidth=0.35)
    data.plot(ax=ax, color=data["color"], edgecolor="white", linewidth=0.55)

    top = data.sort_values("value", ascending=False).head(5).copy()
    points = top.geometry.representative_point()
    label_offsets = {
        "Cyprus": (110_000, -35_000),
        "Malta": (0, -95_000),
        "Greece": (40_000, -35_000),
        "Croatia": (45_000, 55_000),
        "Italy": (-40_000, 20_000),
    }

    for row, point in zip(top.itertuples(index=False), points):
        dx, dy = label_offsets.get(row.country, (0, 0))
        text = ax.text(point.x + dx, point.y + dy, row.country, fontsize=8.5, ha="center", va="center", color="#202124", weight="bold", zorder=5)
        text.set_path_effects([path_effects.withStroke(linewidth=2.8, foreground="white")])

    handles = [Patch(facecolor="#f1f3f4", edgecolor="white", label="No data")]
    handles.extend(Patch(facecolor=color, edgecolor="white", label=label) for color, label in zip(MAP_COLORS, MAP_LABELS))
    ax.legend(handles=handles, title=f"{unit}, {year}", loc="lower left", frameon=False, fontsize=8.5, title_fontsize=9.5)

    ax.set_xlim(MAP_EXTENT[0], MAP_EXTENT[1])
    ax.set_ylim(MAP_EXTENT[2], MAP_EXTENT[3])
    ax.set_aspect("equal")
    ax.axis("off")

    fig.text(0.01, 0.985, f"Air-cooling electricity per dwelling, {year}", ha="left", va="top", fontsize=18, weight="bold", color="#202124")
    fig.text(0.01, 0.947, "Latest year in the workbook; grey countries have no numeric source value.", ha="left", va="top", fontsize=10.5, color="#5f6368")
    fig.text(0.01, 0.012, f"Metric: {metric}. Source: {SOURCE_LABEL}; Eurostat GISCO boundaries, EPSG:3035.", ha="left", va="bottom", fontsize=8.5, color="#5f6368")

    save_figure(fig, "air_cooling_2024_map")
    return len(missing_geometry)

# %%
def main() -> None:
    frame, years, metric, unit = read_workbook(WORKBOOK)
    graph_count = int(frame[years].notna().all(axis=1).sum())
    map_count = int(frame[years[-1]].notna().sum())

    plot_dumbbell_change(frame, years, metric, unit)
    map_unmatched = plot_map(frame, years[-1], metric, unit)

    print(f"years={years[0]}-{years[-1]}")
    print(f"graph_countries={graph_count}")
    print(f"map_countries={map_count}")
    print(f"map_unmatched={map_unmatched}")
    print(f"figures={FIGURES}")


if __name__ == "__main__":
    main()
