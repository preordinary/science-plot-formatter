"""Reference answer for paper-font-format applied to before_paper_format.py.

Inputs assumed: figsize=(5, 3), body_pt=10, column_width_in=3.5, embed_ratio=1.0.
W_page = 3.5" (small band) => title=10, label=9, tick=8 on page.
s = 3.5 / 5 = 0.70; code pt = page pt / s rounded to 0.5.
"""

import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({
    "font.size": 14.5,
    "axes.titlesize": 14.5,
    "figure.titlesize": 14.5,
    "axes.labelsize": 13.0,
    "xtick.labelsize": 11.5,
    "ytick.labelsize": 11.5,
    "legend.fontsize": 11.5,
    "legend.title_fontsize": 13.0,
    "axes.linewidth": 1.14,
    "xtick.major.width": 1.14,
    "ytick.major.width": 1.14,
    "xtick.minor.width": 0.86,
    "ytick.minor.width": 0.86,
    "xtick.major.size": 5.00,
    "ytick.major.size": 5.00,
    "xtick.minor.size": 2.86,
    "ytick.minor.size": 2.86,
    "lines.linewidth": 1.79,
    "lines.markersize": 7.14,
    "patch.linewidth": 1.14,
})

rng = np.random.default_rng(seed=0)
x = np.linspace(0, 10, 50)
y1 = np.sin(x) + rng.normal(0, 0.1, size=x.shape)
y2 = np.cos(x) + rng.normal(0, 0.1, size=x.shape)
err1 = rng.uniform(0.05, 0.15, size=x.shape)
err2 = rng.uniform(0.05, 0.15, size=x.shape)

fig, ax = plt.subplots(figsize=(5, 3))

ax.errorbar(x, y1, yerr=err1, label="model A", marker="o", linestyle="-")
ax.errorbar(x, y2, yerr=err2, label="model B", marker="s", linestyle="--")

ax.set_title("Accuracy vs. time")
ax.set_xlabel("time (s)")
ax.set_ylabel("accuracy")
ax.legend()

fig.tight_layout()
fig.savefig("after_paper_format.pdf")
