from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt

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
BASELINE = "#d8d2c8"
TENURE_OWNER = "#111111"
TENURE_RENTER = "#d8d8d8"

GREY_100 = "#111111"
GREY_080 = "#4d4d4d"
GREY_060 = "#858585"
GREY_045 = "#b5b5b5"
GREY_030 = "#d4d4d4"
GREY_020 = "#e8e8e8"
BLUE_PALE = "#d8e4ec"
SEQUENTIAL_GREYS = [GREY_020, GREY_030, GREY_045, GREY_060, GREY_080, GREY_100]

CHART_SIZE = (11.8, 8.6)
MAP_SIZE = (9.8, 9.8)
TITLE_X = 0.055
TITLE_Y = 0.94
SUBTITLE_Y = 0.895
NOTE_Y = 0.055
TITLE_SIZE = 24
SUBTITLE_SIZE = 13
NOTE_SIZE = 9.3
TICK_SIZE = 10.4
LABEL_SIZE = 10.3
AXIS_LABEL_SIZE = 11.2
GRID_WIDTH = 0.85
BASELINE_WIDTH = 1.15
CONNECTOR_WIDTH = 1.45

SVG_METADATA = {"Date": "2026-07-02"}
FONT_STACK = ["Inter", "Helvetica Neue", "Arial", "DejaVu Sans"]


def apply_theme() -> None:
    mpl.rcParams.update(
        {
            "figure.facecolor": PAPER,
            "axes.facecolor": PAPER,
            "savefig.facecolor": PAPER,
            "font.family": "sans-serif",
            "font.sans-serif": FONT_STACK,
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


def clean_svg(path: Path) -> None:
    path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")


def add_header(fig: plt.Figure, title: str, subtitle: str) -> None:
    fig.text(TITLE_X, TITLE_Y, title, ha="left", va="top", fontsize=TITLE_SIZE, weight="bold", color=INK)
    fig.text(TITLE_X, SUBTITLE_Y, subtitle, ha="left", va="top", fontsize=SUBTITLE_SIZE, color=MUTED)


def add_note(fig: plt.Figure, text: str) -> None:
    fig.text(TITLE_X, NOTE_Y, text, ha="left", va="bottom", fontsize=NOTE_SIZE, color=MUTED)


def style_axis(ax: plt.Axes, grid_axis: str) -> None:
    ax.grid(axis=grid_axis, color=GRID, linewidth=GRID_WIDTH)
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color(BASELINE)
    ax.spines["bottom"].set_linewidth(BASELINE_WIDTH)
    ax.tick_params(axis="x", labelsize=TICK_SIZE, pad=6)
    ax.tick_params(axis="y", labelsize=TICK_SIZE, length=0, pad=6)


def save_figure(fig: plt.Figure, figures: Path, stem: str) -> None:
    figures.mkdir(exist_ok=True)
    svg_path = figures / f"{stem}.svg"
    fig.savefig(figures / f"{stem}.png", dpi=300)
    fig.savefig(svg_path, metadata=SVG_METADATA)
    clean_svg(svg_path)
    plt.close(fig)
