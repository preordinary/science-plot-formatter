# science-plot-formatter

A Claude Code plugin (skills only) that formats matplotlib plotting scripts for inclusion in scientific papers. It reasons about the figure's **final physical size on the page** and sets font sizes, line widths, and (for the second skill) figsize accordingly — rather than naively scaling the user's current values.

## Two skills

### `paper-font-format`
Given a plotting script plus `(body_pt, column_width, embed_ratio)`, recomputes all fonts and line widths from scratch so the figure reads correctly when embedded at the specified width. **Keeps `figsize` unchanged.** Title is anchored to the paper's body font; secondary and tertiary fonts adapt to the figure's final on-page width (the smaller the figure, the tighter the hierarchy).

### `match-reference-style`
Given a reference script the user has already tuned and a target script to harmonize with it, aligns on-page fonts between the two and redesigns the target's `figsize` to fit the intended composed layout (e.g., side-by-side in one column). Respects each chart type's natural aspect ratio (heatmap ≈ 1:1, line plot ≈ 3:2) within ±20 % of the reference's height.

## Installation

Three ways to use the skills, from zero-install to packaged:

### 1. Direct reference (zero install, simplest)

Tell Claude which SKILL.md to follow:

> "Using `skills/paper-font-format/SKILL.md`, format `my_plot.py` assuming Nature single-column (body_pt=7, column_width=3.5, embed_ratio=1.0)."

Works from anywhere — Claude reads the skill file from disk.

### 2. Project-scope skills (recommended for development)

When run inside this repo, Claude Code auto-loads skills from `.claude/skills/` — which is a symlink to `skills/`. Just run `claude` in the project root and the two skills are immediately callable. Edits to `skills/*/SKILL.md` are picked up on the next turn — no reinstall needed.

This is project-scope only: it doesn't affect other projects, and any same-named user-level skills in `~/.claude/skills/` take precedence (they override, they don't conflict).

### 3. Install as a plugin

Once the skills stabilize, this project can be installed as a Claude Code plugin from its git repo. The `.claude-plugin/plugin.json` manifest is already in place.

```bash
# Once published to a marketplace:
claude plugin install science-plot-formatter@<marketplace>
```

## Usage examples

### paper-font-format
```
Use paper-font-format to format examples/before_paper_format.py.
Assume A4 two-column paper: column_width=3.5, embed_ratio=1.0, body_pt=10.
```

### match-reference-style
```
Use match-reference-style to align examples/target_lineplot.py with
examples/reference_heatmap.py. They will sit side-by-side in one column:
column_width=3.5, body_pt=10, ref_embed_ratio=0.5.
```

## Repository layout

```
science-plot-formatter/
├── .claude-plugin/plugin.json        # plugin manifest
├── .claude/skills -> ../skills       # symlink for project-scope auto-load
├── skills/
│   ├── paper-font-format/SKILL.md
│   └── match-reference-style/SKILL.md
├── examples/                         # before/after test fixtures
├── docs/font-scaling-math.md         # human-readable math reference
└── README.md
```

## The math, briefly

A figure drawn at `figsize = (w, h)` inches and embedded at on-page width `W_page` is scaled by `s = W_page / w`. A text declared at `X` pt in matplotlib renders as `X * s` pt on the page. So to hit target page pt `T`, the code must set `X = T / s`. Everything else in both skills follows from this plus a readability floor (≥ 6 pt on page) and chart-type aware aspect ratios. Full derivation: `docs/font-scaling-math.md`.

## Design principles

- **Never scale the user's existing font sizes.** They're usually out of proportion to begin with. Derive absolute targets from paper conventions and figure's page size, then completely overwrite.
- **Skill 1 treats `figsize` as sacred**; skill 2 redesigns it because the target is being composed with another figure.
- **Readability floor at 6 pt** on the printed page for every text element — enforced after all computation.

## Non-goals (v0.1)

- No commands, agents, hooks, or MCP servers.
- No changes to data, colormaps, linestyles, or any other semantic choices in user scripts.
- No marketplace publication workflow yet.
