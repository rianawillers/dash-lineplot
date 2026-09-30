# dash-lineplot -- Task Handoff Document

Status: 2026-09-15 -- browser-served Dash viewer, modernised off a 2022
conda-and-Qt base. Reads CSV, XLSX and JSON data (including multi-rate
JSON; Matlab support was removed, see `closed-history.md`), configured by
an Excel workbook or an equivalent JSON file. Runs on
`feature/modernise-and-json`, pushed to `origin`, not merged to `master`;
that stays the user's decision.

History-file cadence: size threshold, 30 KB (matching the convention this
work already used in the `systemCHandbook` handoff it was split out of).

This work was originally developed and recorded inside the sibling
`systemCHandbook` repository's own handoff, history files and
`docs/devplan/wp2-dashboard-fork.md` (WP2 of that project's development
plan), because the two repositories were being worked on together in one
session. It has now been split out here so this tool can be worked on in
its own right, independently of that project. Nothing in `systemCHandbook`
was edited to remove it -- see the note at the end of section 8.

## 1. File Inventory

Guidance: key files/folders and what each one is.

| Path | What it is |
|---|---|
| `dash-lineplot.py` | The whole application: config loading, data loading, graph building, Dash callbacks, CLI entry point. About 2000 lines, one file. |
| `assets/graphsync.js` | Browser-side JavaScript, served automatically by Dash's assets folder. Page-wide hover sync and `commonX` axis linking -- see section 2. |
| `assets/bWLwgP.css`, `assets/density.css` | Page styling. `density.css` drives the compact/comfortable layout toggle. |
| `dash-config.xlsx` | The default configuration workbook (`-f ./dash-config.xlsx` is the CLI default). Points at the bundled `data/` folder and is the one that actually renders. |
| `dash-config.json` | The JSON-format equivalent of `dash-config.xlsx`, produced by `tools/xlsx_config_to_json.py`. The two are expected to stay behaviourally identical. |
| `dash-3dof.xlsx` | A ready-made viewer for the `CB_3dof` project's telemetry: eight sheets, one per file in that project's `out/ENG-01`, signals grouped rather than one graph per column. Runs without `--datadir`. This is the one file here that is specific to a caller project; everything else in the tool is general-purpose. |
| `commonx-example.json` | A small runnable example demonstrating the `commonX` axis-linking feature. |
| `data/` | The data files the bundled example configs reference: `.rgeo`, `.traj`, `.gmbl` (OSSIM-style space/comma-separated text) and one `.xlsx`. |
| `tools/config_from_run.py` | Generates a first-pass JSON configuration for a directory of JSON telemetry files: one tab per data group, one graph per field, enumerations detected and plotted rather than skipped. |
| `tools/xlsx_config_to_json.py` | Converts an `.xlsx` configuration workbook to the equivalent JSON schema, losslessly (verified by round-trip comparison against `dash-config.xlsx`). |
| `docs/userguide.md` | The maintained user-facing reference for the tool as it stands today. Follows the markdown house style, LaTeX-conversion-safe flavour. Read this, not `doc/*.tex`, for how to use the tool. |
| `doc/*.tex`, `doc/pic/` | A March-2020 LaTeX user guide. **Stale** -- documents the removed PySide/Qt desktop window, the removed range slider (with three figures), and `visdcc` as a live dependency. Every chapter now carries a "this is historical, see `docs/userguide.md`" notice (added a session ago) rather than being half-fixed. **The user has said they will remove this tree themselves; do not delete it.** |
| `environment.yml` | Portable conda environment, pins version floors only, no build strings, no `prefix:`. Solves on both Linux and Windows. See section 7 for the versions it currently solves to. |
| `suggestedwork.md` | The current, **forward-looking-only** backlog: open defects, structural and performance issues, hygiene, and an order of work. Closed items are not kept here -- see `closed-history.md` below. |
| `archive-no-commit/closed-history.md` | Every closed item's write-up, and the narrative of each past review pass, moved out of `suggestedwork.md` to keep that file short. Read this for *why* something is the way it is; read `suggestedwork.md` for what is still worth doing. |

## 2. Current Design

Guidance: what the system does now, stated plainly.

The tool serves a Dash/Flask page to the system browser -- there is no
desktop window; the PySide2/PyQt5 shell was removed because PySide2 has no
Python 3.14 support and the window added nothing the browser does not
already do. It is invoked as:

```bash
python dash-lineplot.py --configfile <path> [--port N] [--datadir DIR]
```

**Configuration** is an Excel workbook or an equivalent JSON file: a
`header` sheet/object of page-level settings, and any number of graph
sheets/objects, each becoming one browser tab. `readConfigTables` reads
either format into the same table shape, so the rest of the code never
has to care which one it got.

**Data** can be CSV, XLSX, or JSON (Matlab support existed once, via
`scipy.io.loadmat`, but was removed -- see `closed-history.md`). JSON
supports two shapes: a top-level list is one record array (one table); a
top-level object is a set of named groups, one per sample rate, each
selected in the config as `file.json#group`. Nothing is ever merged,
resampled, or aligned between files or between groups of one file -- each
table is drawn at its own rate, because a zero-order hold belongs to the
process that caused it, never to the plotting layer. `self.datafiles` is
a dictionary keyed by the exact `Datafile` reference string (fragment
included), one `DataFrame` per file or per group.

**One tab, several files.** A graph sheet is read top to bottom as a
sequence of blocks: a `Height` row opens one, and `Datafile`, `xValue` and
`xLabel` rows apply to every graph below until the next one of that kind
replaces them. A single-block sheet behaves exactly as it always did. This
is what lets one tab compare signals recorded at genuinely different
rates.

**Enumerations.** A column whose values are text (not numeric, not
boolean) is plotted as a state signal: its distinct values are mapped to
integer codes, drawn as a step line (`line.shape = 'hv'`, since a state is
piecewise constant), and the y axis is relabelled with the original names.
Category order is either declared in the config (`Categories`) or taken
from first appearance in the data; a value present in the data but absent
from a declared order is appended, never dropped.

**Page-wide hover and `commonX`**, both in `assets/graphsync.js`, plain
browser JS served automatically from the `assets` folder (replacing the
`visdcc` mechanism that stopped working upstream). Hovering any graph
shows every other graph's readout at that x, each against its own
samples -- nothing interpolated. A tab that sets `commonX` ties every
graph on it to one x range: zoom, pan, click and rubber-band selection on
any of them apply to all of them.

**Typed X/Y range entry**, replacing the range slider that had stopped
working upstream (it depended on a tab-click to trigger a redraw). Plain
text inputs beside each graph (no browser draws chrome on a text input,
which a numeric input's spinner arrows do inconsistently), with Apply and
Reset. On a `commonX` tab, x reaches every graph in the group; y applies
only to the graph whose own boxes were used, because the graphs of a tab
have their own scales and often their own units. Apply patches the
existing figure's axis range (`Patch()`) rather than sending a new figure,
so a large trace is not re-transmitted to change a zoom. A mouse
zoom/pan/autoscale writes the resulting range back into the boxes.

**Compact layout.** Readouts sit beside the graph rather than under it,
with zero vertical space between graph rows and the title drawn inside
the plotting area (`xref/yref: 'paper'`), so a tall stack of small graphs
does not waste page height on Plotly's default margins.

## 3. Critical Implementation Details

Guidance: current behavior that isn't obvious from the code and is worth
not silently forgetting.

- `Height` must resolve to a valid CSS length. The code appends `px`; a
  bare numeric string is invalid CSS and Plotly silently falls back to its
  450 px default with no error.
- On a `commonX` tab, y-range entry deliberately does not fan out: only
  the graph whose own Apply button was pressed gets its y range changed.
  x does fan out to every graph in the group.
- Box Select and Lasso Select report different keys in `selectedData`
  (`range` vs `lassoPoints`); both must be handled or lasso selection
  silently does nothing.
- The hover/zoom sync guard in `graphsync.js` is a per-graph counter, not
  a single page-wide boolean -- `Plotly.relayout` is asynchronous, and a
  boolean cleared on the next line races the echo it is meant to suppress.
- `openpyxl` silently drops workbook parts it does not model (it removed
  `printerSettings` from `dash-config.xlsx` the first time it was
  round-tripped). The workbook is now edited through its own XML, one zip
  entry at a time, when a change must not touch anything else in the
  file.
- pandas 3.x dropped positional fallback when a `Series` is indexed with
  an integer; a frame that has been filtered keeps its original row
  labels, so `series[0]` can raise `KeyError: 0`. Use `.values[0]` or
  `.iloc[0]`.
- Dash 4.x removed `run_server` outright (not merely deprecated); the
  method is `run`.
- `pkill -f dash-lineplot.py` from a shell that is itself running the
  command matches its own process too.

## 4. Standing Constraints

Guidance: decisions marked "do not silently revisit", one line each on
why.

- **The tool knows nothing about any caller's project layout, and that is
  deliberate.** It takes a data directory as `--datadir` and infers
  nothing about data types, sample rates, or time bases from any caller's
  conventions. Resist teaching it about a specific project's telemetry
  fields; `tools/config_from_run.py` plus a hand-edited config is the
  bridge, not code in the tool itself. (`dash-3dof.xlsx` is the one
  deliberate, contained exception -- a ready-made config, not a code
  change.)
- **Never merge or resample tables, ever.** Signals recorded at different
  rates are drawn at their own rates on the same axis. A zero-order hold
  is a property of whatever process caused it and must never be assumed
  by this tool.
- **Cross-platform.** Built and run on both Ubuntu and Windows. No
  hard-coded paths, no drive letters, no user home directories.
  `dash-lineplot.py` now uses `pathlib.Path` exclusively (the `os.path`
  inconsistency this bullet used to warn about is closed -- see
  `closed-history.md` pass 4); keep it that way going forward.
- **`environment.yml` pins version floors, never build strings, never a
  `prefix:`.** The 2022 file this replaced was Windows-only for exactly
  those reasons.
- **Never commit to `master`.** Work happens on a feature branch
  (currently `feature/modernise-and-json`); merging is the user's
  decision.
- **`archive-no-commit/` must always be committed, despite its name.** The
  `no-commit` in the folder name is required by the handoff-management
  skill's own naming convention -- it is not an instruction to exclude the
  folder from commits in this repository. This repository is deployed by
  cloning to several PCs, so `handoff.md`, `handoff-history/`, and
  `prompt.md` under this folder must travel with every clone like any other
  tracked file. Stage and commit changes here exactly as any other change;
  do not treat the directory name as a reason to leave it out. (A prior
  session got this wrong and left `prompt.md` uncommitted -- see history.)
- **`suggestedwork.md` stays forward-looking only.** When an item in it
  closes, move its full write-up to `archive-no-commit/closed-history.md`
  and delete it from `suggestedwork.md` -- do not mark items closed in
  place there. The mix of open and closed items in one file was found
  hard to read and this split is the fix; don't let `suggestedwork.md`
  silently regrow a "closed since last review" section.

## 5. Current Backlog

Guidance: prioritized, currently open items only.

As of 2026-09-15, `suggestedwork.md` was reworked to be forward-looking
only (see the standing constraint above): it now holds exactly the open
items, in five short sections (structure, performance, small independent
items, repository hygiene, suggested order of work), with no closed
history mixed in. **Read `suggestedwork.md` itself for the current
backlog -- do not summarise it here, and do not let this section regrow
into a second, driftable copy of it**, which is what happened to the list
this section used to carry (it had frozen at the 2026-09-11 first-pass
review while five further sessions of work landed). If you need the
history behind why something closed, that's
`archive-no-commit/closed-history.md`.

In one line, what's left as of this rework: instance-vs-`global` state,
`SetNum`/`TraceNum` columns instead of parsed index strings, the
`configio.py` extraction, no tests/linter/`pyproject.toml`, and a handful
of performance items not yet worth measuring against real data.

**Left undone, deliberately, not because it is forgotten:**

- Synchronised cross-subplot hover was lost with `visdcc` and reimplemented
  page-wide instead, in `graphsync.js`. Reimplementing anything closer to
  the original subplot-scoped behaviour is a separate decision, worth
  taking only if it turns out to be missed.
- HTML copies of every graph are written to `./graphs/` on every run
  whenever a sheet sets its disk-export flag; `suggestedwork.md` section
  2.4 recommends defaulting that off.

## 6. How to Cold-Restart

Guidance: the minimum steps a fresh session needs to resume work
correctly.

1. Read this file and the current (highest-numbered) file under
   `handoff-history/` -- never an older, closed one.
2. `git branch -vv` and `git log --oneline -10` for the actual repository
   state; do not trust a branch name or commit hash quoted in prose here
   without checking.
3. Activate the conda environment: `conda activate dashplot`, or invoke it
   by path if conda is not on `PATH` -- see section 7.
4. `docs/userguide.md` is the maintained reference for how the tool
   behaves today; do not restate its content here.
5. `suggestedwork.md` is the maintained reference for what is wrong and
   what to do about it; its own final section gives the suggested order
   of work. `archive-no-commit/closed-history.md` has the reasoning
   behind anything already closed.
6. If work on this tool is being done from a caller project (as it was
   originally, from `systemCHandbook/CB_3dof`), this tool is reached by
   relative path only (`../dash-lineplot` from that project's own root, or
   whatever sibling relationship applies) and never learns that caller's
   layout -- see section 4.

## 7. Technical Reference

Guidance: config format, key function signatures, dependencies.

**Environment**, as most recently solved by conda-forge (2026-09-10):
Python 3.14.7, Dash 4.4.1, Plotly 7.0.0, pandas 3.0.5, numpy 2.5.3,
openpyxl 3.1.5. (`scipy` was dropped from `environment.yml` once the
Matlab reader that needed it was removed -- see `closed-history.md`.)
`environment.yml` pins floors matching these levels of dash/pandas/numpy
specifically, since those three broke
something on the jump from the 2022 baseline (`run_server` removed,
`Series[int]` positional fallback removed) and are worth not regressing
past silently.

conda itself lives at `~/miniforge3`, installed in batch mode (no
`conda init`, no shell profile modified). Invoke by path
(`~/miniforge3/bin/conda`, `~/miniforge3/envs/dashplot/bin/python`) if not
activated. Self-contained and removable with `rm -rf ~/miniforge3` if it
is ever no longer wanted.

**Configuration schema** (see `readConfigTables` in `dash-lineplot.py`,
and `tools/xlsx_config_to_json.py` for the converter): a `header`
Variable/Value table, and any number of graph sheets/objects, each a table
of rows carrying `Variable`, `Value`, `Format`, `LineLabel`, `GraphType`,
`Scale`, `Offset`, `Colour`, `Linewidth`, `Dash`, `Mode`,
`MarkerOpacity`, `Categories`, `Datafile` (the full column list is
`CONFIG_COLUMNS` in `dash-lineplot.py`). A JSON config mirrors the
workbook one for one, using the same field names.

**Entry point**:

```bash
python dash-lineplot.py --configfile <path> [--port 8050] [--datadir DIR]
```

`--datadir` resolves any relative `Datafile` reference in the
configuration; a `#group` fragment on a JSON reference selects one named
group inside a multi-rate file.

**Generating a first-pass config for a data directory**:

```bash
python tools/config_from_run.py <directory>
python dash-lineplot.py --configfile <directory-name>.json --datadir <directory>
```

## 8. History Index

Guidance: edit the STATE sections above in place, never append a new
top-level section with a fresh number. Session narrative goes in the
current history file, not here.

- `handoff-history/handoff-history-001-2026-09-onward.md` -- current,
  actively appended. Opens with the consolidated narrative of all the
  `dash-lineplot` work that had previously been recorded inside the
  sibling `systemCHandbook` repository's own handoff and history files
  (its sessions 7 through 10, plus that repository's
  `docs/devplan/wp2-dashboard-fork.md`), carried over here verbatim in
  substance so nothing is lost by the split, then continues with whatever
  happens in this repository from here on.

**Note on the source material.** The narrative folded into history file
001 was originally written into `systemCHandbook`'s
`archive-no-commit/handoff.md`, its `archive-no-commit/handoff-history/`
files, and its `docs/devplan/wp2-dashboard-fork.md`, because the two
repositories were being developed together in one session. Splitting it
out here is additive: nothing was deleted from `systemCHandbook`, and that
project's own handoff still correctly describes WP2 as complete and still
points here for the detail. Anyone maintaining both repositories should
expect a small amount of duplication between `systemCHandbook`'s WP2
record and this file's history, and should treat *this* repository's
history as authoritative for anything that happens to `dash-lineplot`
from this point forward.
