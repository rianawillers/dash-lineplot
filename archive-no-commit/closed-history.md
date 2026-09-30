# dash-lineplot: Closed Work History

This file holds the write-up for every item that has been closed (fixed,
verified, or determined no longer relevant) out of `suggestedwork.md`.
`suggestedwork.md` itself stays forward-looking only: when an item there
closes, move its full write-up here and delete it there, leaving at most
a one-line pointer if a later reader might otherwise go looking for it.

Organised by review pass, oldest first. Within a pass, roughly the order
the original `suggestedwork.md` had it.

---

## Pass 1 -- 2026-09-11, commit `3bc7304` (read-only review)

The first pass over the repository. Read-only: nothing was changed while
producing it. Findings from it close out across passes 2-4 below; this
entry exists only to record that the review happened and what its method
was.

**Verification status at the time**: read-verified only. No `pandas`,
`dash`, `plotly` or `scipy` was installed on the machine that produced it,
and no conda environment existed for the project, so nothing in it had a
reproduced traceback. Every finding stated the input that would reach the
defect, so the claims were checkable once an environment existed --
building that environment and adding regression tests was itself one of
the recommendations (see WP6 in the current `suggestedwork.md`).

---

## Pass 2 -- 2026-09-14 (callback fix)

### N1. The zoom Apply/Reset buttons were completely broken

`setupCallbacks` builds one callback per graph by iterating what it
believes is a flat list of graph ids. Commit `a37bd56` changed the source
of that iteration from `itertools.chain(allTabs, allGraphs)` (flat, but
targeting ids that mostly didn't exist -- see "callbacks registered
against components that never exist" below) to
`itertools.chain(graphList)`. `graphList` is a *list of lists*, one list
of graph ids per tab, and `itertools.chain()` given a single argument does
not flatten it -- it just walks the outer list. So `gr` was bound to each
tab's whole list of ids, and `theGraph = str(gr)` produced ids like
`"['graph-RelativePosition000', 'graph-RelativePosition001']"`, wired to
components that never existed. Every per-graph callback was affected: the
X/Y range Apply/Reset buttons, the range-box-follows-mouse-zoom sync, and
both click and selection readouts.

Fixed by flattening correctly: `itertools.chain(*graphList)`. Verified in
the browser: Reset returns to the full data range, and typing `1`/`5` and
clicking Apply zooms the axis to exactly `[1, 5]`.

This is also the closure of the original first-pass finding "callbacks
registered against components that never exist" (`setupCallbacks` had
iterated sheet names and pre-`Include`-filter tab lists rather than the
graph ids actually placed on the page, hidden only because
`suppress_callback_exceptions` was set) -- `a37bd56` had actually
introduced a *different* bug while appearing to fix that one, and this
pass is what closed it for real.

Lesson recorded at the time, still true: a mechanical, one-token change to
a `for` loop took down every interactive control on the page with no
exception raised anywhere. This is the standing argument for tests landing
before further structural refactors (see WP6 in the current
`suggestedwork.md`).

### Zoom-controls bug (the session's original trigger)

The user reported: "the zoom functionality provided by the four text boxes
on the right side... entered values and pressed 'apply' nothing happened."
This was N1 above.

### Data reader: two mutually exclusive branches -- closed

`readdatafile` used to decide the file type into three independent flags
(`matlab`, `comma`, extension checks) and test them in two separate `if`
statements rather than one dispatch. A MATLAB-style header containing a
comma set both flags, so both branches ran and the second silently
discarded the first result. Closed by a full rewrite to a single
scan-then-parse pass: count leading `%` lines, use the first as the
header, then one `pd.read_csv` call. No more flag pair.

### `dfData` could be returned unbound -- closed

Was: a space-separated file with no `%` header, no comma, and an
unrecognised extension fell through every branch and raised
`UnboundLocalError`. Closed by the same `readdatafile` rewrite -- see also
N3 below, which is the *next* shape this same underlying risk took after
the rewrite.

### `skiprows` could reach -1 -- closed

Was: counting leading `%` lines and then unconditionally subtracting one
to leave the last comment line as the header could reach -1 for a file
with no `%` line at all, which is not a valid `read_csv` argument. Closed
by the same rewrite: `skip_count` only increments on an actual `%` line,
never decremented.

### `np.isnan` on cells that may hold text -- closed

Six sites called `np.isnan` directly on a configuration cell (`Scale`,
`Offset`, `ToDisk`, `MarkerOpacity`, `Linewidth`, `Include`). A numeric
column containing one text cell becomes `object` dtype, and `np.isnan` on
a Python string raises `TypeError`, so a single typo took the whole page
down with an error naming nothing the user could act on. Closed by adding
`cellFloat`/`cellText`/`cellFlag` helpers (using `pd.isna`, which is total
over `None`/`NaN`/`NaT`/strings) and routing every read through them.

### Modernisation items closed this pass

- `class DashLinePlot():` -> `class DashLinePlot:`
- `import sys, os` -> one import per line
- f-string for the base64 image `src`
- Shadowed builtin `id` (`generateFeedbackBoxes`, `display_click_data`) ->
  renamed to `graphId` in both places; `display_click_data`'s indentation
  straightened to four spaces at the same time
- `math.isnan`/`np.isnan` mixed with the rest -> standardised on
  `pd.isna`; `import math` removed
- `(bolean)` typo in docstrings -> fixed everywhere

### Dead code closed this pass

- `visdcc`/hover-injection dead code (`JS_STR_template`, `jsString`,
  commented `render_content`) -- deleted outright
- `allTabUsedIdx` -- deleted outright
- Unused `reqStart`/`reqEnd` parameters on `makeGraphSet` -- removed; no
  caller passed them anyway
- `__version__ = '$Revision: 4633 $'` (an unexpanded SVN keyword) --
  attribute removed

### Stylesheet loaded twice -- closed (first time; see pass 4 for a
regression)

`external_stylesheets = ['assets/bWLwgP.css']` was passed to `dash.Dash`
while `assets_folder=resourcePath('assets')` already serves every file in
that folder automatically, so the stylesheet was linked twice. Closed by
dropping the `external_stylesheets=` keyword from the `dash.Dash(...)`
call. (Left a dead module-level variable behind, closed properly in pass
4 -- see N4.)

---

## Pass 3 -- 2026-09-14 (axis labels, value integrity, documentation sweep)

### N5. Axis labels were missing on every graph -- closed

`xaxis`/`yaxis` titles were built as plain strings --
`'xaxis':{'title': ctx['xlabel'], ...}` and `yAxisDict = {'title': yLabel,
...}`. Plotly.js 4 (bundled by the `dash>=4.4` this environment pins)
accepts a bare string for `title` without error -- `gd.layout.xaxis.title`
read back correctly -- but rendered it as nothing: the `<g
class="g-xtitle">` element existed in the DOM with empty text content.
Confirmed with `Plotly.relayout(gd, {'xaxis.title': {text: '...'}})` in
the browser console: the object form rendered immediately, the string
form never did.

Fixed by wrapping both in `{'text': ...}`. Verified in the browser: "Time
[s]" and "Distance [m]" (etc.) show on every graph, in both `compact` and
`comfortable` density.

### N6. Scale and Offset leaked into every value the reader read off -- closed

A `yValue` row's `Scale`/`Offset` (and a block's `xValue` `Scale`/`Offset`)
are meant to be a *display* convenience only, so traces of very different
magnitude -- the user's own example was microvolts and megavolts -- can
share one axis. They were not display-only: the hover tooltip, the Click
Data box, and the Rectangle Tool Selection Data box all read the value
straight back off the trace's plotted `x`/`y`, which *is* the scaled,
offset one. A line configured with `Scale=0.01` (the shipped
`dash-config.xlsx` has one, `Missile rol/100`) reported `0.225` on hover
where the recorded value was `22.5125`.

Fixed by giving every trace a `customdata` array carrying the true,
unscaled x (and for a numeric trace, the true y) alongside the plotted
one, and reading from it everywhere a value is displayed:

- Each trace's `hovertemplate` renders `customdata`, not the default
  `%{y}`, so the native Plotly hover tooltip shows the recorded value.
- `commonClickMessage` and `commonSelectMessage` (the `commonX` readouts)
  read each trace's value from `customdata` instead of its plotted `y`,
  and convert the clicked x / selection edges back to true x through
  `self.graphXAxis[grID]` = `(xscale, xoffset)` recorded per graph -- a
  selection box's edges are a plot position with no recorded sample
  behind them, so there is nothing else to convert them from.
- `display_click_data` (the non-`commonX` click box) prefers the clicked
  point's own `customdata` over its plotted `x`/`y`.
- `display_selected_data` (the non-`commonX` rectangle-select box)
  previously reported the selection box's raw top-left/bottom-right
  corners -- not just stale but ambiguous, since two lines on one graph
  can carry different `Scale`/`Offset` and a box corner has no single true
  value to convert to. It now delegates to `commonSelectMessage`, which
  already solves this correctly by reporting each line's own true y
  extent inside the selected x window. This was a visible behaviour
  change, documented in `docs/userguide.md`'s "Rectangle Tool Selection
  Data" section at the time.

Verified in the browser on `Missile rol/100` (`Scale=0.01`): hover
tooltip, Click Data, and Rectangle Tool Selection Data all reported
`22.5125` (or the correct value at other points/windows), never the
scaled `0.225`, across both a plain graph and a `commonX`-linked pair.

### Later request: "keep the y-value, remove the x-value" from hover

The user asked to drop the `x=...` line from the hover tooltip, since the
x position is already visible on the axis below via the vertical hover
line. Both hovertemplates (numeric and enumeration traces) were changed to
show only `name=value`. `docs/userguide.md`'s Hover section updated to
match. Verified in the browser: hover now shows e.g. `Distance=2229.1898`
only.

### Documentation sweep (repository-wide)

Requested by the user directly: "update all documentation ... with
current status." Covered every `.md`, `.tex` and the module docstring,
plus `environment.yml`:

- **`environment.yml`**: dropped `scipy`, unused since the MATLAB reader
  was removed.
- **`README.md`**: dropped the MATLAB bullet from "What it does"; dropped
  the dead range-slider link; dropped `scipy` from the dependency/license
  lines; fixed "To use as a module", which told a reader to import a
  `DashPlotWindow` class that no longer exists.
- **`dash-lineplot.py` module docstring**: the same `DashPlotWindow`
  mistake, `scipy` mention, and dead range-slider/Plotly-subplots links,
  fixed the same way. Rewrote the stale comment block above
  `setupCallbacks` that described a removed `visdcc`/subplot hover
  mechanism attached to code that no longer did that -- current hover
  sync is `assets/graphsync.js`.
- **`docs/userguide.md`**: removed the `.mat` row and the "scipy needed
  for Matlab" requirement; replaced a stale "Matlab reader carried
  forward, unverified" TODO with an accurate removal note; added a "known
  limitation, not the intended design" callout for the plain-CSV crash
  (see N3 below, closed in pass 4); added a note under `Scale`/`Offset`
  stating the N6 guarantee explicitly; rewrote the "Rectangle Tool
  Selection Data" section to match N6's behaviour change.
- **`doc/*.tex`** (`intro.tex`, `func.tex`, `system.tex`, `user.tex`,
  `lic.tex`): added an explicit "this is historical, see
  `docs/userguide.md`" notice to the Introduction and every affected
  chapter. Fixed the plain-text factual errors that didn't depend on
  regenerating screenshots: the MATLAB bullet in `func.tex`, the licence
  and dependency lists in `system.tex`, the PySide/Qt line in `lic.tex`'s
  LGPL section, and the "subplots" claim in `user.tex`'s Click Data
  description. **Not done, and still not done**: rewriting the
  screenshots-and-figures narrative itself -- see the note under "`doc/`
  LaTeX guide" further down this file.

### MATLAB (`.mat`) support removed but undocumented -- closed

The `readdatafile` rewrite (pass 2) deleted the `'mat' in extension`
branch and the `from scipy.io import loadmat` import, reasonably, since
nothing in this repository's own data or configs used it. But several
places still told a reader `.mat` was supported. Closed by the
documentation sweep above: every site corrected to say plainly that
`.mat` is not supported, rather than either restoring the reader or
leaving the docs wrong. A `.mat` file named in a configuration still does
not raise a clear error (falls to `readdatafile`, which tries to read it
as text) -- if MATLAB support is ever needed again, it must be
re-implemented, not re-enabled; the reader is gone, not disabled.

---

## Pass 4 -- 2026-09-15 (colleague's merge, dead code, hardening, legend, deletions)

This pass followed a colleague's own commit (`c9aa083`), merged without
conflict. It fixed the `readdatafile` no-`%`-header crash (N3 below) among
other things, but also reintroduced two regressions this pass found and
fixed again (N4, N7).

### N3. `readdatafile` required a `%`-prefixed header line -- closed

The pass-2 rewrite of `readdatafile` scanned leading lines, kept the first
one starting with `%` as the header, and raised `AttributeError` if none
was found -- a plain CSV with an ordinary top-of-file header (documented
as supported) crashed. Every shipped data file happened to carry a `%`
header, so this went unnoticed until the user's colleague added test
fixtures without one.

Closed by the colleague's commit: when no `%` line is found, falls back to
`pd.read_csv(..., header=0)` with the same multi-separator `sep` regex.
Verified this pass against all three fixture shapes now shipped in
`data/`: `sensor-tel-test1.txt` (one `%` header), `sensor-tel-test2.txt`
(no `%` header at all), `sensor-tel-test3.txt` (four repeated `%` header
lines) -- all load and plot correctly via `dash-config-sim.xlsx`.

### N7. `graphs/` output directory was never actually created -- closed

The colleague's commit changed `os.mkdir(grDir)` to `Path(grDir).mkdir`
(missing its call parentheses) while modernising to `pathlib`. This
evaluates the bound method object and discards it, so the directory is
never created. Since `ToDisk` defaults to `True`, the very first graph
built then crashed with `FileNotFoundError`, taking down the whole server
before it served a page -- masked on the development machine because a
`graphs/` directory already existed from earlier runs. Reproduced by
removing that directory and confirming the app died immediately on a
fresh checkout; fixed by adding the missing `()`. Verified from `/tmp`
with an absolute config path, and from a fresh directory with no
`graphs/`: the app starts cleanly and populates `graphs/` as intended,
from any working directory.

### N4. Dead `external_stylesheets` module-level variable -- closed (for real this time)

Closing the pass-2 stylesheet-double-load fix left the variable itself,
`external_stylesheets = [str(resourcePath('assets/bWLwgP.css'))]`, with no
reader. The colleague's commit then *reintroduced* the double-load bug by
adding `external_stylesheets=external_stylesheets` back to the
`dash.Dash(...)` call, alongside `assets_folder`. This pass removed the
kwarg again (verified via server log: `bWLwgP.css` requested once per page
load, not twice) and deleted the now-genuinely-dead variable and its
stale comment.

### N8. Legend misaligned stacked graphs' x axes -- closed

User-reported, with a screenshot: the right edges of several stacked
graphs on one tab didn't line up at the same x (time) value. Root cause:
Plotly's legend defaults to a column outside the plot, on the right, sized
to fit its longest entry. Since that width varies graph to graph, graphs
with different legend text ended up with different plot-area widths, so
their x axes -- the same time values -- didn't align at the right edge.

Fixed by anchoring the legend inside the top-right corner of the plot
area instead (`x:1, y:1, xanchor:'right', yanchor:'top'`, with a
translucent background so it doesn't obscure data), so every graph's plot
area is exactly the margin-defined width regardless of legend length.
Verified on the `gimbal` tab specifically (the same two-graph stack from
the user's screenshot): right edges now align pixel-for-pixel.

### Logo path relative, bypassed `resourcePath` -- closed

Was: `open('icons/logoSet2long.png', 'rb')`, relative to the working
directory rather than routed through `resourcePath`, re-read and
re-encoded once per tab. Closed by the colleague's commit: now
`base64.b64encode(open(resourcePath('icons/logoSet2long.png'), 'rb').read())`,
computed once at module import. `resourcePath`'s own fallback was fixed in
the same commit, from `Path(".").resolve()` (working-directory-relative,
the actual root cause) to `Path(__file__).resolve().parent` (correct
regardless of invocation directory) -- verified this pass by running the
script from `/tmp` with an absolute config path. (The file handle is still
not closed via `with`, but that's a one-off at import time, not worth
tracking separately.)

### Missing or misspelled configuration names -- closed (hardening pass)

Was the single largest usability return identified in pass 1: a
misspelled column name or a missing `Datafile`/`yLabel` row surfaced as a
bare pandas `KeyError` or crashed with `AttributeError`, naming nothing
the user could act on. Closed at the user's explicit request to harden the
code against bogus or missing config data. `makeGraphSet` now checks,
before touching `self.datafiles` or a `DataFrame`'s columns:

- a `Datafile` that is `None` or names nothing that was loaded,
- an `xValue`/`yValue` naming a column that doesn't exist in the resolved
  file,
- a `Title` with no `yLabel` row under it.

Each raises a `ValueError` naming the sheet, the offending value, and (for
a column name) every column the file actually has. `readConfigTables`'s
JSON branch similarly checks for a missing top-level `header` or `sheets`
key before indexing into either. Verified by deliberately breaking a copy
of `dash-config.xlsx` three ways (bad `xValue`, bad `Datafile`, missing
`yLabel`) and confirming each produces the intended message, e.g.:

```text
ValueError: Sheet 'graph-RelativePosition': xValue 'CurrentSimTime_TYPO'
is not a column of data/tp05j2a.rgeo. Columns available: CurrentSimTime,
Rel-distance, Rel-speed, ...
```

Not covered, and still worth doing if this area is revisited: a `.loc`
lookup against a *duplicate* index label (two `yLabel` rows under one
`Title`) returns a `Series` rather than a scalar and would behave oddly
rather than raising a clear error; low-likelihood, not exercised.

### Dead code closed this pass

Found by scanning the whole file with an AST pass over every function
definition and every import, cross-checked against actual references, at
the user's explicit request to remove "historic carry over code that has
no further purpose":

- `import os` -- completely unused; every file operation goes through
  `pathlib.Path`.
- A commented-out, never-implemented `nearestSample_sorted` sketch.
- `gridColour = 'lightgrey'` -- assigned, never read.
- `allTabs`/`allGraphs`/`tabIndex` bookkeeping in `prepareGraphs` --
  `allGraphs` was rebuilt every run via its own inner loop but never read
  anywhere; `allTabs` no longer needed to be a module `global` since
  nothing outside `prepareGraphs` read it; `tabIndex` was incremented and
  never read at all. The loop was simplified back to what it actually
  needs (it is now local `allTabs = dfPlotterConfig['Graph'].unique()`,
  read only inside `prepareGraphs`).
- The module docstring's ~90-line 2019 Dash-tutorial transcript (bullet
  notes copied from `dash.plot.ly/getting-started`, plus a full
  illustrative `Tabs`/`Div` code block) -- no project-specific content.
  Everything else in the docstring (file types, requirements, "how to use
  as a module") was kept.
- The slider callbacks (`process_xSlider_data`, `reset_xSlider` and their
  six component ids) -- verified still gone; the colleague's merge had
  deleted that block outright rather than leaving it commented, which an
  earlier pass had not yet confirmed.
- Local imports (`import plotly.offline as offline`, `import base64`)
  were already moved to module level in an earlier pass; `from scipy.io
  import loadmat` is gone along with the MATLAB reader. The only
  remaining local import in the file is `import argparse` inside
  `if __name__ == "__main__":`, which is normal practice, not a defect.

Also closed by the same code as a side effect: `os.path` vs
`pathlib.Path` inconsistency. `os.mkdir(grDir)` became `Path(grDir).mkdir()`
(N7 above) and the dead `import os` was removed, so the file now uses
`pathlib` exclusively -- there is no second idiom left to reconcile.
`resourcePath`'s own `try: sys._MEIPASS / except Exception` structure is
unchanged and could still become `getattr(sys, '_MEIPASS', None)`, but
that is a style nit, not the bug originally flagged.

### Deletions (user-approved, one item reviewed at a time)

At the user's explicit direction, following a review-then-approve
process against a deletion plan: deployment moved from a packaged desktop
build to a conda environment run directly by Python-savvy users, so the
tooling for the old deployment mode was removed:

- `pyInstaller/` (122 MB, 3012 tracked files) -- vendored copies of
  `dash`, `plotly`, `visdcc` and Qt runtime pieces, built for CPython 3.7.
- `dash-lineplot.spec`, `runPyInstaller.bat` -- the PyInstaller spec (hard
  coded `pathex=['C:\\Temp']`, bundled PySide2/PyQt5 hidden imports) and
  its build script.
- `startPlotTool.bat` -- launcher for a packaged `dash-lineplot.exe` that
  does not exist in this repository.
- `pythonSetup/` (`condaEnvironmentSetup.md` + a screenshot) -- accurate
  but fully redundant with `docs/userguide.md`'s own Installation section
  (which additionally covers running without `conda init`). Its one
  non-redundant piece, the `conda env export --no-builds --from-history`
  guidance, was folded into `docs/userguide.md` before deletion.
  `README.md`'s link to it now points at `docs/userguide.md` instead.
- `exmple-dash-config.xlsx` -- an upstream example whose `Datafile`
  entries pointed outside this repository and could never be run here.

`README.md` was updated at each point to drop the now-dead links and
mentions. Verified after all deletions: all five shipped configs
(`dash-config.xlsx`, `dash-config-sim.xlsx`, `dash-config.json`,
`commonx-example.json`, `dash-3dof.xlsx`) still start cleanly.

**`doc/*.tex` and `doc/pic/` (the LaTeX guide) were explicitly excluded
from this round of deletions -- the user has said they will remove that
tree themselves.** It still carries the "historical, see
`docs/userguide.md`" notices added in pass 3. Nothing further is expected
from future sessions regarding this tree; if it is ever removed, update
`archive-no-commit/handoff.md`'s file inventory table to match, since that
is the only place left that still describes it.

### `git push`

Pushed to `origin/feature/modernise-and-json` (not `master`, per the
standing constraint) after the fixes-and-hardening commit and the
deletions commit.

---

## Superseded findings (later findings replaced these; kept only as a pointer)

- **"1.7: callbacks registered against components that never exist"**
  (pass 1's original phrasing, citing `allTabs`/`allGraphs`) -- superseded
  by N1 (pass 2), which found and fixed the actual current-code form of
  this defect after an intervening commit changed its shape.
- **"1.2: `dfData` can be unbound on return"** (pass 1) -- superseded by
  N3 (closed pass 4), the next shape the same underlying risk (an
  unhandled input to `readdatafile`) took after the pass-2 rewrite.
