# %%
from __future__ import annotations

import json
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd
import matplotlib.patheffects as path_effects
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from matplotlib.patches import Patch, Polygon
from matplotlib.ticker import FuncFormatter

# %%
ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = ROOT / "Enerdata_Odyssee_260702_122358.xlsx"
FIGURES = ROOT / "figures"
MAP_URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_admin_0_countries.geojson"
SOURCE_LABEL = "ODYSSEE/Enerdata export, 2026-07-02"
EXTENT = (-12.5, 35.0, 35.5, 71.8)

SEGMENT_PALETTE = {
    "Large current market": "#c44536",
    "Fast riser": "#e9893a",
    "Emerging opportunity": "#437f97",
    "Low signal": "#9aa0a6",
}

MAP_BINS = [0, 1, 50, 150, 400, 800, np.inf]
MAP_LABELS = ["0", "1–50", "50–150", "150–400", "400–800", "800+"]
MAP_COLORS = ["#fff7ec", "#fee8c8", "#fdbb84", "#fc8d59", "#d7301f", "#7f0000"]

# %%
def read_workbook(path: Path) -> tuple[pd.DataFrame, list[int], str, str]:
    frame = pd.read_excel(path, sheet_name="Odyssee_export")
    year_columns = [column for column in frame.columns if isinstance(column, int)]
    data = frame.loc[frame["Zone Name"].notna()].copy()
    data[year_columns] = data[year_columns].replace("n.a.", pd.NA).apply(pd.to_numeric, errors="coerce")
    data = data.rename(columns={"Zone Name": "country", "Title": "metric", "Unit": "unit"})
    metric = data["metric"].dropna().iloc[0]
    unit = data["unit"].dropna().iloc[0]
    return data, year_columns, metric, unit


def add_segments(frame: pd.DataFrame, start_year: int, end_year: int) -> pd.DataFrame:
    data = frame.copy()
    data["start"] = data[start_year]
    data["end"] = data[end_year]
    data["change"] = data["end"] - data["start"]

    level_high = data["end"].quantile(0.75)
    growth_high = data["change"].quantile(0.75)
    level_mid = data["end"].quantile(0.50)
    growth_mid = data["change"].quantile(0.50)

    def classify(row: pd.Series) -> str:
        if row["end"] >= level_high:
            return "Large current market"
        if row["change"] >= growth_high:
            return "Fast riser"
        if row["end"] >= level_mid or row["change"] >= growth_mid:
            return "Emerging opportunity"
        return "Low signal"

    data["segment"] = data.apply(classify, axis=1)
    return data.sort_values("end")


def fetch_geojson(url: str) -> dict:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=45) as response:
        return json.load(response)

# %%
def polygon_rings(geometry: dict) -> list[np.ndarray]:
    if geometry["type"] == "Polygon":
        return [np.asarray(geometry["coordinates"][0])]
    if geometry["type"] == "MultiPolygon":
        return [np.asarray(polygon[0]) for polygon in geometry["coordinates"]]
    return []


def geometry_bounds(geometry: dict) -> tuple[float, float, float, float]:
    rings = polygon_rings(geometry)
    points = np.vstack(rings) if rings else np.empty((0, 2))
    return points[:, 0].min(), points[:, 1].min(), points[:, 0].max(), points[:, 1].max()


def intersects(bounds: tuple[float, float, float, float], extent: tuple[float, float, float, float]) -> bool:
    west, south, east, north = bounds
    x_min, y_min, x_max, y_max = extent
    return east >= x_min and west <= x_max and north >= y_min and south <= y_max


def country_name(feature: dict) -> str:
    properties = feature["properties"]
    return properties.get("ADMIN") or properties.get("NAME_LONG") or properties.get("NAME")


def feature_patches(feature: dict, extent: tuple[float, float, float, float]) -> list[Polygon]:
    patches = []
    for ring in polygon_rings(feature["geometry"]):
        bounds = ring[:, 0].min(), ring[:, 1].min(), ring[:, 0].max(), ring[:, 1].max()
        if intersects(bounds, extent):
            patches.append(Polygon(ring, closed=True))
    return patches


def draw_patch_collection(ax: plt.Axes, patches: list[Polygon], colors: list[str], edgecolor: str, linewidth: float) -> None:
    collection = PatchCollection(patches, facecolor=colors, edgecolor=edgecolor, linewidth=linewidth, zorder=2)
    ax.add_collection(collection)

# %%
def kwh_formatter(value: float, position: int) -> str:
    if value >= 1000:
        return f"{value / 1000:.1f}k"
    return f"{value:,.0f}"


def save_figure(fig: plt.Figure, stem: str) -> None:
    FIGURES.mkdir(exist_ok=True)
    fig.savefig(FIGURES / f"{stem}.png", dpi=240, bbox_inches="tight")
    fig.savefig(FIGURES / f"{stem}.svg", bbox_inches="tight")
    plt.close(fig)

# %%
def plot_segments(frame: pd.DataFrame, years: list[int], metric: str, unit: str) -> None:
    start_year = years[0]
    end_year = years[-1]
    data = add_segments(frame.loc[frame[years].notna().all(axis=1)], start_year, end_year)

    fig, ax = plt.subplots(figsize=(11, 9.5))
    y = np.arange(len(data))
    colors = [SEGMENT_PALETTE[segment] for segment in data["segment"]]

    ax.barh(y, data["end"], color=colors, height=0.7, edgecolor="white", linewidth=0.8)
    ax.scatter(data["start"], y, s=32, color="#202124", zorder=4, label=str(start_year))

    for position, row in enumerate(data.itertuples()):
        delta = row.change
        label = f"{row.end:,.0f} ({delta:+,.0f})"
        x = max(row.start, row.end) + data["end"].max() * 0.012
        ax.text(x, position, label, va="center", ha="left", fontsize=8.5, color="#202124")

    handles = [Patch(facecolor=color, label=label) for label, color in SEGMENT_PALETTE.items()]
    handles.append(plt.Line2D([0], [0], marker="o", color="none", markerfacecolor="#202124", markersize=6, label=str(start_year)))

    ax.set_yticks(y)
    ax.set_yticklabels(data["country"], fontsize=9)
    ax.set_xlabel(f"{unit}", fontsize=10)
    ax.xaxis.set_major_formatter(FuncFormatter(kwh_formatter))
    ax.grid(axis="x", color="#e8eaed", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color("#dadce0")
    ax.tick_params(axis="y", length=0)
    ax.set_xlim(0, data["end"].max() * 1.23)
    ax.legend(handles=handles, loc="lower right", frameon=False, fontsize=8.5, title="Segment")

    fig.text(0.01, 0.985, "EU air-cooling electricity per dwelling", ha="left", va="top", fontsize=18, weight="bold", color="#202124")
    fig.text(0.01, 0.947, f"Complete {start_year}–{end_year} histories only; labels show {end_year} value and change since {start_year}.", ha="left", va="top", fontsize=10.5, color="#5f6368")
    fig.text(0.01, 0.012, f"Metric: {metric}. Source: {SOURCE_LABEL}.", ha="left", va="bottom", fontsize=8.5, color="#5f6368")

    save_figure(fig, "air_cooling_opportunity_segments")

# %%
def map_color(value: float) -> tuple[str, str]:
    index = int(np.searchsorted(MAP_BINS, value, side="right") - 1)
    index = max(0, min(index, len(MAP_COLORS) - 1))
    return MAP_COLORS[index], MAP_LABELS[index]


def plot_map(frame: pd.DataFrame, year: int, metric: str, unit: str) -> None:
    data = frame.loc[frame[year].notna(), ["country", year]].copy()
    values = data.set_index("country")[year].to_dict()
    geojson = fetch_geojson(MAP_URL)

    fig, ax = plt.subplots(figsize=(10.8, 9.2))
    context_patches = []
    data_patches = []
    data_colors = []
    label_positions = {}

    for feature in geojson["features"]:
        name = country_name(feature)
        bounds = geometry_bounds(feature["geometry"])
        if not intersects(bounds, EXTENT):
            continue

        patches = feature_patches(feature, EXTENT)
        context_patches.extend(patches)

        if name in values:
            color, _ = map_color(values[name])
            data_patches.extend(patches)
            data_colors.extend([color] * len(patches))
            properties = feature["properties"]
            label_positions[name] = properties.get("LABEL_X"), properties.get("LABEL_Y")

    draw_patch_collection(ax, context_patches, ["#f1f3f4"] * len(context_patches), "#ffffff", 0.45)
    draw_patch_collection(ax, data_patches, data_colors, "#ffffff", 0.55)

    top = data.sort_values(year, ascending=False).head(5)
    for row in top.itertuples(index=False):
        x, y = label_positions.get(row.country, (None, None))
        if x is None or y is None:
            continue
        text = ax.text(x, y, row.country, fontsize=8.5, ha="center", va="center", color="#202124", weight="bold", zorder=5)
        text.set_path_effects([path_effects.withStroke(linewidth=2.8, foreground="white")])

    legend_handles = [Patch(facecolor="#f1f3f4", edgecolor="white", label="No data")]
    legend_handles.extend(Patch(facecolor=color, edgecolor="white", label=label) for color, label in zip(MAP_COLORS, MAP_LABELS))

    ax.legend(handles=legend_handles, title=f"{unit}, {year}", loc="lower left", frameon=False, fontsize=8.5, title_fontsize=9.5)
    ax.set_xlim(EXTENT[0], EXTENT[2])
    ax.set_ylim(EXTENT[1], EXTENT[3])
    ax.set_aspect("equal")
    ax.axis("off")

    fig.text(0.01, 0.985, f"Air-cooling electricity per dwelling, {year}", ha="left", va="top", fontsize=18, weight="bold", color="#202124")
    fig.text(0.01, 0.947, "Latest snapshot year; countries without numeric values are greyed out.", ha="left", va="top", fontsize=10.5, color="#5f6368")
    fig.text(0.01, 0.012, f"Metric: {metric}. Source: {SOURCE_LABEL}; Natural Earth boundaries.", ha="left", va="bottom", fontsize=8.5, color="#5f6368")

    save_figure(fig, "air_cooling_2024_map")

# %%
def main() -> None:
    frame, years, metric, unit = read_workbook(WORKBOOK)
    graph_count = int(frame[years].notna().all(axis=1).sum())
    map_count = int(frame[years[-1]].notna().sum())

    plot_segments(frame, years, metric, unit)
    plot_map(frame, years[-1], metric, unit)

    print(f"years={years[0]}-{years[-1]}")
    print(f"graph_countries={graph_count}")
    print(f"map_countries={map_count}")
    print(f"figures={FIGURES}")


if __name__ == "__main__":
    main()
