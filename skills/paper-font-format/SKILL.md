---
name: paper-font-format
description: Use when a user wants to format matplotlib font sizes in a plotting script for inclusion in a scientific paper, given the paper's body font size, column width, and the fraction of column width the figure will occupy. Recomputes all font sizes from scratch based on the figure's final physical size on the page — does not scale the user's existing fontsize values.
---

# paper-font-format

You are formatting a matplotlib plotting script so that when its saved figure is embedded into a scientific paper at a specified width, **all text in the figure appears at the physically correct pt on the printed page**, with a hierarchy appropriate to how large the figure actually appears in the paper.

## Critical principle

**Do not scale the user's existing fontsize values.** Users often set secondary/tertiary font sizes by trial and error, and those values are frequently out of proportion. If you just multiply them by a scale factor you preserve (and visually amplify) the error. Instead, **derive every font size from scratch** from (a) the paper's body font size and (b) the figure's final physical width on the page. Then completely overwrite the user's old fontsize values.

`figsize` is the one thing you must **not** change — it is set by the user and belongs to the user.

## Inputs to gather

Do **not** immediately ask the user for column widths, body font sizes, or page formats — those are lookup work, not design decisions. Instead, start by asking for the submission target and derive the rest.

### Step A — ask for the venue first

Ask the user (as the very first interaction): **"What conference or journal are you submitting this figure to?"**

If the user gives a venue name (e.g. "NeurIPS 2025", "Nature Methods", "IEEE TVCG", "ICML", "CVPR", "ACM CHI"), proceed to Step B. If the user cannot name one, fall back to Step D (manual).

### Step B — look up the venue's current template specs

Use `WebSearch` / `WebFetch` to find the venue's **latest official author guidelines or LaTeX template** and extract:

- **paper size** (US Letter 8.5 × 11" vs. A4 210 × 297 mm)
- **column layout** (single-column, two-column)
- **column width** in inches or millimetres (look for values in the template's `\columnwidth`, `\textwidth`, or the guidelines' "figure width" instructions)
- **body font size** in pt (look for `\documentclass[Npt]` or explicit statements in the guidelines)

Prefer primary sources in this order:
1. The venue's own author-kit / style-file repository (e.g. `neurips.cc`, `openreview` for confs; journal's "for authors" page).
2. The venue's published LaTeX class / style file (`.cls` / `.sty`) — it contains the ground truth.
3. A recent accepted paper from the venue as a secondary sanity check (not primary — templates change between years).

When citing, include the URL so the user can verify.

### Step C — show the user what you found and ask for confirmation

Present a short summary like:

> Found for **NeurIPS 2025** (source: `https://neurips.cc/Conferences/2025/CallForPapers`):
> - Paper size: US Letter
> - Layout: single-column
> - Column width (`\textwidth`): **5.5"**
> - Body font: **10 pt**
>
> Using these unless you say otherwise.

If the user corrects a value, use the corrected value. If the user says "looks good", proceed.

### Step D — fallback when venue is unknown or unfetchable

If the user can't name a venue, or the lookup in Step B fails (no network, ambiguous results, new venue with no template yet), fall back to asking directly for:

- **column_width_in** (default 6.5" for single-column A4/Letter)
- **body_pt** (default 12)

and offer a short preset menu if helpful (Nature / Science / IEEE two-column / ACM / generic A4).

### Always-required inputs (regardless of venue)

Regardless of whether venue lookup succeeded:

- **figsize** `(w, h)` in inches — read from the target code (`plt.figure(figsize=...)` or `plt.subplots(figsize=...)`). If absent, matplotlib default is `(6.4, 4.8)`; ask the user to confirm or set it.
- **embed_ratio** — fraction of the column width that this particular figure will occupy (default **1.0**). E.g., `0.5` for a half-column, `2.0` for a two-column-spanning figure in a two-column layout.

## Step-by-step procedure

### 1. Compute scale factor

```
W_page = column_width_in * embed_ratio      # figure's final width on page, inches
s      = W_page / figsize[0]                # scale factor
```

A matplotlib fontsize of `X` pt will render at `X * s` pt on the printed page.
So to achieve a target page pt `T`, set the code pt to `T / s`.

### 2. Decide absolute target pt for each element

Base the decision on `W_page` (the figure's final physical width on the page), not on `figsize`, and not on the user's current values.

| Figure on-page width `W_page` | Label (axis label) | Tick / Legend / Annotation |
|---|---|---|
| ≤ 2.5" (very small subpanel) | body_pt − 1 | body_pt − 2 |
| 2.5"–3.5" (small)            | body_pt − 1 | body_pt − 2 |
| 3.5"–5"  (medium, single-col)| body_pt − 2 | body_pt − 3 |
| ≥ 5"     (large / two-col)   | body_pt − 2 | body_pt − 4 |

- **Title / suptitle** = body_pt (always; this is the "main title = paper body text" anchor).
- **Caption / figure text** (if any via `fig.text`) ≈ label pt.
- Suptitle and axes titles both get title pt; for subplots you may use title pt for each axes title and keep suptitle = title pt (unless user asks to differentiate).

Rationale: the smaller the figure appears on the page, the tighter the hierarchy must be, or tertiary text becomes unreadable. The larger the figure, the more visual headroom for a wider hierarchy.

### 3. Enforce floors and ordering

- **Readability floor**: no element may render below **6 pt** on the page. If `target_page_pt < 6`, raise it to 6 before computing the code pt.
- **Ordering invariant**: `title ≥ label ≥ tick` (in page pt). If your table lookup ever violates this (it shouldn't with the ranges above, but body_pt can be very small), clamp so this holds.

### 4. Compute code pt

For each element, `code_pt = target_page_pt / s`, rounded to the nearest **0.5 pt**.

### 5. Compute line/marker widths

Thin elements need the same reverse-scaling so they don't look hairline on the page.

| rcParam | Code value |
|---|---|
| `axes.linewidth` | `0.8 / s` |
| `xtick.major.width`, `ytick.major.width` | `0.8 / s` |
| `xtick.minor.width`, `ytick.minor.width` | `0.6 / s` |
| `xtick.major.size`, `ytick.major.size` | `3.5 / s` |
| `xtick.minor.size`, `ytick.minor.size` | `2.0 / s` |
| `lines.linewidth` | `1.25 / s` (only if user hasn't set explicitly for semantic reasons) |
| `lines.markersize` | `5.0 / s` (same caveat) |
| `patch.linewidth` | `0.8 / s` |
| `legend.frameon` | leave as user set; if unset leave default |

Round to 2 decimals.

### 6. Rewrite the code

Apply all font sizes via a single `plt.rcParams.update({...})` block placed right after the matplotlib import. Use these rcParams keys:

- `font.size` → body_pt (the "anchor"; affects any text that doesn't specify its own)
- `axes.titlesize` → title code pt
- `figure.titlesize` → title code pt (for suptitle)
- `axes.labelsize` → label code pt
- `xtick.labelsize`, `ytick.labelsize` → tick code pt
- `legend.fontsize` → legend/tick code pt
- `legend.title_fontsize` → label code pt

Then walk the rest of the script and **replace** every explicit `fontsize=<N>` / `size=<N>` argument on `set_title`, `set_xlabel`, `set_ylabel`, `text`, `annotate`, `legend`, `suptitle`, `colorbar.ax.set_ylabel`, colorbar tick labels etc. — overwriting the user's values with the correct absolute pt for that element category. Do not leave any old `fontsize=` values behind; either delete them (if the rcParam covers the element) or replace with the new value.

Do **not** touch:
- `figsize`
- data, colors, colormaps, linestyles, markers (semantic choices)
- axis limits, tick locators, labels' text content
- the order/type of plots

### 7. Output

Produce two things:

1. **The full rewritten script**, ready to run.
2. **A brief report** containing:
   - scale factor `s` and `W_page`
   - for each element: target page pt → code pt
   - any floors that kicked in (element X hit 6 pt floor)
   - a one-line sanity check: "title/label/tick on page = A/B/C pt, all ≥ 6 pt, order preserved"

## Worked example

User: figsize=(5, 3), body_pt=10, column_width_in=3.5, embed_ratio=1.0.

```
W_page = 3.5 * 1.0 = 3.5  → falls in "small" band
s      = 3.5 / 5  = 0.70
```

Target page pt: title=10, label=9, tick=8.
Floors: all ≥ 6 ✓. Order: 10 ≥ 9 ≥ 8 ✓.

Code pt: title=10/0.70≈14.5, label=9/0.70≈13.0, tick=8/0.70≈11.5.

Line widths: `axes.linewidth = 0.8/0.70 ≈ 1.14`, `xtick.major.width ≈ 1.14`, etc.

## Common mistakes to avoid

- Scaling the user's existing fontsize values (`new = old * k`) — never do this; always recompute from absolute target.
- Changing `figsize` — the user owns this.
- Using the same hierarchy (e.g., 12/10/8) regardless of figure size — compresses badly on small figures.
- Forgetting to also scale line/tick widths — large text with hairline axes looks broken.
- Leaving stale explicit `fontsize=` kwargs in the script that will override your `rcParams`.
