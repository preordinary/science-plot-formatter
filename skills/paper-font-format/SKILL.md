---
name: paper-font-format
description: Use when a user wants to format a matplotlib plotting script for inclusion in a scientific paper. Derives the full visual system (fonts, line widths, tick widths, marker sizes, bar/patch edges, grid, error-bar caps) from the figure's final physical size on the page, so the figure reads as a visually unified whole at its printed scale. Rescales `figsize` to match the target embed width while preserving the user's aspect ratio, so the saved figure IS its final rendered size. Recomputes every value from scratch — does not scale the user's existing settings.
---

# paper-font-format

You are formatting a matplotlib plotting script so that when its saved figure is embedded into a scientific paper at a specified width, **every visual element — text, strokes, markers, bar edges, error-bar caps, grid — reads at the correct physical size on the printed page, and all of these harmonize so the figure looks like one coherent design.**

## Critical principles

1. **Visual unity is the job, not just font sizing.** Changing text without also adjusting line widths, tick widths, marker sizes, patch edges, and error-bar caps leaves the figure visually unbalanced: big text with hairline axes, or small text with chunky markers. Every time you change a font size, you also change the companion stroke / marker / geometry values.

2. **Never scale the user's existing values.** Users tend to set font sizes, linewidths, and marker sizes by screen trial-and-error; those values are often out of proportion. Multiplying them by a scale factor preserves and amplifies the misproportion. Instead, derive every value from scratch from (a) the paper's body font size and (b) the figure's final physical width on the page, then completely overwrite.

3. **Don't touch the user's composition.** `figsize` aspect ratio, subplot grid, axis limits, legend placement (`loc`, `ncol`, `bbox_to_anchor`), annotation coordinates, axis scales — these are layout/structural decisions the user made. Visual weights are yours to rewrite; composition is not. If a weight rewrite still leaves a composition problem (e.g., a 4-entry legend occupying 40 % of a narrow single-column axes), flag it in the output report and leave the decision to the user.

4. **One exception to rule 3: the absolute scale of `figsize`.** Rescale to `figsize[0] = W_page`, `figsize[1] = h_orig * W_page / w_orig` — aspect ratio preserved (per rule 3), absolute inches matched to the target embed width. This pins `s = 1` so every code value equals its target page pt with no scaling math, and the saved PNG/PDF previews at the paper's printed scale.

5. **Data, colors, colormaps, linestyles, marker glyph choices are semantic** — they express meaning about the data. Never touch them. Only change visual weights, not visual choices.

## The scaling principle

By rule 4, rewrite `figsize` so its width equals `W_page`:

```
figsize_new = (W_page, figsize_orig[1] * W_page / figsize_orig[0])
s           = W_page / figsize_new[0] = 1
```

With `s = 1`, any matplotlib value expressed in **points** (font size, `linewidth`, `markersize`, tick `size`, `capsize`, etc.) renders on the printed page at exactly its code value. So every code value below equals its target page pt directly — no `/ s` division.

(If the user explicitly refuses to rewrite `figsize`, fall back to `s = W_page / figsize_orig[0]` and code value = `target_page_pt / s`. Flag this as a degraded mode — the saved preview will not match the paper.)

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

- **`figsize_orig` `(w, h)`** — read from the target code (`plt.figure(figsize=...)`, `plt.subplots(figsize=...)`). If absent, matplotlib default is `(6.4, 4.8)`; ask the user to confirm. Only the **aspect ratio** `w/h` is preserved; the absolute inches will be rewritten in the next step.
- **`embed_ratio`** — fraction of `column_width_in` this figure occupies (default 1.0; `0.5` = half-column; `2.0` = spans two columns).

### 2. Compute figure page width, rewrite figsize, set scale factor

```
W_page      = column_width_in * embed_ratio
figsize_new = (W_page, figsize_orig[1] * W_page / figsize_orig[0])   # preserve aspect ratio
s           = 1
```

Emit the new `figsize_new` into the rewritten script (see section 7). Report both `figsize_orig` and `figsize_new` in the output so the user sees the resize.

### 3. Derive target page values for every visual category

For every quantity, define the target **on the printed page** (page pt). With the figsize rewrite in section 2, `s = 1` and the code value equals the target page pt directly (rounded to 0.5 pt for fonts/markers, 0.1 pt for strokes). In the degraded fallback mode where figsize is not rewritten, the code value is `target_page_pt / s` with the same rounding.

#### 3a. Typography — depends on `W_page`

**Key principle: the maximum font (title) must step down for non-page-spanning figures.** Only a page-spanning / two-column figure has the real estate to carry title = `body_pt`; a single-column or sub-panel figure with `body_pt` title will visually dominate the small axes area. Axis labels, ticks, and legend step down together to keep a monotonic hierarchy without any one element crowding out the data region.

| `W_page` band | Title / suptitle | Label (axis labels) | Tick / Legend / Annotation |
|---|---|---|---|
| ≤ 2.5" (sub-panel) | `body_pt − 2` | `body_pt − 3` | `body_pt − 4` |
| 2.5"–3.5" (single-col narrow, e.g. ICML/NeurIPS) | `body_pt − 2` | `body_pt − 3` | `body_pt − 3` |
| 3.5"–5" (single-col wide) | `body_pt − 1` | `body_pt − 2` | `body_pt − 3` |
| ≥ 5" (page-spanning / two-col) | `body_pt` | `body_pt − 2` | `body_pt − 3` |

- Caption / `fig.text`: label pt.
- If the script has no `set_title(...)` call, skip the title row — don't invent one.

No absolute readability floor: dense sub-panels may legitimately require fonts below 6 pt, and the skill should not silently clamp the user's design. Still enforce the **relative hierarchy** `title ≥ label ≥ tick ≥ legend` (all may be equal). If any computed page-pt value would fall below 5 pt, flag it in the output report as "sub-5pt: {element} @ {x} pt — verify legibility on the final PDF" but do not clamp.

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

#### 3e. Legend visual weight — `W_page`-dependent rcParams only

A legend that looks fine on a two-column figure can occupy 40 % of a single-column figure's axes area. Tighten the legend's visual weight (frame, padding, handle length) so it reads lighter on small figures. Apply in addition to 3a's `legend.fontsize`:

| rcParam | ≤ 3.5" (single-col / sub-panel) | 3.5"–5" (single-col wide) | ≥ 5" (page-spanning) |
|---|---|---|---|
| `legend.frameon` | `False` | `False` | `True` (or `False` if the axes has a grid) |
| `legend.handlelength` | 1.2 | 1.5 | 2.0 |
| `legend.handletextpad` | 0.4 | 0.5 | 0.6 |
| `legend.columnspacing` | 1.0 | 1.2 | 2.0 |
| `legend.borderpad` | 0.3 | 0.3 | 0.4 |
| `legend.labelspacing` | 0.3 | 0.4 | 0.5 |

**Legend placement, `ncol`, and `bbox_to_anchor` are structural choices — DO NOT rewrite them.** Like `figsize` aspect ratio and the subplot grid, legend location is the user's composition. This skill only adjusts visual weights on the existing `ax.legend(...)` call; it never moves a legend from inside the axes to outside, never flips `loc`, and never changes `ncol`.

If, after the font/padding rewrite, the legend still occupies a large fraction of the axes area (rule of thumb: > 25 % on the PNG preview), **flag it in the output report** — e.g., *"legend occupies ~35 % of axes at `W_page = 3.25"`; consider manually moving it outside with `bbox_to_anchor=(...)` or reducing entries"* — and stop there. Leave the decision to the user.

### 4. Compute code values

With `s = 1` (figsize rewritten per section 2), code value = target page pt directly, rounded to:

- 0.5 pt for font sizes and marker/capsize
- 0.1 pt for stroke linewidths

In the degraded fallback mode (figsize left alone, `s ≠ 1`), code value = `page_pt / s` with the same rounding. Example at `s = 0.7`:

- `axes.linewidth` page 0.8 pt → code `0.8 / 0.7 = 1.14`
- `lines.linewidth` page 1.25 pt → code `1.25 / 0.7 = 1.79`
- label font page 9 pt → code `9 / 0.7 = 12.86 → round 13.0`

### 5. Consistency pass

Before writing, sanity-check the whole visual system:

- Is `title_page_pt ≥ label_page_pt ≥ tick_page_pt ≥ legend_page_pt`? (Monotonic hierarchy; equality is OK.)
- Is `lines.linewidth_page > axes.linewidth_page`? (Plot strokes should stand out from frame by ≥ 30 %, otherwise data disappears into the frame.)
- Is `lines.markersize_page ≥ 3 × lines.linewidth_page`? (Markers should read as points, not dots on the line.)
- Any element below 5 pt on the page? List them in the report for the user to verify on the final PDF (do not clamp).

If any relative-hierarchy or stroke-relation check fails, explain why and adjust.

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

1. **Replace the `figsize=` argument** on `plt.figure(...)` / `plt.subplots(...)` with `figsize_new` from section 2. If the user explicitly asked to keep `figsize_orig`, leave it and proceed in degraded (`s ≠ 1`) mode.

2. **Insert a single `plt.rcParams.update({...})` block** right after the matplotlib import, containing **every** computed value from sections 3a–3d. Do not split it. Use these rcParams keys:

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
       # --- Legend layout (section 3e) ---
       "legend.frameon":        legend_frameon,
       "legend.handlelength":   legend_handlelength,
       "legend.handletextpad":  legend_handletextpad,
       "legend.columnspacing":  legend_columnspacing,
       "legend.borderpad":      legend_borderpad,
       "legend.labelspacing":   legend_labelspacing,
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

3. **Walk the rest of the script** and overwrite every explicit `fontsize=`, `size=`, `linewidth=`/`lw=`, `markersize=`/`ms=`, `markeredgewidth=`/`mew=`, `capsize=`, `capthick=` argument on calls like `set_title`, `set_xlabel`, `set_ylabel`, `text`, `annotate`, `legend`, `plot`, `errorbar`, `bar`, `axhline`, `axvline`, etc. — either delete them (so rcParams takes over) or replace with the newly computed value. **Never leave stale values** that would override your rcParams.

4. For `ax.errorbar(...)` calls, ensure both `capsize` and `capthick` are set (or fall back to rcParams where possible; for `capthick`, matplotlib does not read it from rcParams — set it explicitly per-call with the computed value).

5. For `ax.bar(...)`: apply the semantic width decision from section 6.

6. Do not touch: the aspect ratio of `figsize` (only its absolute scale, per section 2), data, colormaps, linestyles, marker glyphs (`marker='o'` etc.), colors, alpha, axis limits, label text content.

### 8. Output

1. **The full rewritten script**, ready to run.
2. **Figsize report**: `figsize_orig = (…, …)` → `figsize_new = (…, …)`; aspect ratio preserved.
3. **A visual-system report**, tabulated (with `s = 1`, code value = page value):

   | Category | Element | Page pt | Code pt |
   |---|---|---|---|
   | Typography | title / label / tick / legend | … | … |
   | Strokes | axes.linewidth / tick widths / patch / grid | … | … |
   | Lengths | tick major/minor size, pads | … | … |
   | Lines | `lines.linewidth`, `markersize`, `markeredgewidth` | … | … |
   | Errorbars | `capsize`, `capthick` | … | … |
   | Bars | width decision and reason | — | — |

4. **Consistency checks** listed explicitly:
   - title ≥ label ≥ tick ≥ legend ✓/✗
   - `lines.linewidth_page > axes.linewidth_page` ✓/✗
   - `markersize_page ≥ 3 × lines.linewidth_page` ✓/✗
   - sub-5pt elements (list all, if any — not clamped)

5. **Scale summary**: `W_page = …, s = … (= 1 under the figsize rewrite; report actual s in degraded mode)`.

## Worked example

Inputs: venue = NeurIPS 2025 (Letter, single-column, `\textwidth ≈ 5.5"`, body 10 pt). `figsize_orig = (5, 3)`, `embed_ratio = 1.0`.

```
W_page      = 5.5 * 1.0 = 5.5    → "large" band
figsize_new = (5.5, 3 * 5.5/5) = (5.5, 3.3)    # aspect 5:3 preserved
s           = 1
```

Typography (page pt = code pt, `W_page = 5.5"` falls in the ≥ 5" band): title=10, label=8, tick=7, legend=7.

Strokes (page pt = code pt):
- axes.linewidth: 0.8
- tick.major.width: 0.8
- tick.minor.width: 0.5
- patch.linewidth: 0.8
- grid.linewidth: 0.5

Lengths:
- tick.major.size: 3.5
- tick.minor.size: 2.0

Lines (large band):
- lines.linewidth: 1.5
- lines.markersize: 5.0
- errorbar.capsize: 3.0, capthick = 0.8

Consistency checks all pass; no sub-5pt elements. Bar review: not applicable (line plot).

## Common mistakes to avoid

- Scaling user-existing values instead of deriving from scratch.
- Updating fonts but leaving `lines.linewidth`, `markersize`, `axes.linewidth` at defaults — creates visual imbalance.
- Changing the **aspect ratio** of `figsize` (only the absolute scale is rewritten, per section 2).
- Forgetting to update `figsize` so the saved preview matches the paper rendering.
- Touching `color`, `cmap`, `linestyle`, `marker` glyphs, `alpha` — these are semantic.
- Treating bar `width=` like a line width (it's data-coord, different rule).
- Forgetting `capthick` for errorbars (not in rcParams; must be set per-call).
- Forgetting to remove stale `fontsize=` / `linewidth=` kwargs that will override your rcParams.
- Scaling scatter `s=` when it's a per-point data-encoding array.
- Silently clamping sub-5pt fonts — flag them instead.
- Keeping `title = body_pt` on a single-column figure — the title will dominate a small axes area. Step the title down per the 3a table.
- Moving the legend outside the axes or changing its `ncol` — that's **structural**, not visual weight. Only the user decides legend placement; the skill flags the problem in the report but never rewrites the `ax.legend(...)` location/`ncol`/`bbox_to_anchor` kwargs.
- Overwriting the user's composition in general — `figsize` aspect ratio, subplot grid, axis limits, legend location, annotation positions are all structural and stay untouched.
