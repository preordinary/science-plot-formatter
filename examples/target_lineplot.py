"""A target line plot that the user wants placed next to reference_heatmap.py.

Currently messy: oversized title, inconsistent fontsizes, a figsize picked
arbitrarily. The match-reference-style skill is expected to rewrite figsize
and all font sizes so this figure looks coordinated with the reference
when the two are placed side-by-side in one column.
"""

import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng(seed=2)
x = np.linspace(0, 100, 200)
y = np.cumsum(rng.normal(0, 1, size=x.shape))

fig, ax = plt.subplots(figsize=(6, 4))

ax.plot(x, y, linewidth=2.0, color="tab:blue")
ax.fill_between(x, y - 2, y + 2, alpha=0.2, color="tab:blue", label="± 2 SD")

ax.set_title("Cumulative drift", fontsize=24)
ax.set_xlabel("step", fontsize=12)
ax.set_ylabel("value", fontsize=12)
ax.tick_params(axis="both", labelsize=10)
ax.legend(fontsize=14)

fig.tight_layout()
fig.savefig("target_lineplot.pdf")
