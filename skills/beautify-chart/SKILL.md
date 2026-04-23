---
name: beautify-chart
description: Use when a user wants to beautify a matplotlib plotting script for a specific conference/journal submission. Takes the script path, venue name, and the figure's fraction of column width; renders the chart, inspects it critically, rewrites the visual system (figsize, fonts, linewidths, markers, ticks, legend weight), then re-renders and verifies. Always renders before editing and after editing. Never silently claims "no issues".
---

# beautify-chart

This skill turns an existing matplotlib script into a publication-ready figure for a specific venue. It is defined by a **render → inspect → rewrite → re-render → verify** loop. You are not permitted to edit code before you have rendered the figure and looked at it, and you are not permitted to call the task done before you have re-rendered and looked at it again.

## Inputs

Collect from the user (ask only for what is missing):

1. `script_path` — absolute path to the matplotlib `.py` script.
2. `venue` — target conference or journal (e.g. "NeurIPS 2026", "Nature Communications", "ICML 2026").
3. `fraction` — the figure's fraction of column width, as used on the page:
   - `0.5` → half a column
   - `1.0` → one full column (single-column width)
   - `2.0` → full textwidth (both columns)
   - values in between are allowed (e.g. `1.5`).

Do **not** ask the user for raw numbers like `column_width_in` or `body_pt`. Derive those from the venue.

## Phase 1 — Venue lookup (live)

Use `WebSearch` / `WebFetch` to pull the venue's official author/style guide. Extract:

- `column_width_in` — single-column text width in inches.
- `textwidth_in` — full two-column (or full page) text width in inches, if the venue is two-column.
- `body_pt` — paper body font size in pt.
- Font family requirement (Times / Helvetica / Computer Modern / sans, if mandated).

Compute the figure's final physical width on the page:

- `fraction ≤ 1.0` → `W_page = fraction × column_width_in`.
- `fraction  > 1.0` → `W_page = (fraction / 2.0) × textwidth_in` for two-column venues (so `2.0` = full textwidth). For single-column venues, `W_page = fraction × column_width_in` clamped by `textwidth_in`.

If the lookup genuinely fails after a good-faith attempt, state so explicitly and ask the user for `column_width_in` and `body_pt` as a fallback. Never silently invent numbers.

Record the retrieved values in chat so the user can sanity-check them.

## Phase 2 — Baseline render (BEFORE any edit)

**Hard rule: no code edit is allowed until the baseline image has been produced and read.**

1. Read the script. Find where/how it saves the figure (`plt.savefig(...)`, `fig.savefig(...)`) or whether it only calls `plt.show()`.
2. If the script already saves to a known path, use that path for the baseline.
3. If it only calls `plt.show()`:
   - Ask the user to confirm adding a minimal `plt.savefig("before.png", dpi=200, bbox_inches="tight")` at the end (this is pre-edit instrumentation, not a visual change).
   - Prefer saving next to the script, in a subdir like `<script_dir>/_beautify/before.png`.
4. Run the script headlessly via `Bash`:
   ```
   MPLBACKEND=Agg python <script_path>
   ```
   Use the script's own working directory. Do not alter its data loading.
5. Use the `Read` tool on the produced PNG to actually see the figure. Do not skip this — you must look at the pixels.

If the script fails to run, fix only the minimum needed to produce the baseline (e.g. a missing output directory). Never silently "fix" plot style during this phase.

## Phase 3 — Critical inspection

Look at the rendered image **as it will appear at `W_page` inches wide on the page**, not at screen size. Mentally shrink it to the target physical width.

Inspect broadly, across at least these dimensions:

- **Legibility at target size** — will tick labels, axis labels, legend, and annotations still be readable at `W_page`? Any text that would drop below ~5pt on the printed page is a problem.
- **Visual hierarchy** — title vs axis labels vs tick labels vs legend vs annotations. Ordering should feel deliberate, not accidental.
- **Overlap / collision** — tick labels colliding with each other, legend covering data, title clipped, colorbar label truncated, subplot labels overlapping axes.
- **Weight balance** — data lines should stand out from axis spines; markers should read as points (not dots or blobs); grid should recede; errorbar caps should be visible but not dominant.
- **Tick density and rotation** — too many ticks, awkward rotation, scientific-notation clutter.
- **Legend** — position, frame, padding, handle length; is it stealing data real estate?
- **Colorbar** — present when needed, proportioned to the axes, label legible.
- **Whitespace / layout** — uneven margins, unused space, subplots too cramped or too loose.
- **Venue-specific constraints** — mandated font family, grayscale legibility if the venue prints B&W, any hard figure-size limit.

Write the observations out in chat as a numbered list. Tie each to what you see (e.g. *"Tick labels at 14pt on a 5″ figsize become ~9pt on a 3.3″ column — still readable, but the title at 11pt on-figure would shrink to ~7pt and look cramped next to them"*).

**Self-check before leaving this phase:**

> "If you found zero issues on first inspection, you weren't looking hard enough."

If your draft list has zero items, or only generic filler, re-inspect. Zoom mentally to the page width, look at each element again, check every subplot, check the legend and colorbar. A figure that truly needs no change is extremely rare — state an explicit reason if you conclude the baseline is already paper-ready (e.g. "the script already calls a house-style rcParams block that matches venue spec").

## Phase 4 — Design the visual system

From `venue`, `W_page`, `body_pt`, chart type, and the Phase 3 issues, decide the target visual system. All numbers below are values **on the printed page** — if you leave `figsize` width equal to `W_page`, the code values equal the page values (scale factor = 1); otherwise divide by the scale factor.

- **`figsize`** — set width to `W_page`. Pick height from chart-type aesthetic unless the user composed something deliberate:
  - heatmap / spatial / confusion matrix → ~1.00 × width (square)
  - line / scatter / bar → ~0.60–0.70 × width
  - distribution / violin / box → ~0.75 × width
  State the aspect choice and why. If the user's original aspect looks deliberate (e.g. time series spanning many seasons), preserve it and only rewrite the absolute scale.
- **Typography (pt on page)** — axes labels / tick labels / legend / annotations. Anchor around `body_pt`: tick/legend usually `body_pt − 2` to `body_pt − 3`, axis labels around `body_pt − 1` to `body_pt`. Enforce label ≥ tick on the page.
- **On-figure title (`axes.titlesize`)** — paper figures sit under a `\caption{}` that does the primary labeling, so the on-figure title is *auxiliary*, not the head of the visual hierarchy. On column-width panels (W_page ≤ column_width, height ≤ ~2"), set `axes.titlesize ≤ axes.labelsize` (e.g. 7.5 when labels are 8) and keep `axes.titlepad` ≤ 2.0. The "title ≥ label ≥ tick" rule applies only to *standalone* figures (slides, posters, un-captioned supplementary plots); for captioned paper figures, the rule is `label ≥ title` and `label ≥ tick`. If the user's script has no title and a caption is present, consider leaving it that way — matplotlib's default `axes.titlesize=12` is calibrated for 6–8" figures and will dominate any column-width panel regardless of what pt you set it to, so a small title often adds nothing over an empty slot + caption. Reason this is a common failure: matplotlib's defaults plus notebook-sized figsize make titles look right at 8" wide, then the figure gets pasted into a 3.25" column and the title that was 10% of figure height becomes 25% without anyone noticing.
- **Strokes** — `axes.linewidth`, `xtick.major.width`, `ytick.major.width`, `xtick.minor.width`, `ytick.minor.width`, `grid.linewidth`, `patch.linewidth`.
- **Data elements** — `lines.linewidth`, `lines.markersize`, `lines.markeredgewidth`. Data lines should be visibly thicker than axis spines. Markers must be ≥ ~3× line width to read as points, not thickenings.
- **Errorbars** — set `capsize` and `capthick` explicitly on each `errorbar(...)` call (capthick is not in rcParams).
- **Legend** — `legend.frameon`, `legend.handlelength`, `legend.handletextpad`, `legend.columnspacing`, `legend.labelspacing`, `legend.borderpad`, `legend.fontsize`.
- **Tick geometry** — `xtick.major.size`, `xtick.minor.size`, `ytick.major.size`, `ytick.minor.size`, `xtick.major.pad`, `ytick.major.pad`, `axes.labelpad`, `axes.titlepad`.
- **Font family** — respect the venue's mandate if there is one; otherwise leave the user's choice alone.

Present this as a single `plt.rcParams.update({...})` block plus any per-call adjustments (e.g. explicit `capthick=`).

**Never touch:** data values, colors, colormaps, linestyles, axis limits, tick locators that encode semantics (e.g. log scale), the subplot grid/layout the user chose, or the semantic meaning of any element.

## Phase 5 — Apply edits

Use `Edit` (not `Write`) to modify the user's script in place:

- Replace the `figsize=...` argument on the `plt.figure(...)` / `plt.subplots(...)` call.
- Insert (or replace, if one already exists) a single `plt.rcParams.update({...})` block near the top, after the matplotlib import.
- Walk the script and remove stale per-call `fontsize=`, `labelsize=`, `linewidth=`, `markersize=` kwargs that are now centrally controlled — otherwise the rcParams block will be silently overridden.
- For each `errorbar(...)` call, set `capsize=` and `capthick=` explicitly.
- Do not reorder code, do not rename variables, do not change anything semantic.

## Phase 6 — Verification render (AFTER edits)

**Hard rule: no success claim is allowed until the re-rendered image has been produced and read.**

1. If the baseline was saved to `before.png`, save the new render to `after.png` in the same directory. If the script's own `savefig` path is reused, keep a copy of the before render in `_beautify/before.png` so both exist.
2. Re-run the script:
   ```
   MPLBACKEND=Agg python <script_path>
   ```
3. `Read` the new PNG.
4. **Measure edge padding in pixels — do not rely on visual judgement.** Visual inspection of a rendered thumbnail misses 1–3 pixel clipping of rotated text, long twin-axis labels, and descenders. Run this check on every output PNG:
   ```python
   from PIL import Image
   import numpy as np
   im = np.array(Image.open(path).convert("L"))
   h, w = im.shape
   col = (im < 200).any(axis=0); row = (im < 200).any(axis=1)
   top   = int(np.where(row)[0].min())
   bot   = h - 1 - int(np.where(row)[0].max())
   left  = int(np.where(col)[0].min())
   right = w - 1 - int(np.where(col)[0].max())
   print(f"{path}: {w}x{h}px | pad top={top} bot={bot} left={left} right={right}")
   ```
   At dpi=300, **any side with <10 px of white border is clipped or about to clip** (rotated descenders, emoji, superscripts, `ℓ`, parens often extend farther than tight-bbox predicts). Treat top=0 as a hard failure even if the image "looks fine."
5. Walk through each item in the Phase 3 issue list and mark it **resolved**, **partial**, or **still present**, with a one-line justification tied to what you see in the new image.
6. Scan for regressions the edits could have introduced:
   - Clipping (title cut off, rotated twin-axis y-label overshooting the top, legend pushed outside axes by new figsize). The pixel-pad check above catches most of these deterministically.
   - Over-thickened data lines that swamp small markers.
   - New overlaps from smaller figure width.
   - Legend now larger than data region.
7. **Common failures and fixes:**
   - *top=0 or bot=0 px* — a rotated text artist extends beyond figure canvas. Fix: switch `layout="constrained"` → `fig.tight_layout(pad=0.5)`, and/or add `"savefig.pad_inches": 0.15` to rcParams. If the offender is a *long* twin-axis y-label (common with `ax.twinx()` + descriptive ylabel), the real fix is a taller figsize: relax the strict chart-type aspect and make the figure ~10–20% taller so the rotated label fits.
   - *Title feels oversized relative to panel height* — drop `axes.titlesize` to match or slightly below `axes.labelsize` (e.g. 7.5 when labels are 8) and reduce `axes.titlepad` to 1.5–2.0. For column-width figures the LaTeX caption does most of the labeling work; an on-figure title only needs to name the data, not lead the visual hierarchy.
   - *Legend dominates data region on small figsize* — add `ncol=2` per-call, shrink `legend.handlelength` to 0.8, tighten `legend.labelspacing` to 0.2 and `legend.borderpad` to 0.2. If still too large, move the legend below the plot with `loc="upper center", bbox_to_anchor=(0.5, -0.3)` and budget extra bottom margin.
8. If any Phase 3 issue is still present, or a regression was introduced, go back to Phase 4 with a targeted adjustment, edit, and re-render. Cap at 2–3 iterations before checking in with the user — do not loop silently.

## Phase 7 — Output

Summarise for the user:

- Venue spec values used: `column_width_in`, `textwidth_in` (if relevant), `body_pt`, font family.
- Computed `W_page` and the fraction that produced it.
- Table of key visual-system changes (figsize, fonts, linewidths, markersize, capsize/capthick, legend, ticks) — before vs after.
- The Phase 3 issue list with resolution status after Phase 6.
- Absolute paths to both `before.png` and `after.png`.

Then, per the project `CLAUDE.md`, commit the changes to the user's script with a senior-level message.

## What this skill will not do

- Will not alter data, colors, colormaps, or linestyles.
- Will not restructure the user's subplot grid or axis composition beyond the `figsize` rewrite.
- Will not harmonize against a separate reference figure (that is a different problem).
- Will not silently clamp fonts below venue-appropriate floors — it will flag and ask.

## Red flags — stop and reconsider

- You are about to edit code without having read a rendered PNG. **Stop.** Render first.
- You are about to report "done" without having read the post-edit PNG. **Stop.** Re-render and look.
- You are about to report "done" without having run the pixel-pad check from Phase 6. **Stop.** Eyeballing a thumbnail is not sufficient — rotated descenders and long twin-axis labels routinely clip by 1–5 px without looking clipped.
- Your Phase 3 issue list has zero items. **Stop.** Look again at the page-size preview.
- The venue lookup failed and you are inventing column widths or body font sizes. **Stop.** Ask the user.
- You are tempted to tweak colors or data to "make it look better". **Stop.** That is out of scope.
