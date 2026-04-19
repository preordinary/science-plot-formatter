"""Example: an unformatted plotting script for testing paper-font-format.

Realistic "it works on my screen" script — font sizes are out of proportion
(tick > label, title too small), figsize will be kept as-is by the skill.
"""

import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng(seed=0)
x = np.linspace(0, 10, 50)
y1 = np.sin(x) + rng.normal(0, 0.1, size=x.shape)
y2 = np.cos(x) + rng.normal(0, 0.1, size=x.shape)
err1 = rng.uniform(0.05, 0.15, size=x.shape)
err2 = rng.uniform(0.05, 0.15, size=x.shape)

fig, ax = plt.subplots(figsize=(5, 3))

ax.errorbar(x, y1, yerr=err1, label="model A", marker="o", linestyle="-")
ax.errorbar(x, y2, yerr=err2, label="model B", marker="s", linestyle="--")

ax.set_title("Accuracy vs. time", fontsize=11)
ax.set_xlabel("time (s)", fontsize=10)
ax.set_ylabel("accuracy", fontsize=10)
ax.tick_params(axis="both", labelsize=14)
ax.legend(fontsize=9)

fig.tight_layout()
fig.savefig("before_paper_format.pdf")
