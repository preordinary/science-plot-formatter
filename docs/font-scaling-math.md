# Font scaling math

Human-readable reference for the math used by both skills. Skills themselves encode this — this doc is for debugging, onboarding, and decision-making.

## The fundamental relation

A matplotlib figure saved at `figsize = (w, h)` inches and then embedded in a paper at on-page width `W_page` is scaled by:

```
s = W_page / w
```

A text element declared at `code_pt` pt in matplotlib renders on the printed page at:

```
page_pt = code_pt * s
```

Therefore, to hit a target `page_pt` on the page, the matplotlib code must set:

```
code_pt = page_pt / s
```

The same applies to line and marker widths — they are drawn in points in matplotlib, and likewise scale.

## Target page pt by element (paper-font-format)

Anchor to the paper's body font size. The title matches the paper's body text so the figure reads like part of the page.

| Element | Target page pt |
|---|---|
| Title / suptitle | body_pt |
| Caption (`fig.text`) | label_pt (see below) |
| Axis label | depends on `W_page` (see table) |
| Tick label | depends on `W_page` |
| Legend text | = tick label pt |
| Annotation | = tick label pt |

### Table: hierarchy by on-page figure width

| `W_page` | Axis label | Tick / Legend / Annot |
|---|---|---|
| ≤ 2.5" | body_pt − 1 | body_pt − 2 |
| 2.5"–3.5" | body_pt − 1 | body_pt − 2 |
| 3.5"–5" | body_pt − 2 | body_pt − 3 |
| ≥ 5" | body_pt − 2 | body_pt − 4 |

Intuition:

- At small physical size, the figure has no room for a wide text hierarchy. Compress the gap between primary and tertiary text or the tertiary will fall off the readability cliff.
- At large physical size, there's visual room for a more classical typographic hierarchy (title > label > tick spread out).

### Readability floor

Any rendered page pt below **6** is unreadable in print. If the target falls below 6, raise it to 6.

### Ordering invariant

After all lookups and floors: require `title ≥ label ≥ tick`. If `body_pt` is very small (e.g. 7 pt in Nature), the subtractions above can make label or tick zero or negative — the floor handles this but also reorders: clamp upward to preserve the chain.

## Paper format presets (reference only — not the lookup table)

⚠️ **Do not treat this table as authoritative.** Both skills are designed to ask the user for the target venue and then use `WebSearch` / `WebFetch` to retrieve the venue's **current** author guidelines / LaTeX class file. Templates change between years and the values below are a rough sanity check only.

| Format | Column width | Body pt |
|---|---|---|
| A4 single-column | 6.5" (~165 mm) | 10–12 |
| A4 two-column (IEEE/ACM historical) | 3.35"–3.5" (~85 mm) | 9–10 |
| Nature single-column (historical) | 3.5" (89 mm) | 7 |
| Nature two-column (historical) | 7.2" (183 mm) | 7 |
| Science single-column (historical) | 2.28" (58 mm) | 9 |
| Letter single-column | 6.5" | 10–12 |

When only a venue name is available but a live lookup is impossible (offline, venue not found), fall back to this table and **tell the user** which row you used and that it may be out of date.

## Line and marker width scaling

Matplotlib's built-in defaults are roughly:

| rcParam | Default |
|---|---|
| `axes.linewidth` | 0.8 |
| `xtick.major.width` | 0.8 |
| `xtick.minor.width` | 0.6 |
| `xtick.major.size` | 3.5 |
| `xtick.minor.size` | 2.0 |
| `lines.linewidth` | 1.5 |
| `lines.markersize` | 6.0 |
| `patch.linewidth` | 1.0 |

When the figure is shrunk on the page (`s < 1`), these render as hairline — divide by `s` to preserve their page-pt appearance. When the figure is enlarged on the page (`s > 1`), they would look bulky — the same `1/s` correction shrinks the code value so it renders normally.

## Why `figsize` is sacred in skill 1 but fluid in skill 2

- **Skill 1 (paper-font-format)**: the user picked `figsize` for a reason (data aspect, subplot grid, aspect of a particular chart). Changing it would alter what the user is communicating. We only fix the typography.
- **Skill 2 (match-reference-style)**: the target is being composed with a reference; its `figsize` must be redesigned to fit the composed layout. Font changes alone cannot make two figures look coordinated if their on-page dimensions don't cooperate.

## Aspect ratios used by skill 2

Natural `height / width` ratios for matching chart types to aspects:

| Chart type | Natural aspect |
|---|---|
| heatmap / imshow / confusion matrix / spatial map | 1.00 |
| line / scatter / bar / timeseries | 0.62 |
| distribution (hist / kde / violin / box) | 0.75 |
| unknown | 0.62 |

Skill 2 coordinates with the reference height within ±20 % of the natural aspect, so two figures share a row gracefully without crushing either.
