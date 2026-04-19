---
name: match-reference-style
description: Use when a user has one matplotlib script already tuned visually (the reference) and another script to harmonize with it for joint inclusion in a paper. Aligns the whole visual system — typography, line widths, tick widths, marker sizes, patch edges, error-bar caps — to match the reference's on-page appearance, and redesigns the target's figsize to fit the composed layout. Unlike paper-font-format, figsize is rewritten here; unlike a literal copy, numbers are never copied directly because the two figures may differ in chart type, scale, and page position.
---

# match-reference-style

You are aligning a target matplotlib script to a reference matplotlib script so that **when both figures appear together in the paper, every visual element reads at a consistent physical size and stroke weight across the two figures** — fonts, line widths, tick widths, marker sizes, patch edges, error-bar caps — while respecting each chart type's natural aspect ratio.

## Critical principles

1. **Match the physical truth on the printed page, not the code numbers.**
   The reference's `figsize`, `fontsize`, `linewidth`, `markersize` etc. are only correct for the reference's own scale factor. Copy them and they render at the wrong physical size in the target. The invariant to preserve across the two figures is what the reader *sees on the page*: the on-page pt of every text element, the on-page pt of every stroke, the on-page pt of every marker.

2. **Harmonize the entire visual system, not just fonts.**
   If the reference's axes spines render at 0.8 pt on the page, the target's must too — otherwise one figure looks heavier than the other even with matching text. The same goes for plot line thickness, tick widths, marker sizes, bar/patch edges, and error-bar caps. Mismatched stroke weight is as visually jarring as mismatched text.

3. **Redesign `figsize` for the composed layout.**
   Unlike `paper-font-format`, the target's `figsize` **is** rewritten here, because the two figures are being composed into a shared layout (side-by-side, stacked, etc.). Natural aspect ratio of the target chart type is a soft constraint: prefer matching the reference's on-page height, but clamp within ±20 % of the target's natural aspect so a line plot isn't crushed square or a heatmap stretched flat.

4. **Never scale by a ratio of reference / target code values.**
   Always go through the physical-page layer: `ref_code_value × s_ref → page_value → page_value / s_tgt = tgt_code_value`.

5. **Data and semantics untouched.** Colors, colormaps, linestyles, marker glyphs, data, axis labels' text — none of these change.

## The relations

For the reference:

```
s_ref       = (column_width_in * ref_embed_ratio) / w_ref
W_ref_page  = column_width_in * ref_embed_ratio
H_ref_page  = h_ref * s_ref
page_val[e] = ref_code_val[e] * s_ref          # for every point-valued element
```

For the target (after choosing `tgt_figsize_new`):

```
s_tgt       = W_tgt_page / tgt_figsize_new[0]
tgt_code_val[e] = page_val[e] / s_tgt          # page-pt matches reference
```

## Step-by-step procedure

### 1. Gather inputs

**Step A — venue first.** Ask: *"What conference or journal are you submitting to?"* Use `WebSearch` / `WebFetch` on the official author guidelines / LaTeX class file to extract paper size, column layout, column width, body font size. Show the user what you found with a source URL. Fall back to asking directly if lookup fails.

**Step B — always-required inputs:**

1. **Reference script path** and **target script path**.
2. **Layout relationship** in the paper:
   - `side-by-side-same-column` — both fit in one column
   - `side-by-side-two-column` — side-by-side across a two-column page
   - `stacked` — one above the other
   - `independent` — just want consistency, no shared row/column
3. **Reference `embed_ratio`** — what fraction of a column the reference occupies (commonly 0.5 for half-column, 1.0 for full-column, 2.0 for two-column-spanning).
4. **Inter-figure gap** for side-by-side layouts (default **0.15"**).

### 2. Extract the reference's physical truth

Read the reference script. Extract:

- `ref_figsize = (w_ref, h_ref)` from the code.
- `ref_code_val` for every visual element it sets (rcParams + explicit kwargs). Categories to cover, matching section 3 of `paper-font-format`:
  - **Typography**: title, label, tick, legend, annotation, suptitle.
  - **Strokes**: `axes.linewidth`, `xtick.major.width`/`ytick.major.width`, `xtick.minor.width`/`ytick.minor.width`, `grid.linewidth`, `patch.linewidth`, `hatch.linewidth`, boxplot widths.
  - **Lengths**: `xtick.major.size`/`ytick.major.size`, `xtick.minor.size`/`ytick.minor.size`, tick pads, `axes.labelpad`.
  - **Lines/markers**: `lines.linewidth`, `lines.markersize`, `lines.markeredgewidth`.
  - **Errorbars** (if present): `capsize`, `capthick`.
  - **Bar width** (if reference uses `ax.bar`): record the numeric width argument (data-coord, not to be `/ s`-ed).

For unset elements, use matplotlib's defaults:

| Element | matplotlib default |
|---|---|
| `font.size` | 10 |
| `axes.titlesize` | 1.2 × font.size (≈ 12) |
| `axes.labelsize` | font.size (≈ 10) |
| `xtick.labelsize` / `ytick.labelsize` | font.size (≈ 10) |
| `legend.fontsize` | font.size (≈ 10) |
| `axes.linewidth` | 0.8 |
| `xtick.major.width` | 0.8 |
| `xtick.minor.width` | 0.6 |
| `xtick.major.size` | 3.5 |
| `xtick.minor.size` | 2.0 |
| `lines.linewidth` | 1.5 |
| `lines.markersize` | 6.0 |
| `patch.linewidth` | 1.0 |
| `grid.linewidth` | 0.8 |

Then compute `s_ref` and for every element:

```
page_val[e] = ref_code_val[e] * s_ref
```

Also record `W_ref_page`, `H_ref_page` for layout math.

### 3. Choose target on-page width and height

**Width** — from layout:

| Layout | `W_tgt_page` |
|---|---|
| side-by-side-same-column | `(column_width_in - gap - W_ref_page)` or even split `(column_width_in - gap) / 2` |
| side-by-side-two-column | `(2 * column_width_in + col_gap - gap - W_ref_page)` |
| stacked | `W_ref_page` |
| independent | ask user; default `column_width_in * embed_ratio_tgt` |

**Height** — from chart type + reference:

1. Detect target chart type (`imshow`/`pcolormesh`/`sns.heatmap` → heatmap; `plot` → line; `scatter`; `bar`/`barh`; `hist`/`kdeplot`/`violinplot`/`boxplot` → distribution; `contour`/`contourf` → spatial).
2. Natural aspect (`height / width`): heatmap/spatial 1.00; line/scatter/bar 0.62; distribution 0.75; unknown 0.62.
3. `H_nat = W_tgt_page * natural_aspect`.
4. If layout is side-by-side or stacked and `H_ref_page ∈ [H_nat × 0.8, H_nat × 1.2]`: use `H_tgt_page = H_ref_page` (full match, preferred).
5. Otherwise clamp: `H_tgt_page = clamp(H_ref_page, H_nat × 0.8, H_nat × 1.2)` — stay close to reference but don't deform target by more than ±20 %.
6. For `independent`, just use `H_nat`.

Always **report** which branch you took (full match vs clamp), so the user understands why.

### 4. Set target figsize and scale

Use the on-page dimensions as figsize itself (`embed_ratio_tgt = 1.0`):

```
tgt_figsize_new = (W_tgt_page, H_tgt_page)
s_tgt           = 1.0
```

(If user wants a specific non-1 embed ratio for the target — e.g., they'll further shrink it in LaTeX — divide figsize accordingly and set `s_tgt = embed_ratio_tgt`.)

### 5. Compute target code values per element

For every element category from section 2, the target's code value = reference's on-page value divided by target's scale:

```
tgt_code_val[e] = page_val[e] / s_tgt
```

Apply the same consistency net from `paper-font-format`:

- Readability floor: if any element's `page_val` < 6 pt (for text) or violates the stroke-vs-frame / marker-vs-line invariants below, raise it.
- Ordering: `title ≥ label ≥ tick` on page (in page pt). Clamp upward if the reference itself violates this and it would look odd.
- `lines.linewidth_page > axes.linewidth_page` — plot strokes must stand out from the frame.
- `markersize_page ≥ 3 × lines.linewidth_page` — markers read as points, not dots on the line.

Round code values: 0.5 for fonts and markers; 0.1 for stroke linewidths.

### 6. Errorbars — explicit per-call

`capthick` is not read from rcParams; it must be set explicitly on each `ax.errorbar(...)` call. Target's `capthick_code = page_val[axes.linewidth] / s_tgt`. Target's `capsize_code = page_val[capsize] / s_tgt` (where `page_val[capsize]` is taken from the reference if present, else the default band value from `paper-font-format` section 3d at the target's `W_tgt_page` band).

### 7. Bar geometry (if target uses `ax.bar` / `barh`)

Bar `width=` is data-coord, not `/ s`. Harmonization rule:

1. If the target explicitly sets `width=X` with `X ∈ [0.5, 0.95]`, leave it.
2. If the reference also uses bars and sets `width=X_ref`, copy that to the target (assumes user has deliberately tuned it).
3. Otherwise, apply the section-6 semantic rule from `paper-font-format` at the target's `W_tgt_page` and its own bar count.

Do not port the reference's bar width to a target that is not a bar chart.

### 8. Rewrite the target script

1. Replace its `figsize` with `tgt_figsize_new`.
2. Insert or overwrite a single `plt.rcParams.update({...})` block after the matplotlib import, containing the full visual system (same keys as listed in `paper-font-format` section 7).
3. Walk the target script and overwrite every explicit `fontsize=`, `linewidth=`/`lw=`, `markersize=`/`ms=`, `markeredgewidth=`/`mew=`, `capsize=`, `capthick=`, `size=` kwarg. Never leave stale values.
4. For `ax.errorbar` calls, set `capsize` and `capthick` explicitly to the computed values.
5. Apply the bar width decision (section 7) if applicable.
6. Do not touch: data, colormaps, colors, linestyles, marker glyphs, alpha, axis limits, label text.

### 9. Output

1. **The rewritten target script**, ready to run.
2. **Side-by-side comparison table** — for every visual element, `reference page value | target page value | target code value`:

   | Category | Element | Reference page | Target page | Target code |
   |---|---|---|---|---|
   | Typography | title / label / tick / legend / annotation | … | … | … |
   | Strokes | axes / tick-major / tick-minor / grid / patch | … | … | … |
   | Lengths | tick.major.size / tick.minor.size / pads | … | … | … |
   | Lines | lines.linewidth / markersize / markeredgewidth | … | … | … |
   | Errorbars | capsize / capthick | … | … | … |
   | Bars (if any) | width decision | … | … | … |

3. **Layout note**: `W_ref_page × H_ref_page` vs `W_tgt_page × H_tgt_page`; which height branch was taken (full match or ±20 % clamp) and why.
4. **Consistency checks**: the same four checks as `paper-font-format` step 5, run on the target's final page values.

## Worked example

Venue: Nature Communications (double-column, column_width_in = 3.5", body_pt = 7).

Reference: heatmap, `ref_figsize = (3.5, 3.5)`, sets `font.size=14`, `axes.titlesize=14`, `axes.labelsize=12.6`, `xtick.labelsize=11.2`, `ytick.labelsize=11.2`, `legend.fontsize=11.2`, `axes.linewidth=1.6`, `xtick.major.width=1.6`, `xtick.major.size=7`, `lines.linewidth=2`, `lines.markersize=8`.

User says `ref_embed_ratio = 0.5`. Then:

- `W_ref_page = 3.5 × 0.5 = 1.75"`, `s_ref = 1.75 / 3.5 = 0.5`, `H_ref_page = 1.75"`.
- Page values: title = 14 × 0.5 = 7 pt, label = 12.6 × 0.5 = 6.3 pt, tick = 11.2 × 0.5 = 5.6 pt → **below 6 pt floor, clamp to 6**. Axes linewidth page = 1.6 × 0.5 = 0.8 pt. lines.linewidth page = 2 × 0.5 = 1.0 pt. markersize page = 8 × 0.5 = 4.0 pt. tick.major.size page = 7 × 0.5 = 3.5 pt. patch.linewidth page = 1.0 × 0.5 = 0.5 pt.

Target: line plot, layout = `side-by-side-same-column`, `gap = 0.15`.

- `W_tgt_page = (3.5 - 0.15) / 2 ≈ 1.675"` (assuming even split). Nature has gutter; the actual available may be slightly less but this is fine for a 0.1 Ball-park.
- Natural aspect for line plot = 0.62 → `H_nat = 1.675 × 0.62 ≈ 1.04"`.
- `H_ref_page = 1.75"` outside `[0.83, 1.24]`; clamp → `H_tgt_page = 1.24"`.
- `tgt_figsize_new = (1.675, 1.24)`, `s_tgt = 1.0`.
- Every target code value = page value (identity at `s_tgt = 1.0`):
  - Typography (post-floor): title 7, label 6.5, tick/legend 6.0 (rounded).
  - Strokes: axes 0.8, tick.major.width 0.8, tick.minor.width 0.5, grid 0.5, patch 0.5 (copied page-pt from ref).
  - Lengths: tick.major.size 3.5, tick.minor.size 2.0, pads 3.0.
  - Lines: lines.linewidth 1.0, markersize 4.0, markeredgewidth 0.5.
  - Errorbars: capsize 2.0, capthick 0.8.
- Layout note: target held at 1.24" tall (vs reference 1.75") to avoid deforming the line plot's natural 3:2 ratio.
- Consistency checks: title 7 ≥ label 6.5 ≥ tick 6.0 ✓; lines.linewidth 1.0 > axes.linewidth 0.8 ✓; markersize 4.0 ≥ 3 × 1.0 ✓.

## Common mistakes to avoid

- Copying `figsize` or `fontsize` literal numbers from reference to target — always go through page-pt.
- Matching only fonts, leaving strokes/markers/patches at target's old values — creates visual mismatch between the two figures.
- Forcing target height = reference height even when it deforms the target's chart type (skip the ±20 % clamp).
- Forgetting `capthick` per-call on errorbars.
- Copying reference bar width to a target that isn't a bar chart.
- Scaling user's scatter `s=` when it's a per-point data-encoding array.
- Ignoring the readability floor — a reference that itself renders tick text below 6 pt on page should be clamped in the target (floors fix errors, they don't propagate them).
