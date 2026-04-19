---
name: match-reference-style
description: Use when a user has one matplotlib script they have already tuned visually (the reference) and another script they want visually harmonized with it for joint inclusion in a paper. Unlike paper-font-format, this skill also rewrites figsize — because the two figures will share a layout (typically side-by-side), and the target may be a different chart type whose natural aspect ratio differs from the reference.
---

# match-reference-style

You are aligning a target matplotlib script to a reference matplotlib script so that **when both figures appear together in the paper, they look visually unified** — same on-page font sizes, coordinated heights — while still respecting each chart type's natural proportions.

## Critical principle

**Do not copy the reference's `figsize` or `fontsize` numbers literally.** Those numbers are only correct for the reference's own scale factor and chart type. What you preserve across the two figures is the **physical truth on the printed page**:

- Each font element should render at the same absolute pt on the page in both figures (so readers perceive consistent text).
- The target's on-page height should coordinate with the reference's on-page height (often equal in a side-by-side layout), but with the target's natural aspect ratio as a soft constraint so you don't crush a line plot into a square or stretch a heatmap flat.

This is different from `paper-font-format`: there, `figsize` is fixed by the user. Here, you redesign `figsize` for the target because it's being composed with another figure.

## Inputs to gather

Like `paper-font-format`, start from the submission target, not from column-width numbers.

### Step A — ask for the venue first

Ask: **"What conference or journal are you submitting to?"** Then use `WebSearch` / `WebFetch` to look up the venue's current author guidelines and extract paper size, column layout, column width, and body font size. Show the user what you found (with source URL) and let them confirm or correct.

Prefer primary sources: the venue's author-kit / LaTeX class file / official "for authors" page. Templates change between years, so do not rely on memory — always look up current values.

If venue lookup fails or the user can't name one, fall back to asking directly for `column_width_in` and `body_pt` (default 6.5" / 12 pt for generic single-column A4/Letter).

### Always-required inputs (regardless of venue)

After venue is resolved, also ask for:

1. **Reference script path** and **target script path**.
2. **Layout relationship** between the two figures in the paper:
   - `side-by-side-same-column` (both fit in one column)
   - `side-by-side-two-column` (side-by-side across a two-column page)
   - `stacked` (one above the other)
   - `independent` (just want visual consistency, no shared row/column)
3. **Reference `embed_ratio`** — what fraction of a column does the reference occupy in the final paper? (This is how you derive the reference's scale. Common: 0.5 for half-column, 1.0 for full-column, 2.0 for two-column-spanning.)
4. **Inter-figure gap** for side-by-side layouts (default **0.15"**).

## Step-by-step procedure

### 1. Extract the reference's "physical truth"

Read the reference script. Determine:

- `ref_figsize = (w_ref, h_ref)` from the code.
- `ref_font_code = { title, label, tick, legend, annotation }` in code pt — read from both `rcParams` updates and explicit `fontsize=` args. If an element has no explicit value, fall back to the rcParams default it would inherit (e.g., `axes.titlesize` defaults to `font.size * 1.2` — but if `font.size` is untouched you can assume 10.0).
- Reference scale: `s_ref = (column_width_in * ref_embed_ratio) / w_ref`.
- Reference on-page dimensions: `W_ref_page = column_width_in * ref_embed_ratio`, `H_ref_page = h_ref * s_ref`.
- Reference on-page pt per element: `page_pt[elem] = ref_font_code[elem] * s_ref`.

### 2. Determine the target's on-page dimensions

Target on-page **width** is driven by layout:

| Layout | Target `W_tgt_page` |
|---|---|
| side-by-side-same-column | `(column_width_in - gap - W_ref_page)` (or `(column_width_in - gap) / 2` if split evenly) |
| side-by-side-two-column | `(2 * column_width_in + col_gap - gap - W_ref_page)` |
| stacked | `W_ref_page` (match reference width) |
| independent | ask user; default `column_width_in * embed_ratio_tgt` |

Target on-page **height** is where chart-type aesthetics kick in:

1. Detect the target's chart type from its code. Typical signals:
   - heatmap / confusion matrix: `imshow`, `pcolormesh`, `sns.heatmap`
   - line / timeseries: `plot` with many `plot` calls or x is ordered sequence
   - scatter: `scatter`
   - bar: `bar` / `barh`
   - distribution: `hist`, `kdeplot`, `violinplot`, `boxplot`
   - map / spatial: `contour`, `contourf`, `tricontour`
2. Look up natural aspect ratio (height / width) for that type:
   - heatmap / spatial: **1.0** (square)
   - line / scatter / timeseries: **0.62** (roughly 3:2 wide, close to golden ratio)
   - bar: **0.62**
   - distribution: **0.75** (4:3-ish)
   - other / unknown: **0.62**
3. Compute the "natural" height: `H_nat = W_tgt_page * natural_aspect`.
4. Coordinate with reference:
   - If layout is side-by-side (any kind) or stacked: prefer `H_tgt_page = H_ref_page` to make the row or column align.
   - If `H_ref_page` falls within `[H_nat * 0.8, H_nat * 1.2]`, use `H_tgt_page = H_ref_page` (full match).
   - Otherwise, use `H_tgt_page = clamp(H_ref_page, H_nat * 0.8, H_nat * 1.2)` — stay close to reference but don't deform the target's natural proportions by more than ±20%.
   - If layout is `independent`, just use `H_nat` and skip coordination.
5. **Report** which branch was taken (full match vs clamped), so the user knows why the two figures aren't exactly the same height.

### 3. Set target figsize

Simplest: use the on-page dimensions as the figsize itself (`embed_ratio_tgt = 1.0`), so the scale is 1:1 by construction.

```
tgt_figsize_new = (W_tgt_page, H_tgt_page)
s_tgt           = 1.0
```

(If user wants a specific non-1 embed ratio for the target, compute `tgt_figsize_new = (W_tgt_page / embed_ratio_tgt, H_tgt_page / embed_ratio_tgt)` and `s_tgt = embed_ratio_tgt` — but default to 1:1 unless asked.)

### 4. Compute target code pt per element

For each element, target code pt = reference's on-page pt divided by the target's scale:

```
tgt_code_pt[elem] = page_pt[elem] / s_tgt
```

Then apply safety floors (same as `paper-font-format`):

- Any element whose `page_pt` is < 6 gets raised to 6 before dividing by `s_tgt`.
- Keep `title ≥ label ≥ tick` on page; clamp if the reference violates this.

Round code pt to nearest **0.5 pt**.

### 5. Line and marker widths

Scale by `1 / s_tgt` (same as `paper-font-format` step 5), but use the reference's page-pt line width as the anchor if the reference explicitly sets it. Otherwise use the same defaults (`axes.linewidth = 0.8 / s_tgt`, etc.).

### 6. Rewrite the target script

- Replace its `figsize` with `tgt_figsize_new`.
- Insert (or overwrite) a single `plt.rcParams.update({...})` block right after the matplotlib import, with all font sizes and line widths.
- Walk the rest of the target script and replace every explicit `fontsize=<N>` / `size=<N>` kwarg with the matching computed code pt (or drop it so the rcParams value takes effect).
- Do **not** change:
  - data, colormaps, linestyles, marker choices, alpha, etc.
  - axis labels' text, tick labels' text, legend text
  - the structural choice of plot types and their order

### 7. Output

1. **The rewritten target script**, ready to run.
2. **A comparison table**:

   | Element | Reference page pt | Target page pt | Target code pt |
   |---|---|---|---|
   | title | ... | ... | ... |
   | label | ... | ... | ... |
   | tick  | ... | ... | ... |
   | legend | ... | ... | ... |

3. **A layout note**: the on-page dimensions of reference and target, and why the target height is what it is (full match vs ±20% clamp) given its chart type.

## Worked example

Reference: a heatmap, `ref_figsize=(3.5, 3.5)`, `font.size=10`, `axes.titlesize=10`, `axes.labelsize=9`, `xtick.labelsize=8`. User will embed it at full width of a 3.5" column (`ref_embed_ratio = 1.0`).

- `s_ref = 3.5 / 3.5 = 1.0`
- `W_ref_page = 3.5"`, `H_ref_page = 3.5"`
- Page pt: title=10, label=9, tick=8.

Target: a line plot, layout = `side-by-side-same-column`, `column_width_in = 3.5`, `gap = 0.15`.

- `W_tgt_page = (3.5 - 0.15 - 3.5)` → negative; this layout doesn't fit. Fall back to even split: `(3.5 - 0.15) / 2 = 1.675"` (and tell the user the reference is too wide to sit next to the target in one column — prompt for resolution).

Alternative with realistic sizing (`ref_embed_ratio = 0.5`):

- `W_ref_page = 1.75`, `s_ref = 1.75 / 3.5 = 0.5`, `H_ref_page = 1.75`.
- `W_tgt_page = (3.5 - 0.15) / 2 = 1.675"`.
- Target is a line plot → natural aspect = 0.62 → `H_nat = 1.675 * 0.62 ≈ 1.04"`.
- `H_ref_page = 1.75` is outside `[H_nat * 0.8, H_nat * 1.2] = [0.83, 1.24]`, so clamp: `H_tgt_page = 1.24"`.
- `tgt_figsize_new = (1.675, 1.24)`, `s_tgt = 1.0`.
- Page pt inherited from reference: title=10, label=9, tick=8 → code pt identical (since `s_tgt = 1`).
- Layout note to user: target held below reference height (1.24" vs 1.75") to avoid deforming the line plot's natural 3:2 ratio.

## Common mistakes to avoid

- Copying `figsize` directly from the reference — it was sized for the reference's embedding, not the target's.
- Copying code-pt fontsize values directly — they're only correct for `s_ref`, not `s_tgt`.
- Forcing the target to match the reference's height exactly even when the chart type makes it ugly — the ±20% clamp is there for a reason.
- Treating the two figures as independent — the whole point is page-level visual harmony.
