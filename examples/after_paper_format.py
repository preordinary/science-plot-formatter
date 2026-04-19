"""Reference answer for paper-font-format applied to before_paper_format.py.

Inputs: figsize=(5, 3), body_pt=10, column_width_in=3.5, embed_ratio=1.0.
W_page = 3.5"  ->  "small" band (2.5"-3.5")
s      = 3.5 / 5 = 0.70

Typography page pt: title=10, label=9, tick/legend=8 (all >= 6 floor).
Strokes / lengths / lines / errorbars: per docs/font-scaling-math.md tables.
Every rcParam value below is (target_page_pt / 0.70) rounded to 0.5 (fonts)
or 0.1 (strokes).
"""

import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({
    # --- Typography ---
    "font.size":             14.5,   # 10 / 0.7
    "axes.titlesize":        14.5,
    "figure.titlesize":      14.5,
    "axes.labelsize":        13.0,   # 9 / 0.7
    "xtick.labelsize":       11.5,   # 8 / 0.7
    "ytick.labelsize":       11.5,
    "legend.fontsize":       11.5,
    "legend.title_fontsize": 13.0,
    # --- Strokes (page pt targets: 0.8 / 0.5) ---
    "axes.linewidth":        1.1,    # 0.8 / 0.7
    "xtick.major.width":     1.1,
    "ytick.major.width":     1.1,
    "xtick.minor.width":     0.7,    # 0.5 / 0.7
    "ytick.minor.width":     0.7,
    "grid.linewidth":        0.7,
    "patch.linewidth":       1.1,
    "hatch.linewidth":       1.1,
    # --- Lengths ---
    "xtick.major.size":      5.0,    # 3.5 / 0.7
    "ytick.major.size":      5.0,
    "xtick.minor.size":      2.9,    # 2.0 / 0.7
    "ytick.minor.size":      2.9,
    "xtick.major.pad":       4.3,    # 3.0 / 0.7
    "ytick.major.pad":       4.3,
    "axes.labelpad":         5.0,    # 3.5 / 0.7
    # --- Lines / markers (middle band: 1.25 / 4.0 / 0.6) ---
    "lines.linewidth":       1.8,    # 1.25 / 0.7
    "lines.markersize":      5.7,    # 4.0 / 0.7
    "lines.markeredgewidth": 0.9,    # 0.6 / 0.7
})

# Errorbar capsize and capthick are set per-call (capthick is not in rcParams).
CAPSIZE  = 3.6   # page 2.5 / 0.7
CAPTHICK = 1.1   # == axes.linewidth code value

rng = np.random.default_rng(seed=0)
x = np.linspace(0, 10, 50)
y1 = np.sin(x) + rng.normal(0, 0.1, size=x.shape)
y2 = np.cos(x) + rng.normal(0, 0.1, size=x.shape)
err1 = rng.uniform(0.05, 0.15, size=x.shape)
err2 = rng.uniform(0.05, 0.15, size=x.shape)

fig, ax = plt.subplots(figsize=(5, 3))

ax.errorbar(x, y1, yerr=err1, label="model A",
            marker="o", linestyle="-", capsize=CAPSIZE, capthick=CAPTHICK)
ax.errorbar(x, y2, yerr=err2, label="model B",
            marker="s", linestyle="--", capsize=CAPSIZE, capthick=CAPTHICK)

ax.set_title("Accuracy vs. time")
ax.set_xlabel("time (s)")
ax.set_ylabel("accuracy")
ax.legend()

fig.tight_layout()
fig.savefig("after_paper_format.pdf")
