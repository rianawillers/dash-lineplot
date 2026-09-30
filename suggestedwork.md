---
title: "dash-lineplot: Suggested Work"
date: "2026-09-15"
pdf-engine: lualatex
style: |
  .markdown-preview.markdown-preview {
    font-size: 11pt;
    line-height: 1.5;
  }
puppeteer:
  displayHeaderFooter: true
  format: "A4"
  margin:
    top: "1.5cm"
    bottom: "1.5cm"
    left: "1cm"
    right: "1cm"
  headerTemplate: |
    <div style="font-family: Arial, sans-serif; font-size: 9pt; width: 100%; padding: 0 1cm; display: flex; justify-content: space-between; color: #000;">
      <span class="title"></span>
      <span class="date"></span>
    </div>
  footerTemplate: |
    <div style="font-family: Arial, sans-serif; font-size: 9pt; width: 100%; text-align: center; color: #000;">
      <span class="pageNumber"></span>/<span class="totalPages"></span>
    </div>
---

# dash-lineplot: Suggested Work

Open items only: defects, dead constructs, structural and performance
issues, and a recommended order of work. This file is kept
**forward-looking**. When an item here is closed (fixed, verified, or
found no longer relevant), move its write-up to
[`archive-no-commit/closed-history.md`](closed-history.md) and delete it
from here -- don't mark it closed in place. That file also carries the
narrative of every past review pass, if you need the history behind why
something is the way it is.

Markdown flavour for this file: Native/KaTeX, with PDF-export front matter.

**Standing decision:** the xlsx configuration path is the one in daily
use and stays the primary, actively maintained format. JSON config
support is kept for the cases it already serves, but is not where further
investment should go -- no new JSON-only features, and any shared refactor
(`configio.py`, validation, cell helpers) should be judged by whether it
helps the xlsx path, not by JSON parity.

**Verification status:** findings are checked against the running
application (conda env `dashplot`, `dash-lineplot.py -f dash-config.xlsx`
and the other shipped configs), not just read from the source, unless a
finding says otherwise.

## Priority summary

| # | Item | Kind | Severity |
|---|---|---|---|
| 1 | Module-level `global` state instead of instance state | Structure | High |
| 2 | Index strings parsed by `split('#')`/`split('-')`; `Variable` names compared by substring | Structure | Medium |
| 3 | Canonical-column/sheet-filter logic duplicated (script vs. `tools/xlsx_config_to_json.py`) | Duplication | Medium |
| 4 | No tests, no `pyproject.toml`, no linter config | Hygiene | High |
| 5 | Config walk is row-by-row `.loc` plus `concat` | Performance | Medium |
| 6 | Full trace data duplicated into `self.graphTraces` | Performance | Medium |
| 7 | Per-click work is linear, uncached | Performance | Medium |
| 8 | HTML copies of every graph written by default | Behaviour | Medium |
| 9 | Config workbook opened twice | Performance | Low |
| 10 | File-type dispatch is still substring-based | Defect | Low |
| 11 | Header `%` stripping lives in one reader, not normalised centrally | Inconsistency | Low |
| 12 | `suppress_callback_exceptions` is broader than it needs to be | Robustness | Low |
| 13 | Modern-Python remainder (see list) | Modernisation | Low |

---

## 1. Structural problems

### 1.1 Module-level `global` state

Six `global` statements still carry per-instance state into module scope
(down from eleven in the original review -- the other five were
`allTabs`, `allGraphs`, `sliderMinValues`, `sliderMaxValues` and
`tabIndex`, all deleted as dead code rather than fixed structurally, see
`closed-history.md`).

| Global | Set in | Read in |
|---|---|---|
| `dfPlotterHeader` | `loadConfig:1417-1418` | `makeGraphSet:852-853`, `loadConfig:1421,1427-1428` |
| `dfPlotterConfig` | `loadConfig:1436-1437,1478` | `prepareGraphs:1300,1306`, `loadData:1553-1555` |
| `pageDensity` | `loadConfig:1425-1426,1430` | `makeGraphSet:1180,1204`, `makePage:1377` |
| `divSets` | `prepareGraphs:1285,1291,1316` | `makePage:1344`, `render_content:1681` |
| `graphTabs` | `prepareGraphs:1286,1294,1318` | `makePage:1346` |
| `graphList` | `prepareGraphs:1287,1297,1317` | `setupCallbacks:1686` |
| `dashApp` | `runDash:1627-1628` | throughout `runDash`, and `runPlotter:1989` |

Consequences, in order of how much they cost:

- Two `DashLinePlot` instances in one process overwrite each other's
  configuration and page. The module docstring advertises exactly that
  use ("To use as a module in another application"), so the documented
  API is not safe to use twice.
- `makeGraphSet` reads `dfPlotterHeader` and `pageDensity` out of module
  scope while taking `dft` as an argument, so its inputs are half explicit
  and half ambient. Nothing about the signature says what it needs.
- A callback closure reading `divSets` (`render_content:1681`) depends on
  `prepareGraphs` having run first, with no way to assert it.

Fix: make all of them instance attributes -- `self.divSets`, `self.config`
(`dfPlotterConfig`), `self.header` (`dfPlotterHeader`), `self.density`
(`pageDensity`), `self.graphTabs`, `self.graphList`, `self.dashApp`. The
callback definitions already live in a method (`setupCallbacks`) and close
over `self` naturally. This is mechanical, touches many lines, and is the
single largest structural improvement available. Do it in its own commit,
no behaviour change alongside it, and only after tests exist (item 4)
since nothing currently exercises `setupCallbacks`/`graphList` outside a
human clicking around in a browser -- see `closed-history.md`'s N1 entry
for what a silent regression in exactly this code already cost once.

```python
# Sketch: wrap the related module-level state in the instance itself,
# rather than a separate context object -- DashLinePlot already is that
# object, it just doesn't use itself consistently yet.
class DashLinePlot:
    def __init__(self):
        ...
        self.header = pd.DataFrame()
        self.config = pd.DataFrame()
        self.density = 'compact'
        self.divSets = []
        self.graphTabs = []
        self.graphList = []
        self.dashApp = None
```

### 1.2 Index strings parsed by splitting

The configuration index encodes set and trace numbers into the row label,
`yValue#003-007`, and the graph code takes it apart with string surgery:

```python
setStr = str(index).split('#')[1].split('-')[0]     # dash-lineplot.py:929
setStr = str(index).split('#')[1]                   # dash-lineplot.py:1064
```

Membership is then tested by substring rather than equality:
`'Datafile' in var_name`, `'Title' in var_name`, `'yLabel' in var_name`,
`'yValue' in var_name` (`dash-lineplot.py:1457,1464,1467,1470`) -- so a
`Variable` named `SubTitle` or `DatafileB` would be taken for a `Title` or
a `Datafile` row. The tab label is derived as `graphTab.split('-')[1]`
(`dash-lineplot.py:1318`), which truncates any sheet named
`graph-my-signals` to `my`.

Fix: carry set and trace numbers as their own integer columns --
`SetNum`, `TraceNum` -- alongside the existing `Graph` and `ShtNum`
columns, and select with `dft[dft['SetNum'] == n]` instead of parsing a
label. Compare `Variable` names with `==`. Use
`graphTab.split('-', 1)[1]` or `graphTab.removeprefix('graph-')` for the
tab label. Do this against the xlsx path's own test fixtures first, per
the standing decision -- that is the path every real configuration in
this project uses.

### 1.3 Duplicated configuration logic

`readConfigTables` (`dash-lineplot.py:495`) and `workbookToDict` in
`tools/xlsx_config_to_json.py` each implement the `'graph' in sheetname`
sheet filter and the openpyxl-for-sheet-order trick, and
`CONFIG_COLUMNS`/`onCanonicalColumns` exist only in the former while the
latter has its own `cellValue`/`isEmpty` pair covering similar ground to
`cellFloat`/`cellText`/`cellFlag`.

Fix: extract a small `configio.py` beside the script holding
`CONFIG_COLUMNS`, the sheet filter, the workbook reader and the cell
helpers, and import it from both. That also makes the config layer
testable without importing Dash. Note while doing so that the sheet
filter is itself a substring test: `'graph' in sn` matches a sheet named
`paragraphs`. `sn.startswith('graph-')` is what is meant, and should be
defined once. Per the standing decision, only do this if it serves the
xlsx path -- do not extend it chasing JSON/xlsx parity for its own sake.

## 2. Performance

Ordered by what a large data set actually costs. No data set large enough
to make any of these visible has been run against the current code, so
severity is "worth doing, not urgent" throughout -- measure with the
largest run available before investing in any of them.

### 2.1 The configuration walk

`loadConfig` iterates each sheet row by row and writes back through `.loc`
on every iteration, then grows the master frame with `pd.concat` inside
the sheet loop (`dash-lineplot.py:1478`). Both are standard pandas
anti-patterns: each `.loc` assignment on a mixed-dtype frame can copy, and
each `concat` reallocates everything accumulated so far.

Fix: build the index labels as a list comprehension over the rows, assign
the column once, and collect the per-sheet frames in a list for a single
`pd.concat(frames)` after the loop. This is also where the `SetNum`/
`TraceNum` columns of 1.2 naturally get built.

### 2.2 Trace data duplicated for the click/selection readout

```python
self.graphTraces[grID] = [                                # dash-lineplot.py:1218
    (trace.get('name', ''), trace['x'], trace.get('customdata'),
     trace.get('text'))
    for trace in thisGraphData]
```

Every graph's full x and customdata (which itself carries both true x and
true y per point, see `closed-history.md`'s N6 entry) is retained for the
lifetime of the process so a `commonX` click or a rectangle selection can
be answered. For a large trace this is a second copy of the data, held
per graph rather than per data file.

Fix: store what identifies the trace -- data reference, x column, y
column, scale and offset -- and read values back from `self.datafiles` on
demand. The frames are already in memory.

### 2.3 Per-click work is linear and uncached

`commonClickMessage` (`dash-lineplot.py:595`) calls `nearestSample` for
every trace of every graph in a `commonX` group on every click, and
`nearestSample` (`dash-lineplot.py:387`) builds a fresh `np.asarray` over
the whole x column each time.

Fix: cache the `numpy` x array per trace at build time. For a monotonic x
-- which a time column is -- `np.searchsorted` answers in logarithmic
rather than linear time, and monotonicity can be checked once at load.
`commonSelectMessage` has the same per-call `np.asarray` cost.

### 2.4 HTML copies written on every run by default

`toDisk` defaults to `True` (`dash-lineplot.py:862`), so every graph of
every included tab is written to `./graphs/` as a standalone HTML file on
every start-up, whether or not anyone asked. Each file embeds its own copy
of the data and of the Plotly bundle.

Note also that `.gitignore` describes the directory as "Generated by
graphToDisk when a sheet sets GraphToDisk" (`.gitignore:9`), but the flag
the code reads is `ToDisk`. One of the two names is wrong.

Fix: default `toDisk` to `False` -- exporting is an explicit request, not
a side effect of viewing -- and reconcile the flag name between the code,
the `.gitignore` comment and `docs/userguide.md`.

### 2.5 The configuration workbook is opened twice

`readConfigTables` builds a `pd.ExcelFile` and then calls
`oxl.load_workbook(configfile)` (`dash-lineplot.py:538`) for the sheet
order, parsing the file twice. `pd.ExcelFile` already holds the openpyxl
workbook as its `.book`, so the order is available without a second read.
The same duplication exists in `tools/xlsx_config_to_json.py`.

## 3. Small, independent items

### 3.1 File-type dispatch is still substring-based

```python
extension = Path(datapath).suffix.lower()    # dash-lineplot.py:1582 (case-folding now done)
if 'xls' in extension: ...
elif 'json' in extension: ...
```

Case-sensitivity is fixed (`.suffix.lower()`). The substring half is not:
an extension containing `xls` or `json` as a substring of something else
would still misdispatch, though in practice this is low-risk since the
set of extensions reaching this code is small and controlled by the
config. Fold into whichever change next touches this block rather than
doing it alone.

### 3.2 Header `%` stripping lives in one reader only

The leading-`%` strip sits inside `readdatafile`, which is now the only
text-format reader (the old multi-branch dispatch that made this
inconsistent across formats is gone). Mostly moot as a defect, but still
not normalised centrally in `loadData` the way a reader-agnostic column
clean-up would be.

### 3.3 `suppress_callback_exceptions` is broader than it needs to be

Set unconditionally in `runDash` (`dash-lineplot.py:1641`), with a `#
todo` comment already in the code next to it. Now that callback
registration is driven only by `graphList` (the graphs actually on the
page), the only dynamic content that still needs suppression is the
tab-switch `children` output (`render_content`). Scoping suppression to
that one callback, rather than the whole app, would surface the next id
mismatch as a startup error instead of a silent no-op -- exactly the
failure mode `closed-history.md`'s N1 entry describes.

### 3.4 Modern-Python remainder

- `dash.callback_context` is still used at three sites (`apply_ranges`,
  `display_common_click_data`, `display_common_selected_data`) rather
  than `dash.ctx`/`ctx.triggered_id`.
- The four-element magic-index click history
  (`self.clickedData[graphId][3][0]` and siblings, in
  `display_click_data`) is unchanged; `commonClickMessage` already solves
  the same problem with a plain two-element list and reads far better --
  worth folding `display_click_data` onto the same shape rather than
  maintaining both.
- Type hints on the module-level helpers: still none. `cellFloat`,
  `cellText`, `cellFlag`, `splitDataRef`, `readJsonData`, `traceYExtent`,
  `nearestSample`, `isEnumSeries`, `parseCategories`, `enumCategories`,
  `isJsonConfig` are all small, pure functions -- exactly where a type
  hint pays for itself immediately.
- `print()` for error reporting: still used at three sites (a missing
  data file, an unrecognised `Density` value). Consider the `logging`
  module, or at minimum `file=sys.stderr`, so a caller embedding the
  plotter as a module can control it.
- Naming is camelCase throughout, against PEP 8 but consistent and
  deliberate -- leave it. Consistency with the existing file beats
  conformance here, and a rename would obscure every future diff.

## 4. Repository hygiene

No test of any kind, no `pyproject.toml`, no `requirements.txt`, no
linter or formatter configuration. `environment.yml` is the only
dependency declaration, and it is conda-only.

The absence of tests is what makes every structural item above riskier
than it needs to be. Fix, in the order that pays off soonest:

1. A `pyproject.toml` with `[tool.ruff]` configured to the file's actual
   style. `ruff` would have caught most of the dead-code items closed in
   `closed-history.md`'s pass 4 automatically, and finds the
   unbound-variable class of defect that N3 (also closed) once was.
2. `pytest` tests for the pure helpers, which need neither Dash nor a
   browser: `splitDataRef`, `readJsonData` on all three shapes and all
   three error paths, `parseCategories`, `enumCategories` (including the
   append-unknown-states rule), `isEnumSeries`, `selectionBounds` (box and
   lasso), `nearestSample`, `traceYExtent`, `resolveSetContexts` (a
   multi-block sheet), and `readConfigTables` on a workbook and its
   converted JSON -- the last of which also regression-tests that the two
   formats agree.
3. Round-trip tests for `readdatafile` over small fixtures: a `%` header
   with and without a leading space, a `%` header containing a comma, a
   comma file, an uppercase extension, a plain CSV with no `%` header at
   all (the fixture shape N3 needed -- its crash is fixed, but nothing
   currently stops it recurring silently), and a file with several
   repeated `%` header lines (the shape `data/sensor-tel-test3.txt`
   exercises).
4. A test that builds the callback graph for the shipped
   `dash-config.xlsx` and asserts every registered `Output`/`Input`/
   `State` id exists in the rendered layout. This is the concrete test
   that would have caught the N1 regression in `closed-history.md`
   immediately, as a startup failure, instead of a silent no-op button a
   human had to notice.
5. A `pip`-installable declaration alongside `environment.yml`, so the
   package can be installed without conda.

## 5. Suggested order of work

1. **Tests and tooling** (section 4) -- do this before the structural
   work below, not after. `ruff` plus the helper tests are worth having
   regardless of what else happens next, and the callback-graph test
   specifically de-risks item 1.1.
2. **Structure** (section 1) -- globals onto the instance, `SetNum`/
   `TraceNum` as columns, the `configio.py` extraction. The largest and
   riskiest package here; one concern per commit, no behaviour changes
   mixed in.
3. **Performance** (section 2) -- only after measuring with the largest
   run available. None of it is urgent on the data sets this repository
   ships.
4. **Small, independent items** (section 3) and **hygiene follow-through**
   (defaulting `toDisk` to `False`, the `.gitignore` wording, the
   substring dispatch) can happen any time, in whatever commit next
   touches the relevant code -- none of them need their own dedicated
   session.

`doc/*.tex` (the LaTeX guide) is intentionally absent from this plan: the
user has said they will remove that tree themselves, and no further
automated work on it is expected. See `archive-no-commit/handoff.md`'s
file inventory table for its status.
