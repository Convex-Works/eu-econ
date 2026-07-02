# %%
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.ticker import FuncFormatter

# %%
ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = ROOT / "Enerdata_Odyssee_260702_122358.xlsx"
DEGREE_DAYS_WORKBOOK = ROOT / "Enerdata_Odyssee_260702_130403.xlsx"
FIGURES = ROOT / "figures"
GISCO_URL = "https://gisco-services.ec.europa.eu/distribution/v2/countries/geojson/CNTR_RG_10M_2024_3035.geojson"
SOURCE_LABEL = "ODYSSEE/Enerdata export, 2026-07-02"
SVG_METADATA = {"Date": "2026-07-02"}
MAP_EXTENT = (2_420_000, 6_780_000, 1_420_000, 5_360_000)

INK = "#111111"
MUTED = "#666666"
GRID = "#e4e4e4"
PAPER = "#ffffff"
LAND = "#f0f0f0"
BORDER = "#ffffff"
START = "#ffffff"
START_EDGE = "#9a9a9a"
END = "#111111"
CONNECTOR = "#b8b8b8"
LABEL_LINE = "#d8d8d8"

REGION_ORDER = ["North", "West", "East", "South"]
REGION_COLORS = {
    "North": "#b5b5b5",
    "West": "#858585",
    "East": "#4d4d4d",
    "South": "#111111",
}

COUNTRY_REGIONS = {
    "Austria": "West",
    "Belgium": "West",
    "Bulgaria": "East",
    "Croatia": "South",
    "Cyprus": "South",
    "Czechia": "East",
    "Denmark": "North",
    "Estonia": "North",
    "Finland": "North",
    "France": "West",
    "Germany": "West",
    "Greece": "South",
    "Hungary": "East",
    "Ireland": "North",
    "Italy": "South",
    "Latvia": "North",
    "Lithuania": "North",
    "Luxembourg": "West",
    "Malta": "South",
    "Netherlands": "West",
    "Poland": "East",
    "Portugal": "South",
    "Romania": "East",
    "Slovakia": "East",
    "Slovenia": "South",
    "Spain": "South",
    "Sweden": "North",
}

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
MAP_COLORS = ["#e8e8e8", "#d4d4d4", "#b5b5b5", "#858585", "#4d4d4d", "#111111"]
MAP_CONTEXT_CODES = {
    "AD",
    "AL",
    "BA",
    "BY",
    "CH",
    "LI",
    "MC",
    "MD",
    "ME",
    "MK",
    "NO",
    "RS",
    "SM",
    "UA",
    "UK",
    "VA",
    "XK",
    *COUNTRY_CODES.values(),
}

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
            "svg.hashsalt": "convex-eu-econ",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


apply_theme()

# %%
def read_workbook(path: Path) -> tuple[pd.DataFrame, list[int], str]:
    frame = pd.read_excel(path, sheet_name="Odyssee_export")
    year_columns = [column for column in frame.columns if isinstance(column, int)]
    data = frame.loc[frame["Zone Name"].notna()].copy()
    data[year_columns] = data[year_columns].replace("n.a.", pd.NA).apply(pd.to_numeric, errors="coerce")
    data = data.rename(columns={"Zone Name": "country", "Unit": "unit"})
    data["country_code"] = data["country"].map(COUNTRY_CODES)
    unit = data["unit"].dropna().iloc[0]
    return data, year_columns, unit


def complete_history(frame: pd.DataFrame, years: list[int]) -> pd.DataFrame:
    start_year = years[0]
    end_year = years[-1]
    data = frame.loc[frame[years].notna().all(axis=1)].copy()
    data["start"] = data[start_year]
    data["end"] = data[end_year]
    data["change"] = data["end"] - data["start"]
    return data.loc[data["end"].gt(0)].sort_values("end", ascending=False)


def latest_snapshot(frame: pd.DataFrame, year: int) -> pd.DataFrame:
    data = frame.loc[frame[year].notna(), ["country", "country_code", year]].copy()
    data = data.rename(columns={year: "value"})
    missing_codes = data.loc[data["country_code"].isna(), "country"].tolist()
    if missing_codes:
        raise ValueError(f"Missing GISCO country codes: {missing_codes}")
    return data


def regional_degree_days(
    degree_frame: pd.DataFrame,
    degree_years: list[int],
    electricity_frame: pd.DataFrame,
    electricity_year: int,
) -> tuple[pd.DataFrame, int]:
    countries = set(electricity_frame.loc[electricity_frame[electricity_year].notna(), "country"])
    data = degree_frame.loc[
        degree_frame["country"].isin(countries)
        & degree_frame[degree_years].notna().all(axis=1)
        & degree_frame["country"].isin(COUNTRY_REGIONS)
    ].copy()
    data["region"] = data["country"].map(COUNTRY_REGIONS)
    regional = data.groupby("region")[degree_years].median().reindex(REGION_ORDER).dropna(how="all")
    return regional, len(data)

# %%
def kwh_formatter(value: float, position: int) -> str:
    if value >= 1000:
        return f"{value / 1000:.1f}k"
    return f"{value:,.0f}"


def value_label(value: float) -> str:
    return f"{value:,.0f}"


def change_label(value: float) -> str:
    return f"{value:+,.0f}"


def clean_svg(path: Path) -> None:
    path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")


def label_positions(values: pd.Series, gap: float, lower: float, upper: float) -> pd.Series:
    positions = []
    current = lower - gap
    for country, value in values.sort_values().items():
        y = max(float(value), current + gap)
        positions.append((country, y))
        current = y
    if positions and positions[-1][1] > upper:
        shift = positions[-1][1] - upper
        positions = [(country, y - shift) for country, y in positions]
        adjusted = []
        current = lower - gap
        for country, y in positions:
            y = max(y, current + gap)
            adjusted.append((country, y))
            current = y
        positions = adjusted
    return pd.Series(dict(positions))


def save_figure(fig: plt.Figure, stem: str) -> None:
    FIGURES.mkdir(exist_ok=True)
    svg_path = FIGURES / f"{stem}.svg"
    fig.savefig(FIGURES / f"{stem}.png", dpi=300, bbox_inches="tight")
    fig.savefig(svg_path, bbox_inches="tight", metadata=SVG_METADATA)
    clean_svg(svg_path)
    plt.close(fig)

# %%
def plot_dumbbell_change(frame: pd.DataFrame, years: list[int], unit: str) -> None:
    start_year = years[0]
    end_year = years[-1]
    data = complete_history(frame, years)
    y = np.arange(len(data))
    max_value = max(data["start"].max(), data["end"].max())

    fig = plt.figure(figsize=(11.8, 9.8))
    ax = fig.add_axes([0.17, 0.12, 0.78, 0.74])

    for position, row in enumerate(data.itertuples(index=False)):
        ax.hlines(position, row.start, row.end, color=CONNECTOR, linewidth=1.55, alpha=1.0, zorder=1)

    ax.scatter(data["start"], y, s=56, color=START, edgecolor=START_EDGE, linewidth=1.35, zorder=3)
    ax.scatter(data["end"], y, s=66, color=END, edgecolor=PAPER, linewidth=1.25, zorder=4)

    for position, row in enumerate(data.itertuples(index=False)):
        label = f"{value_label(row.end)} ({change_label(row.change)})"
        x = max(row.start, row.end) + max_value * 0.018
        ax.text(x, position, label, va="center", ha="left", fontsize=9.8, color=INK)

    ax.set_yticks(y)
    ax.set_yticklabels(data["country"], fontsize=10.5)
    ax.invert_yaxis()
    ax.set_xlabel(unit, fontsize=11.5, labelpad=10)
    ax.xaxis.set_major_formatter(FuncFormatter(kwh_formatter))
    ax.grid(axis="x", color=GRID, linewidth=0.85)
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color("#d8d2c8")
    ax.spines["bottom"].set_linewidth(1.2)
    ax.tick_params(axis="x", labelsize=10.5, pad=6)
    ax.tick_params(axis="y", length=0, pad=8)
    ax.set_xlim(-max_value * 0.01, max_value * 1.22)

    handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=START, markeredgecolor=START_EDGE, markersize=8, label=str(start_year)),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=END, markeredgecolor=PAPER, markersize=8.5, label=str(end_year)),
    ]
    ax.legend(handles=handles, loc="lower right", frameon=False, fontsize=10.5, borderpad=0.2, labelspacing=0.7)

    fig.text(0.04, 0.965, "Air-cooling electricity per dwelling", ha="left", va="top", fontsize=26, weight="bold", color=INK)
    fig.text(0.04, 0.922, f"{start_year} → {end_year} · {unit}", ha="left", va="top", fontsize=13.5, color=MUTED)
    fig.text(0.04, 0.035, f"Complete {start_year}–{end_year} histories with nonzero {end_year} values · Source: {SOURCE_LABEL}.", ha="left", va="bottom", fontsize=9.3, color=MUTED)

    save_figure(fig, "air_cooling_change_dumbbell")

# %%
def map_bucket(value: float) -> str:
    index = int(np.searchsorted(MAP_BINS, value, side="right") - 1)
    index = max(0, min(index, len(MAP_LABELS) - 1))
    return MAP_LABELS[index]


def read_gisco() -> gpd.GeoDataFrame:
    return gpd.read_file(GISCO_URL)


def map_note(fig: plt.Figure, unit: str, year: int) -> None:
    ax = fig.add_axes([0.10, 0.055, 0.82, 0.105])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(0.0, 0.82, f"{unit}, {year}", ha="left", va="center", fontsize=10.8, weight="semibold", color=INK)
    items = [(LAND, "No data"), *zip(MAP_COLORS, MAP_LABELS)]
    x = 0.0
    for color, label in items:
        ax.add_patch(Rectangle((x, 0.43), 0.035, 0.20, facecolor=color, edgecolor=BORDER, linewidth=0.8))
        ax.text(x + 0.044, 0.53, label, ha="left", va="center", fontsize=9.5, color=INK)
        x += 0.135 if label != "No data" else 0.17
    ax.text(0.0, 0.10, f"Source: {SOURCE_LABEL}; Eurostat GISCO boundaries, EPSG:3035.", ha="left", va="center", fontsize=9.3, color=MUTED)


def plot_map(frame: pd.DataFrame, year: int, unit: str) -> int:
    snapshot = latest_snapshot(frame, year)
    world = read_gisco()
    missing_geometry = sorted(set(snapshot["country_code"]) - set(world["CNTR_ID"]))
    if missing_geometry:
        raise ValueError(f"Missing GISCO geometries: {missing_geometry}")

    context = world.loc[world["CNTR_ID"].isin(MAP_CONTEXT_CODES | set(snapshot["country_code"]))].copy()
    merged = context.merge(snapshot, left_on="CNTR_ID", right_on="country_code", how="left")
    data = merged.loc[merged["value"].notna()].copy()
    data["bucket"] = data["value"].map(map_bucket)
    data["color"] = data["bucket"].map(dict(zip(MAP_LABELS, MAP_COLORS)))

    fig = plt.figure(figsize=(9.8, 9.6))
    ax = fig.add_axes([0.11, 0.18, 0.78, 0.72])

    context.plot(ax=ax, color=LAND, edgecolor=BORDER, linewidth=0.34)
    data.plot(ax=ax, color=data["color"], edgecolor=BORDER, linewidth=0.72)

    ax.set_xlim(MAP_EXTENT[0], MAP_EXTENT[1])
    ax.set_ylim(MAP_EXTENT[2], MAP_EXTENT[3])
    ax.set_aspect("equal")
    ax.axis("off")

    map_note(fig, unit, year)
    fig.text(0.04, 0.965, "Air-cooling electricity per dwelling", ha="left", va="top", fontsize=26, weight="bold", color=INK)
    fig.text(0.04, 0.922, f"{year} snapshot · {unit}", ha="left", va="top", fontsize=13.5, color=MUTED)

    save_figure(fig, "air_cooling_2024_map")
    return len(missing_geometry)

# %%
def plot_degree_day_trend(
    degree_frame: pd.DataFrame,
    degree_years: list[int],
    electricity_frame: pd.DataFrame,
    electricity_year: int,
) -> int:
    regional, count = regional_degree_days(degree_frame, degree_years, electricity_frame, electricity_year)
    years = np.array(degree_years)
    y_max = np.ceil(regional.to_numpy().max() * 1.16 / 50) * 50
    latest = regional[degree_years[-1]]
    label_y = label_positions(latest, gap=y_max * 0.045, lower=0, upper=y_max * 0.95)

    fig = plt.figure(figsize=(11.8, 7.2))
    ax = fig.add_axes([0.09, 0.18, 0.75, 0.64])

    for region in regional.index:
        values = regional.loc[region].to_numpy()
        color = REGION_COLORS[region]
        ax.plot(years, values, color=color, linewidth=3.0, alpha=1.0, zorder=3)
        ax.scatter(years[-1], values[-1], s=42, color=color, edgecolor=PAPER, linewidth=1.1, zorder=4)

    for region in regional.index:
        value = latest[region]
        y = label_y[region]
        color = REGION_COLORS[region]
        ax.plot([years[-1] + 0.10, years[-1] + 0.42], [value, y], color=LABEL_LINE, linewidth=0.85, zorder=1)
        ax.text(years[-1] + 0.50, y, region, ha="left", va="center", fontsize=10.8, color=color, weight="bold")

    ax.set_xlim(years[0] - 0.6, years[-1] + 1.9)
    ax.set_ylim(0, y_max)
    ax.set_ylabel("Annual cooling degree-days", fontsize=11.5, labelpad=10)
    ax.set_xticks([years[0], *years[3::3], years[-1]])
    ax.set_yticks(np.arange(0, y_max + 1, 100))
    ax.grid(axis="y", color=GRID, linewidth=0.85)
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color("#d8d2c8")
    ax.spines["bottom"].set_linewidth(1.2)
    ax.tick_params(axis="x", labelsize=10.5, pad=6)
    ax.tick_params(axis="y", labelsize=10.5, length=0, pad=6)

    fig.text(0.04, 0.955, "Cooling-weather pressure is rising", ha="left", va="top", fontsize=26, weight="bold", color=INK)
    fig.text(
        0.04,
        0.902,
        f"Regional medians · annual cooling degree-days · {degree_years[0]}–{degree_years[-1]}",
        ha="left",
        va="top",
        fontsize=13.5,
        color=MUTED,
    )
    fig.text(
        0.04,
        0.045,
        f"Cooling degree-days combine how many hot days there are and how far temperatures sit above the cooling threshold; {count} matched countries · Source: {SOURCE_LABEL}.",
        ha="left",
        va="bottom",
        fontsize=9.3,
        color=MUTED,
    )

    save_figure(fig, "cooling_degree_days_trend")
    return count


# %%
def main() -> None:
    frame, years, unit = read_workbook(WORKBOOK)
    degree_frame, degree_years, _ = read_workbook(DEGREE_DAYS_WORKBOOK)
    graph_count = int((frame[years].notna().all(axis=1) & frame[years[-1]].gt(0)).sum())
    map_count = int(frame[years[-1]].notna().sum())

    plot_dumbbell_change(frame, years, unit)
    map_unmatched = plot_map(frame, years[-1], unit)
    degree_day_count = plot_degree_day_trend(degree_frame, degree_years, frame, years[-1])

    print(f"years={years[0]}-{years[-1]}")
    print(f"graph_countries={graph_count}")
    print(f"map_countries={map_count}")
    print(f"map_unmatched={map_unmatched}")
    print(f"degree_day_countries={degree_day_count}")
    print(f"figures={FIGURES}")


if __name__ == "__main__":
    main()
