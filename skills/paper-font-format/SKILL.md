---
name: paper-font-format
description: Use when a user wants to format a matplotlib plotting script for inclusion in a scientific paper. Derives the full visual system (fonts, line widths, tick widths, marker sizes, bar/patch edges, grid, error-bar caps) from the figure's final physical size on the page, so the figure reads as a visually unified whole at its printed scale. Recomputes every value from scratch — does not scale the user's existing settings.
---

# paper-font-format

You are formatting a matplotlib plotting script so that when its saved figure is embedded into a scientific paper at a specified width, **every visual element — text, strokes, markers, bar edges, error-bar caps, grid — reads at the correct physical size on the printed page, and all of these harmonize so the figure looks like one coherent design.**

## Critical principles

1. **Visual unity is the job, not just font sizing.** Changing text without also adjusting line widths, tick widths, marker sizes, patch edges, and error-bar caps leaves the figure visually unbalanced: big text with hairline axes, or small text with chunky markers. Every time you change a font size, you also change the companion stroke / marker / geometry values.

2. **Never scale the user's existing values.** Users tend to set font sizes, linewidths, and marker sizes by screen trial-and-error; those values are often out of proportion. Multiplying them by a scale factor preserves and amplifies the misproportion. Instead, derive every value from scratch from (a) the paper's body font size and (b) the figure's final physical width on the page, then completely overwrite.

3. **`figsize` is sacred.** The user chose it for a reason (data aspect, subplot grid). Do not change it.

4. **Data, colors, colormaps, linestyles, marker glyph choices are semantic** — they express meaning about the data. Never touch them. Only change visual weights, not visual choices.

## The scaling principle

A figure saved at `figsize = (w, h)` inches and embedded on the page at width `W_page` inches is scaled by:

```
s = W_page / w
```

Any matplotlib value expressed in **points** (font size, `linewidth`, `markersize`, tick `size`, `capsize`, etc.) declared at `X` pt renders on the printed page at `X * s` pt. So to hit a target **page pt** `T`, the code must set `X = T / s`.

Bar geometry (`ax.bar(..., width=...)`) is in **data coordinates** and does not follow this rule — it stays the same relative to the x-axis regardless of embedding scale. It is handled separately (see section 6).

## Step-by-step procedure

### 1. Gather inputs

**Step A — ask for the venue first.** Ask: *"What conference or journal are you submitting this figure to?"* If the user gives a venue (NeurIPS, Nature, IEEE TVCG, CVPR, etc.), use `WebSearch` / `WebFetch` on the venue's official author guidelines / LaTeX class file / `.cls` to extract:

- paper size (US Letter vs A4)
- column layout (single / two-column)
- column width (from `\textwidth` / `\columnwidth` or the guidelines' figure-width instruction)
- body font size (pt)

Prefer primary sources (venue's own author kit, LaTeX class file, "for authors" page) over third-party summaries. Show the user what you found with a source URL and ask for confirmation before proceeding.

**Step B — if venue lookup fails or user can't name one**, fall back to asking directly for `column_width_in` (default 6.5") and `body_pt` (default 12).

**Step C — always-required inputs regardless of venue:**

- **`figsize` `(w, h)`** — read from the target code (`plt.figure(figsize=...)`, `plt.subplots(figsize=...)`). If absent, matplotlib default is `(6.4, 4.8)`; ask the user to confirm.
- **`embed_ratio`** — fraction of `column_width_in` this figure occupies (default 1.0; `0.5` = half-column; `2.0` = spans two columns).

### 2. Compute scale factor and figure page width

```
W_page = column_width_in * embed_ratio
s      = W_page / figsize[0]
```

### 3. Derive target page values for every visual category

For every quantity, define the target **on the printed page** (page pt), then the code value is `target_page_pt / s` rounded to 0.5 pt (or 0.1 for small stroke values).

#### 3a. Typography — depends on `W_page`

Title is anchored to `body_pt` and is size-independent. Secondary and tertiary sizes compress on smaller figures to preserve readability hierarchy.

| `W_page` band | Label (axis labels) | Tick / Legend / Annotation |
|---|---|---|
| ≤ 2.5" (sub-panel) | `body_pt − 1` | `body_pt − 2` |
| 2.5"–3.5" (small) | `body_pt − 1` | `body_pt − 2` |
| 3.5"–5" (medium, single-col) | `body_pt − 2` | `body_pt − 3` |
| ≥ 5" (large / two-col) | `body_pt − 2` | `body_pt − 4` |

- Title / suptitle: `body_pt`.
- Caption / `fig.text`: label pt.

Readability floor: no element may render below **6 pt** on the page. If a target falls below, clamp to 6. Enforce `title ≥ label ≥ tick` after clamping.

#### 3b. Strokes — fixed page pt targets (not `W_page`-dependent)

These are matplotlib's long-established typographic conventions for print, tuned to look crisp but not heavy at body-text sizes. They're the same regardless of figure size; it's the `/ s` step that makes the code value differ.

| rcParam | Target page pt |
|---|---|
| `axes.linewidth` (spines) | **0.8** |
| `xtick.major.width`, `ytick.major.width` | **0.8** |
| `xtick.minor.width`, `ytick.minor.width` | **0.5** |
| `grid.linewidth` | **0.5** |
| `patch.linewidth` (bar edges, rect edges) | **0.8** |
| `hatch.linewidth` | **0.8** |
| `boxplot.boxprops.linewidth`, `whiskerprops`, `capprops`, `medianprops` | **0.8** |
| `boxplot.flierprops.markeredgewidth` | **0.5** |

#### 3c. Lengths — fixed page pt targets

| rcParam | Target page pt |
|---|---|
| `xtick.major.size`, `ytick.major.size` | **3.5** |
| `xtick.minor.size`, `ytick.minor.size` | **2.0** |
| `xtick.major.pad`, `ytick.major.pad` | **3.0** |
| `axes.labelpad` | **3.5** |

#### 3d. Plot lines, markers, error bars — `W_page`-dependent

Slightly heavier for large figures so lines remain visible from a distance; slightly lighter for small figures so they don't dominate. Values are on the page.

| Quantity | ≤ 2.5" | 2.5"–5" | ≥ 5" |
|---|---|---|---|
| `lines.linewidth` (page pt) | 1.0 | 1.25 | 1.5 |
| `lines.markersize` (page pt) | 3.0 | 4.0 | 5.0 |
| `lines.markeredgewidth` (page pt) | 0.5 | 0.6 | 0.8 |
| errorbar `capsize` (page pt) | 1.8 | 2.5 | 3.0 |
| errorbar `capthick` (page pt) | same as `axes.linewidth` (0.8) | same | same |

For `scatter`, the `s=` argument is in **points squared**. Default `s=36` → marker diameter 6 pt. Derive `target_scatter_s_pt = (lines.markersize)²` in page pt², then code value = `(markersize_page / s)² = markersize_page² / s²`. Only override `scatter` sizes if user passed no explicit `s=` or passed a constant scalar; if `s=` is a per-point array (encoding data), **do not touch** — it's semantic.

### 4. Compute code values

For every target in section 3 except 3a typography, code value = `page_pt / s`, rounded to:

- 0.5 pt for font sizes and marker/capsize
- 0.1 pt for stroke linewidths

Example at `s = 0.7`:

- `axes.linewidth` page 0.8 pt → code `0.8 / 0.7 = 1.14`
- `lines.linewidth` page 1.25 pt → code `1.25 / 0.7 = 1.79`
- `xtick.major.size` page 3.5 pt → code `3.5 / 0.7 = 5.00`
- label font page 9 pt → code `9 / 0.7 = 12.86 → round 13.0`

### 5. Consistency pass

Before writing, sanity-check the whole visual system:

- Is `title_page_pt ≥ label_page_pt ≥ tick_page_pt`? (Monotonic hierarchy.)
- Is `lines.linewidth_page > axes.linewidth_page`? (Plot strokes should stand out from frame by ≥ 30 %, otherwise data disappears into the frame.)
- Is `lines.markersize_page ≥ 3 × lines.linewidth_page`? (Markers should read as points, not dots on the line.)
- Does the floor apply anywhere? Note it.

If any check fails, explain why and adjust.

### 6. Semantic bar-geometry review (only if plot uses `ax.bar` / `barh`)

Bar `width` is in data coordinates — it does not follow the `/ s` rule. But it can still look wrong after rescaling if the default 0.8 was chosen for a different context:

1. Count the number of bars along the category axis.
2. If the user passed an explicit `width=X` and `X ∈ [0.5, 0.95]`, leave it unchanged (assume intentional).
3. Otherwise, if `width` is default (0.8):
   - With 1–4 bars in a wide figure (`W_page > 4"`): recommend `width = 0.6` (bars look airier).
   - With 10+ bars in any figure: recommend `width = 0.8` (default is fine; keep).
   - With 2–9 bars: keep default 0.8.
4. Grouped bars (multiple `ax.bar` calls with manual offsets): do not touch widths automatically; the user's layout math is semantic.

Always mention this review in the output report, whether or not you changed anything.

### 7. Rewrite the code

1. **Insert a single `plt.rcParams.update({...})` block** right after the matplotlib import, containing **every** computed value from sections 3a–3d. Do not split it. Use these rcParams keys:

   ```python
   plt.rcParams.update({
       # --- Typography ---
       "font.size":             body_pt_code,
       "axes.titlesize":        title_code,
       "figure.titlesize":      title_code,
       "axes.labelsize":        label_code,
       "xtick.labelsize":       tick_code,
       "ytick.labelsize":       tick_code,
       "legend.fontsize":       legend_code,
       "legend.title_fontsize": label_code,
       # --- Strokes ---
       "axes.linewidth":        axes_lw_code,
       "xtick.major.width":     tick_major_w_code,
       "ytick.major.width":     tick_major_w_code,
       "xtick.minor.width":     tick_minor_w_code,
       "ytick.minor.width":     tick_minor_w_code,
       "grid.linewidth":        grid_lw_code,
       "patch.linewidth":       patch_lw_code,
       "hatch.linewidth":       hatch_lw_code,
       # --- Lengths ---
       "xtick.major.size":      tick_major_size_code,
       "ytick.major.size":      tick_major_size_code,
       "xtick.minor.size":      tick_minor_size_code,
       "ytick.minor.size":      tick_minor_size_code,
       "xtick.major.pad":       tick_pad_code,
       "ytick.major.pad":       tick_pad_code,
       "axes.labelpad":         label_pad_code,
       # --- Lines / markers ---
       "lines.linewidth":       lines_lw_code,
       "lines.markersize":      markersize_code,
       "lines.markeredgewidth": marker_edge_w_code,
   })
   ```

2. **Walk the rest of the script** and overwrite every explicit `fontsize=`, `size=`, `linewidth=`/`lw=`, `markersize=`/`ms=`, `markeredgewidth=`/`mew=`, `capsize=`, `capthick=` argument on calls like `set_title`, `set_xlabel`, `set_ylabel`, `text`, `annotate`, `legend`, `plot`, `errorbar`, `bar`, `axhline`, `axvline`, etc. — either delete them (so rcParams takes over) or replace with the newly computed value. **Never leave stale values** that would override your rcParams.

3. For `ax.errorbar(...)` calls, ensure both `capsize` and `capthick` are set (or fall back to rcParams where possible; for `capthick`, matplotlib does not read it from rcParams — set it explicitly per-call with the computed value).

4. For `ax.bar(...)`: apply the semantic width decision from section 6.

5. Do not touch: `figsize`, data, colormaps, linestyles, marker glyphs (`marker='o'` etc.), colors, alpha, axis limits, label text content.

### 8. Output

1. **The full rewritten script**, ready to run.
2. **A visual-system report**, tabulated:

   | Category | Element | Target page value | Code value (`/ s`) |
   |---|---|---|---|
   | Typography | title / label / tick / legend | … pt | … pt |
   | Strokes | axes.linewidth / tick widths / patch / grid | … pt | … pt |
   | Lengths | tick major/minor size, pads | … pt | … pt |
   | Lines | `lines.linewidth`, `markersize`, `markeredgewidth` | … | … |
   | Errorbars | `capsize`, `capthick` | … | … |
   | Bars | width decision and reason | — | — |

3. **Consistency checks** listed explicitly:
   - title ≥ label ≥ tick ✓/✗
   - `lines.linewidth_page > axes.linewidth_page` ✓/✗
   - `markersize_page ≥ 3 × lines.linewidth_page` ✓/✗
   - readability floor hits (which elements, if any)

4. **Scale summary**: `W_page = …, s = …`

## Worked example

Inputs: venue = NeurIPS 2025 (Letter, single-column, `\textwidth ≈ 5.5"`, body 10 pt). `figsize = (5, 3)`, `embed_ratio = 1.0`.

```
W_page = 5.5 * 1.0 = 5.5    → "large" band
s      = 5.5 / 5   = 1.10
```

Typography page pt: title=10, label=8, tick=6 (= body_pt − 4 = 6, at floor). Code pt: 9.0, 7.5, 5.5 — but tick went below 6 on page? No, `6 × 1.10 = 6.6` on page ✓.

Strokes (page → code, `/ 1.10`):
- axes.linewidth: 0.8 → 0.7
- tick.major.width: 0.8 → 0.7
- tick.minor.width: 0.5 → 0.5
- patch.linewidth: 0.8 → 0.7
- grid.linewidth: 0.5 → 0.5

Lengths:
- tick.major.size: 3.5 → 3.2
- tick.minor.size: 2.0 → 1.8

Lines (large band):
- lines.linewidth: 1.5 → 1.4
- lines.markersize: 5.0 → 4.5
- errorbar.capsize: 3.0 → 2.7, capthick = axes.linewidth = 0.7

Consistency checks all pass. Bar review: not applicable (line plot).

## Common mistakes to avoid

- Scaling user-existing values instead of deriving from scratch.
- Updating fonts but leaving `lines.linewidth`, `markersize`, `axes.linewidth` at defaults — creates visual imbalance.
- Changing `figsize`.
- Touching `color`, `cmap`, `linestyle`, `marker` glyphs, `alpha` — these are semantic.
- Treating bar `width=` like a line width (it's data-coord, different rule).
- Forgetting `capthick` for errorbars (not in rcParams; must be set per-call).
- Forgetting to remove stale `fontsize=` / `linewidth=` kwargs that will override your rcParams.
- Scaling scatter `s=` when it's a per-point data-encoding array.
