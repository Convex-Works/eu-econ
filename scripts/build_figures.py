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
from matplotlib.patches import Rectangle
from matplotlib.ticker import FuncFormatter

# %%
ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = ROOT / "Enerdata_Odyssee_260702_122358.xlsx"
FIGURES = ROOT / "figures"
GISCO_URL = "https://gisco-services.ec.europa.eu/distribution/v2/countries/geojson/CNTR_RG_10M_2024_3035.geojson"
SOURCE_LABEL = "ODYSSEE/Enerdata export, 2026-07-02"
MAP_EXTENT = (1_750_000, 6_720_000, 1_320_000, 5_620_000)

INK = "#14161a"
MUTED = "#69707a"
GRID = "#e8e3db"
PAPER = "#fbfaf7"
LAND = "#eef0f1"
BORDER = "#ffffff"
START = "#aeb7c0"
END = "#075a78"
GAIN = "#0f7b83"
DROP = "#d9684a"
FLAT = "#c8ced4"

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
MAP_COLORS = ["#e8f4f8", "#c7e4ef", "#8dc9df", "#46a1c4", "#0878a8", "#03486f"]

# %%
def apply_theme() -> None:
    mpl.rcParams.update(
        {
            "figure.facecolor": PAPER,
            "axes.facecolor": PAPER,
            "savefig.facecolor": PAPER,
            "font.family": "sans-serif",
            "font.sans-serif": ["Inter", "Helvetica Neue", "Arial", "DejaVu Sans"],
            "axes.titleweight": "bold",
            "axes.labelcolor": INK,
            "xtick.color": INK,
            "ytick.color": INK,
            "text.color": INK,
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


apply_theme()

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
    fig.savefig(FIGURES / f"{stem}.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIGURES / f"{stem}.svg", bbox_inches="tight")
    plt.close(fig)

# %%
def change_color(value: float) -> str:
    if value > 0.5:
        return GAIN
    if value < -0.5:
        return DROP
    return FLAT


def plot_dumbbell_change(frame: pd.DataFrame, years: list[int], metric: str, unit: str) -> None:
    start_year = years[0]
    end_year = years[-1]
    data = complete_history(frame, years)
    y = np.arange(len(data))
    max_value = max(data["start"].max(), data["end"].max())

    fig = plt.figure(figsize=(11.8, 9.8))
    ax = fig.add_axes([0.17, 0.12, 0.78, 0.74])

    for position, row in enumerate(data.itertuples(index=False)):
        ax.hlines(position, row.start, row.end, color=change_color(row.change), linewidth=3.2, alpha=0.82, zorder=1)

    ax.scatter(data["start"], y, s=58, color=START, edgecolor=PAPER, linewidth=1.5, zorder=3)
    ax.scatter(data["end"], y, s=76, color=END, edgecolor=PAPER, linewidth=1.5, zorder=4)

    for position, row in enumerate(data.itertuples(index=False)):
        label = f"{value_label(row.end)} ({change_label(row.change)})"
        x = max(row.start, row.end) + max_value * 0.018
        ax.text(x, position, label, va="center", ha="left", fontsize=9.8, color=INK)

    ax.set_yticks(y)
    ax.set_yticklabels(data["country"], fontsize=10.5)
    ax.invert_yaxis()
    ax.set_xlabel(unit, fontsize=11.5, labelpad=10)
    ax.xaxis.set_major_formatter(FuncFormatter(kwh_formatter))
    ax.grid(axis="x", color=GRID, linewidth=1.05)
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color("#d8d2c8")
    ax.spines["bottom"].set_linewidth(1.2)
    ax.tick_params(axis="x", labelsize=10.5, pad=6)
    ax.tick_params(axis="y", length=0, pad=8)
    ax.set_xlim(-max_value * 0.01, max_value * 1.22)

    handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=START, markeredgecolor=PAPER, markersize=8, label=str(start_year)),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=END, markeredgecolor=PAPER, markersize=9, label=str(end_year)),
    ]
    ax.legend(handles=handles, loc="lower right", frameon=False, fontsize=10.5, borderpad=0.2, labelspacing=0.7)

    fig.text(0.04, 0.965, "Air-cooling electricity per dwelling", ha="left", va="top", fontsize=26, weight="bold", color=INK)
    fig.text(0.04, 0.922, f"{start_year} → {end_year} · {unit}", ha="left", va="top", fontsize=13.5, color=MUTED)
    fig.text(0.04, 0.035, f"Labels show {end_year} value and Δ since {start_year}. Complete {start_year}–{end_year} histories only. Source: {SOURCE_LABEL}.", ha="left", va="bottom", fontsize=9.3, color=MUTED)

    save_figure(fig, "air_cooling_change_dumbbell")

# %%
def map_bucket(value: float) -> str:
    index = int(np.searchsorted(MAP_BINS, value, side="right") - 1)
    index = max(0, min(index, len(MAP_LABELS) - 1))
    return MAP_LABELS[index]


def read_gisco() -> gpd.GeoDataFrame:
    return gpd.read_file(GISCO_URL)


def legend_row(fig: plt.Figure, unit: str, year: int) -> None:
    ax = fig.add_axes([0.18, 0.075, 0.64, 0.06])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(0.0, 0.68, f"{unit}, {year}", ha="left", va="center", fontsize=10.8, weight="semibold", color=INK)
    items = [(LAND, "No data"), *zip(MAP_COLORS, MAP_LABELS)]
    x = 0.0
    for color, label in items:
        ax.add_patch(Rectangle((x, 0.18), 0.035, 0.22, facecolor=color, edgecolor=BORDER, linewidth=0.8))
        ax.text(x + 0.044, 0.29, label, ha="left", va="center", fontsize=9.5, color=INK)
        x += 0.135 if label != "No data" else 0.17


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

    fig = plt.figure(figsize=(11.4, 9.4))
    ax = fig.add_axes([0.04, 0.15, 0.92, 0.70])

    world.plot(ax=ax, color=LAND, edgecolor=BORDER, linewidth=0.34)
    data.plot(ax=ax, color=data["color"], edgecolor=BORDER, linewidth=0.72)

    top = data.sort_values("value", ascending=False).head(5).copy()
    points = top.geometry.representative_point()
    label_offsets = {
        "Cyprus": (-12_000, -52_000),
        "Malta": (0, -92_000),
        "Greece": (25_000, -34_000),
        "Croatia": (40_000, 56_000),
        "Italy": (-38_000, 22_000),
    }

    for row, point in zip(top.itertuples(index=False), points):
        dx, dy = label_offsets.get(row.country, (0, 0))
        text = ax.text(point.x + dx, point.y + dy, row.country, fontsize=9.2, ha="center", va="center", color=INK, weight="bold", zorder=5)
        text.set_path_effects([path_effects.withStroke(linewidth=3.0, foreground=PAPER)])

    ax.set_xlim(MAP_EXTENT[0], MAP_EXTENT[1])
    ax.set_ylim(MAP_EXTENT[2], MAP_EXTENT[3])
    ax.set_aspect("equal")
    ax.axis("off")

    legend_row(fig, unit, year)
    fig.text(0.04, 0.965, "Air-cooling electricity per dwelling", ha="left", va="top", fontsize=26, weight="bold", color=INK)
    fig.text(0.04, 0.922, f"{year} snapshot · {unit}", ha="left", va="top", fontsize=13.5, color=MUTED)
    fig.text(0.04, 0.035, f"Source: {SOURCE_LABEL}; Eurostat GISCO boundaries, EPSG:3035.", ha="left", va="bottom", fontsize=9.3, color=MUTED)

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
