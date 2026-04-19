"""A reference heatmap that the user has already tuned visually.

Intended to be embedded as half-column width in a 3.5" column of an A4
two-column paper, body_pt = 10. s_ref = 1.75 / 3.5 = 0.5.
Page pt: title=10, label=9, tick=8.
Code pt (= page_pt / s_ref): title=20, label=18, tick=16.
"""

import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({
    "font.size": 20.0,
    "axes.titlesize": 20.0,
    "axes.labelsize": 18.0,
    "xtick.labelsize": 16.0,
    "ytick.labelsize": 16.0,
    "legend.fontsize": 16.0,
    "axes.linewidth": 1.6,
    "xtick.major.width": 1.6,
    "ytick.major.width": 1.6,
    "xtick.major.size": 7.0,
    "ytick.major.size": 7.0,
})

rng = np.random.default_rng(seed=1)
data = rng.normal(0, 1, size=(10, 10))
data = (data + data.T) / 2  # symmetric for visual interest

fig, ax = plt.subplots(figsize=(3.5, 3.5))
im = ax.imshow(data, cmap="viridis", aspect="equal")

ax.set_title("Correlation matrix")
ax.set_xlabel("feature i")
ax.set_ylabel("feature j")

cbar = fig.colorbar(im, ax=ax, shrink=0.85)
cbar.ax.tick_params()

fig.tight_layout()
fig.savefig("reference_heatmap.pdf")
