# %%
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.ticker import FuncFormatter

from figure_style import (
    AXIS_LABEL_SIZE,
    BLUE_PALE,
    BORDER,
    CHART_SIZE,
    CONNECTOR,
    CONNECTOR_WIDTH,
    END,
    GREY_045,
    GREY_060,
    GREY_080,
    GREY_100,
    INK,
    LABEL_SIZE,
    LAND,
    MAP_SIZE,
    MUTED,
    NOTE_SIZE,
    PAPER,
    SEQUENTIAL_GREYS,
    START,
    START_EDGE,
    TENURE_OWNER,
    TENURE_RENTER,
    add_header,
    add_note,
    apply_theme,
    save_figure,
    style_axis,
)

# %%
ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = ROOT / "Enerdata_Odyssee_260702_122358.xlsx"
BARRIER1_CSV = ROOT / "barrier1_tenant_landlord.csv"
BARRIER3_CSV = ROOT / "barrier3_building_age.csv"
FIGURES = ROOT / "figures"
GISCO_URL = "https://gisco-services.ec.europa.eu/distribution/v2/countries/geojson/CNTR_RG_10M_2024_3035.geojson"
SOURCE_LABEL = "ODYSSEE/Enerdata export, 2026-07-02"
MAP_EXTENT = (2_420_000, 6_780_000, 1_420_000, 5_360_000)
DUMBBELL_AX = [0.17, 0.17, 0.77, 0.66]
BARRIER_BAR_AX = [0.18, 0.16, 0.72, 0.66]
BARRIER_SPLIT_AX = [0.19, 0.17, 0.72, 0.64]
MAP_AX = [0.10, 0.19, 0.80, 0.68]
MAP_NOTE_AX = [0.10, 0.065, 0.82, 0.095]

BARRIER_CONTEXT_COUNTRIES = {"Switzerland", "Denmark", "Sweden"}
AGE_BUCKETS = [
    ("before_1919", "Before 1919", GREY_100),
    ("y1919_1945", "1919–1945", GREY_080),
    ("y1946_1960", "1946–1960", GREY_060),
    ("y1961_1980", "1961–1980", GREY_045),
]
AGE_NEW_COLOR = BLUE_PALE

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
MAP_COLORS = SEQUENTIAL_GREYS
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


def read_csv_data(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, comment="#")


def read_csv_source(path: Path) -> str:
    line = path.read_text().splitlines()[0].removeprefix("# Source: ").strip()
    if "ilc_lvho02" in line:
        return "Eurostat ilc_lvho02"
    if "cens_21dwop_r3" in line:
        return "Eurostat cens_21dwop_r3, 2021 Population & Housing Census"
    return line.split(". Filters:")[0]


def complete_history(frame: pd.DataFrame, years: list[int]) -> pd.DataFrame:
    start_year = years[0]
    end_year = years[-1]
    data = frame.loc[frame[years].notna().all(axis=1)].copy()
    data["start"] = data[start_year]
    data["end"] = data[end_year]
    data["change"] = data["end"] - data["start"]
    return data.loc[data["end"].gt(0)].sort_values("end", ascending=False)


def barrier_country_set(frame: pd.DataFrame, years: list[int]) -> set[str]:
    return set(complete_history(frame, years)["country"]) | BARRIER_CONTEXT_COUNTRIES


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


def percent_axis(value: float, position: int) -> str:
    return f"{abs(value):.0f}%"


def percent_label(value: float) -> str:
    return f"{value:.1f}%"

# %%
def plot_dumbbell_change(frame: pd.DataFrame, years: list[int], unit: str) -> None:
    start_year = years[0]
    end_year = years[-1]
    data = complete_history(frame, years)
    y = np.arange(len(data))
    max_value = max(data["start"].max(), data["end"].max())

    fig = plt.figure(figsize=CHART_SIZE)
    ax = fig.add_axes(DUMBBELL_AX)

    for position, row in enumerate(data.itertuples(index=False)):
        ax.hlines(position, row.start, row.end, color=CONNECTOR, linewidth=CONNECTOR_WIDTH, alpha=1.0, zorder=1)

    ax.scatter(data["start"], y, s=56, color=START, edgecolor=START_EDGE, linewidth=1.35, zorder=3)
    ax.scatter(data["end"], y, s=66, color=END, edgecolor=PAPER, linewidth=1.25, zorder=4)

    for position, row in enumerate(data.itertuples(index=False)):
        label = f"{value_label(row.end)} ({change_label(row.change)})"
        x = max(row.start, row.end) + max_value * 0.018
        ax.text(x, position, label, va="center", ha="left", fontsize=9.6, color=INK)

    ax.set_yticks(y)
    ax.set_yticklabels(data["country"], fontsize=LABEL_SIZE)
    ax.invert_yaxis()
    ax.set_xlabel(unit, fontsize=AXIS_LABEL_SIZE, labelpad=10)
    ax.xaxis.set_major_formatter(FuncFormatter(kwh_formatter))
    style_axis(ax, "x")
    ax.tick_params(axis="y", pad=8)
    ax.set_xlim(-max_value * 0.01, max_value * 1.22)

    handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=START, markeredgecolor=START_EDGE, markersize=8, label=str(start_year)),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=END, markeredgecolor=PAPER, markersize=8.5, label=str(end_year)),
    ]
    ax.legend(handles=handles, loc="lower right", frameon=False, fontsize=10.5, borderpad=0.2, labelspacing=0.7)

    add_header(fig, "Air-conditioning electricity use by country", f"Electricity per dwelling for air cooling · {start_year} and {end_year} · {unit} · complete country histories")
    add_note(fig, f"Includes countries with complete {start_year}–{end_year} histories and nonzero {end_year} values · Source: {SOURCE_LABEL}.")

    save_figure(fig, FIGURES, "air_cooling_change_dumbbell")

# %%
def map_bucket(value: float) -> str:
    index = int(np.searchsorted(MAP_BINS, value, side="right") - 1)
    index = max(0, min(index, len(MAP_LABELS) - 1))
    return MAP_LABELS[index]


def read_gisco() -> gpd.GeoDataFrame:
    return gpd.read_file(GISCO_URL)


def map_note(fig: plt.Figure, unit: str, year: int) -> None:
    ax = fig.add_axes(MAP_NOTE_AX)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(0.0, 0.82, f"{unit}, {year}", ha="left", va="center", fontsize=10.5, weight="semibold", color=INK)
    items = [(LAND, "No data"), *zip(MAP_COLORS, MAP_LABELS)]
    x = 0.0
    for color, label in items:
        ax.add_patch(Rectangle((x, 0.43), 0.035, 0.20, facecolor=color, edgecolor=BORDER, linewidth=0.8))
        ax.text(x + 0.044, 0.53, label, ha="left", va="center", fontsize=9.3, color=INK)
        x += 0.135 if label != "No data" else 0.17
    ax.text(0.0, 0.10, f"Source: {SOURCE_LABEL}; Eurostat GISCO boundaries, EPSG:3035.", ha="left", va="center", fontsize=NOTE_SIZE, color=MUTED)


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

    fig = plt.figure(figsize=MAP_SIZE)
    ax = fig.add_axes(MAP_AX)

    context.plot(ax=ax, color=LAND, edgecolor=BORDER, linewidth=0.34)
    data.plot(ax=ax, color=data["color"], edgecolor=BORDER, linewidth=0.72)

    ax.set_xlim(MAP_EXTENT[0], MAP_EXTENT[1])
    ax.set_ylim(MAP_EXTENT[2], MAP_EXTENT[3])
    ax.set_aspect("equal")
    ax.axis("off")

    map_note(fig, unit, year)
    add_header(fig, "Air-conditioning electricity use across Europe", f"Electricity per dwelling for air cooling · {year} · {unit}")

    save_figure(fig, FIGURES, "air_cooling_2024_map")
    return len(missing_geometry)

# %%
def plot_barrier_owner_tenure(frame: pd.DataFrame, countries: set[str], source: str) -> int:
    data = frame.loc[frame["country"].isin(countries)].copy()
    missing = sorted(countries - set(data["country"]))
    if missing:
        raise ValueError(f"Missing barrier 1 countries: {missing}")
    data["owner"] = 100 - data["pct_tenant_total"]
    data["renter"] = data["pct_tenant_total"]
    share_columns = ["renter", "owner"]
    if data[share_columns].lt(-1e-9).any().any():
        raise ValueError("Barrier 1 tenure shares include negative values")
    if not np.allclose(data[share_columns].sum(axis=1), 100):
        raise ValueError("Barrier 1 tenure shares do not sum to 100")
    data = data.sort_values("owner", ascending=False)

    fig = plt.figure(figsize=CHART_SIZE)
    ax = fig.add_axes(BARRIER_BAR_AX)
    y = np.arange(len(data))

    ax.barh(y, data["owner"], color=TENURE_OWNER, height=0.66, edgecolor=PAPER, linewidth=0.8)
    ax.barh(y, data["renter"], left=data["owner"], color=TENURE_RENTER, height=0.66, edgecolor=PAPER, linewidth=0.8)

    for position, value in enumerate(data["owner"]):
        ax.text(value / 2, position, percent_label(value), ha="center", va="center", fontsize=9.4, color=PAPER, weight="semibold")

    ax.set_yticks(y)
    ax.set_yticklabels(data["country"], fontsize=LABEL_SIZE)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel("Share of population (%)", fontsize=AXIS_LABEL_SIZE, labelpad=10)
    ax.xaxis.set_major_formatter(FuncFormatter(percent_axis))
    style_axis(ax, "x")
    ax.tick_params(axis="y", pad=8)

    handles = [
        Line2D([0], [0], color=TENURE_OWNER, linewidth=8, label="Owner"),
        Line2D([0], [0], color=TENURE_RENTER, linewidth=8, label="Renter"),
    ]
    fig.legend(handles=handles, loc="upper right", bbox_to_anchor=(0.91, 0.872), frameon=False, ncol=2, fontsize=9.8, handlelength=1.6, columnspacing=1.0)

    add_header(fig, "Owner and renter tenure by country", "Population share · latest Eurostat year · selected countries")
    add_note(fig, f"Owner share is computed as 100 minus renter share; sorted by owner share · Source: {source}.")

    save_figure(fig, FIGURES, "barrier1_owner_tenure")
    return len(data)


def plot_barrier_building_age(frame: pd.DataFrame, countries: set[str], source: str) -> int:
    data = frame.loc[frame["country"].isin(countries)].copy()
    missing = sorted(countries - set(data["country"]))
    if missing:
        raise ValueError(f"Missing barrier 3 countries: {missing}")
    data["known"] = data["total_dwellings"] - data["unknown_year"]
    data["post1980_sum"] = data["known"] - data["pre1980_sum"]
    for column, _, _ in AGE_BUCKETS:
        data[f"{column}_pct"] = data[column] / data["known"] * 100
    data["pre1980_pct"] = data["pre1980_sum"] / data["known"] * 100
    data["post1980_pct"] = data["post1980_sum"] / data["known"] * 100
    data = data.sort_values("post1980_pct", ascending=False)

    fig = plt.figure(figsize=CHART_SIZE)
    ax = fig.add_axes(BARRIER_SPLIT_AX)
    y = np.arange(len(data))
    old_total = data["pre1980_pct"]
    max_side = np.ceil(max(old_total.max(), data["post1980_pct"].max()) / 10) * 10 + 10

    left = -old_total.to_numpy()
    for column, label, color in AGE_BUCKETS:
        values = data[f"{column}_pct"].to_numpy()
        ax.barh(y, values, left=left, height=0.66, color=color, edgecolor=PAPER, linewidth=0.7, label=label)
        left = left + values
    ax.barh(y, data["post1980_pct"], left=0, height=0.66, color=AGE_NEW_COLOR, edgecolor=PAPER, linewidth=0.7, label="1981+")

    for position, row in enumerate(data.itertuples(index=False)):
        ax.text(-row.pre1980_pct - max_side * 0.025, position, f"{row.pre1980_pct:.0f}%", ha="right", va="center", fontsize=9.4, color=INK, weight="semibold")
        ax.text(row.post1980_pct + max_side * 0.025, position, f"{row.post1980_pct:.0f}%", ha="left", va="center", fontsize=9.4, color=INK, weight="semibold")

    ax.axvline(0, color=INK, linewidth=1.2)
    ax.set_yticks(y)
    ax.set_yticklabels(data["country"], fontsize=LABEL_SIZE)
    ax.invert_yaxis()
    ax.set_xlim(-max_side, max_side)
    ax.set_xticks([])
    ax.grid(False)
    ax.set_axisbelow(True)
    ax.spines[:].set_visible(False)
    ax.tick_params(axis="x", length=0, labelbottom=False)
    ax.tick_params(axis="y", length=0, pad=8)

    fig.legend(loc="upper right", bbox_to_anchor=(0.91, 0.872), frameon=False, ncol=5, fontsize=9.2, handlelength=1.5, columnspacing=0.9)

    add_header(fig, "Dwelling stock age by country", "Conventional dwellings by construction period · 2021 Census · selected countries")
    add_note(fig, f"Left: pre-1980; right: 1981+; sorted by 1981+ share; rows sum to 100% · Source: {source}.")

    save_figure(fig, FIGURES, "barrier3_building_age_split")
    return len(data)


# %%
def main() -> None:
    frame, years, unit = read_workbook(WORKBOOK)
    barrier1_frame = read_csv_data(BARRIER1_CSV)
    barrier3_frame = read_csv_data(BARRIER3_CSV)
    barrier_countries = barrier_country_set(frame, years)
    graph_count = int((frame[years].notna().all(axis=1) & frame[years[-1]].gt(0)).sum())
    map_count = int(frame[years[-1]].notna().sum())

    plot_dumbbell_change(frame, years, unit)
    map_unmatched = plot_map(frame, years[-1], unit)
    barrier1_count = plot_barrier_owner_tenure(barrier1_frame, barrier_countries, read_csv_source(BARRIER1_CSV))
    barrier3_count = plot_barrier_building_age(barrier3_frame, barrier_countries, read_csv_source(BARRIER3_CSV))

    print(f"years={years[0]}-{years[-1]}")
    print(f"graph_countries={graph_count}")
    print(f"map_countries={map_count}")
    print(f"map_unmatched={map_unmatched}")
    print(f"barrier_country_set={len(barrier_countries)}")
    print(f"barrier1_countries={barrier1_count}")
    print(f"barrier3_countries={barrier3_count}")
    print(f"figures={FIGURES}")


if __name__ == "__main__":
    main()
