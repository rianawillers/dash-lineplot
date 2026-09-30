# Handoff History -- 2026-09 onward

Status: current, actively appended. Will be closed and superseded by 002
once it crosses 30 KB -- see `handoff.md` section 8 for the index.

The first four sessions below (labelled by the date they happened rather
than renumbered from scratch) are a consolidation of material that was
originally written into the sibling `systemCHandbook` repository's own
`archive-no-commit/handoff.md`, its `handoff-history/` files, and its
`docs/devplan/wp2-dashboard-fork.md`, because at the time the two
repositories were being developed together in one session. It is carried
over here in substance, condensed rather than trimmed, so a cold start in
this repository does not depend on that project's handoff at all. Sessions
from 2026-09-14 onward are native to this file.

## Decision, 2026-09-09

The dashboard for a colleague project (`systemCHandbook/CB_3dof`, a 3-DOF
missile guidance simulation) needed a way to plot its telemetry
interactively. The decision taken: modernise this existing fork rather
than build a new tool. It already existed at `NelisW/dash-lineplot`
(forked from `rianawillers/dash-lineplot`, last pushed 2026-04-21) and was
cloned as a sibling of that other project's repository, reached by
relative path. Chosen scope: drop the Qt desktop shell entirely and serve
to the browser only, plus a text (JSON) configuration format alongside
the existing Excel workbook.

The tool's own data model turned out to fit almost exactly: `self.datafiles`
was already a dictionary of filename to `DataFrame`, and each plot names
its own data file, so multiple telemetry files at multiple independent
sample rates could stay independent with no merging and no resampling.
The blocking dependency forcing the work was PySide2, which has no Python
3.14 support -- not Dash, which merely needed catching up.

A development plan for the modernisation was written as WP2 of that other
project's six-work-package plan
(`docs/devplan/wp2-dashboard-fork.md` there), eight tasks with checkboxes
and verification gates, written for a developer working through it by
hand.

## Session, 2026-09-10 -- WP2 executed: browser-only, pandas/numpy 2.x, JSON reader

Executed end to end, unattended. Five commits on `feature/modernise-and-json`:
`b5bfdbf` environment, `d614b7e` modernisation, `8d94f07` generated-output
cleanup, `bcef290` JSON configuration, `6acd9d4` documentation.

**conda had to be installed first.** Neither conda nor pip was present on
the machine. Miniforge 26.7.2 went into `~/miniforge3` in batch mode
(no `conda init`, no shell profile touched); invoked by path.

**The environment solved further ahead than the plan assumed, and two of
the differences were real work.** Dash 4.4.1 has removed `run_server`
outright, not merely deprecated it -- the method is now `run`. pandas 3.0.5
no longer falls back to positional lookup when a `Series` is indexed with
an integer, so `dft[...]['Scale'][0]` raised `KeyError: 0` on a frame that
had been filtered and therefore kept its original row labels; fixed with
`.values[0]`, the idiom already present two lines above in the same
function. The plan's predicted pandas 2.x breakages (`DataFrame.append`,
`iteritems`, `sheetname=`) did not appear at all. numpy 2.5.3 and Plotly
7.0.0 needed no work. Python 3.14.7 solved on the first try; the planned
fallback to 3.13 was never needed.

**The plan named a verification target that cannot work.**
`exmple-dash-config.xlsx` (typo in the upstream filename) points its three
`Datafile` entries at `../../../test/TestPoint05/reswin/...`, a tree not
in the repository, so `loadData` fails and no page builds. `dash-config.xlsx`,
the default, references the bundled `data/` folder and is the config that
actually works. Both the plan file (in the other project) and this
repository's own README record this now.

**Two bugs found that the plan did not anticipate.** The new argparse
entry point ignored `runPlotter`'s return value and printed
"serving on ..." even when no server had started -- which is how a
missing-data-file case first presented as a mystery rather than an error.
`sys.argv.append("--disable-web-security")` appeared twice, a Chromium
flag meant for the now-removed Qt WebEngine, which was only polluting the
argv that argparse reads. Both fixed.

**Verification went beyond "it renders".** Figures were read back out of
the live page and checked against the source telemetry: gimbal pitch/yaw
angles matched recorded limits, a constant-speed signal was flat at the
expected value, and the two data files at 1 ms and 20 ms sample periods
drew at a verified 20:1 point-count ratio with no interpolation anywhere
-- the multi-rate honesty the design intended. One apparent anomaly (a
tracking-error signal spiking to over 100 deg) was chased down to being
correct: the spike occurred exactly at the run's closest-approach time and
is the line of sight swinging past the target, not a tracking failure.

**Left undone, deliberately:** synchronised cross-subplot hover, lost with
the `visdcc` dependency and worth reimplementing only if missed; the
Matlab reader, untouched and unexercised; `pyInstaller/`,
`dash-lineplot.spec` and the two `.bat` launchers, all of which package a
Qt application that no longer exists, left alone rather than half-fixed.

## Session, 2026-09-10 -- second round: page-wide hover, multi-rate JSON, enumerations, commonX

All work in this fork; the closing state from the previous session was
"telemetry renders in a browser" and this made it actually usable on that
telemetry, in several user-directed rounds. Thirteen commits ending at
`e086b32`.

**A user guide was written** (`docs/userguide.md`), following the markdown
house style, LaTeX-conversion-safe flavour, structured after a March-2020
LaTeX guide but with its variable tables rebuilt from the workbook's own
documentation sheet rather than the old guide, which described a Qt
application that no longer existed.

**Features added, all user-requested:**

- Page-wide synchronised hover, `assets/graphsync.js`, replacing what
  `visdcc` used to do and covering a whole page rather than one figure's
  subplots.
- Multi-rate JSON: a top-level object means named groups, one per sample
  rate, each its own table, selected as `file.json#group`; a top-level
  list still means one table.
- A per-`yValue` `Datafile` override, without which the multi-rate reader
  would have been theoretical -- a tab could otherwise only ever show one
  rate.
- Enumerations: text columns mapped to codes with the labels on the y axis,
  drawn as steps.
- `commonX`: every graph on a tab tied to one x range for zoom, pan, click
  and rubber-band selection.
- A compact layout, readouts beside the graph, title inside the plotting
  area.

**Four bugs surfaced in the tool, none in the caller project:**

- Lasso selection was silently dead -- Box Select sends a `range`, Lasso
  sends `lassoPoints`, and only the first was handled.
- `Height` was never applied at all: emitted as a bare `240`, invalid CSS,
  so every graph had always used Plotly's 450 px default regardless of
  configuration.
- The hover/zoom sync guard was a single page-wide boolean cleared on the
  line after it was set, while `Plotly.relayout` is asynchronous, so
  echoes arrived after the flag was already clear and one wedged graph
  disabled syncing everywhere.
- `openpyxl` silently drops workbook parts it does not model -- saving the
  shipped workbook through it removed the `printerSettings` parts. Fixed
  by editing the workbook's own XML directly, one zip entry at a time,
  which preserves everything else byte for byte.

**A mistake worth not repeating:** a `commonX` demonstration was first put
on a tab with `Include` set to `False`, which never renders at all, so the
setting appeared to do nothing. A setting on an excluded tab has no
effect -- an easy trap when a page has several tabs and only some are
switched on.

**On verification methodology:** the Dash callback interface over HTTP
proved a far better test harness than driving the browser directly -- it
exercises the real server-side logic with no rendering involved.
Browser-side behaviour (drag-zoom propagation, rubber-band selection)
needed the user's own confirmation by hand. Two lessons kept from this:
prefer the callback interface for anything server-side, and expect to
hand genuinely browser-side behaviour to the user.

`pkill -f dash-lineplot.py`, run from a shell that is itself running the
command, matches its own process too -- kill by PID instead.

## Session, 2026-09-11 -- third round: axis range entry, blocks, dash-3dof.xlsx

Seven commits ending at `31cd73d`, all pushed.

**Axis range entry, replacing the slider.** The original tool had a range
slider, commented out upstream because it depended on a tab-click to
trigger a redraw and that mechanism had stopped working. The user did not
want the widget revived, only the capability -- "if not a slider widget,
then at least the capability to enter a start x-axis and end x-axis
value" -- so it came back as typed **X range** / **Y range** boxes beside
each graph, with one Apply and one Reset serving both:

| Aspect | Behaviour |
|---|---|
| Reach of x on a `commonX` tab | every graph on the tab |
| Reach of y on a `commonX` tab | only the graph whose boxes were used |
| Blank pair | that axis left alone |
| Mouse zoom | writes the resulting range back into the boxes |
| Autoscale | blanks the pair; blank means the full range |

Apply patches the axis range into the figure already in the browser
(`Patch()`) rather than returning a new figure, so a large trace is not
re-sent to change a zoom.

**Blocks: several data files on one tab.** A graph sheet is now read as a
sequence of blocks -- a `Height` row opens one, `Datafile`/`xValue`/`xLabel`
apply to every graph below until replaced, each `Title` captures what is
in force. A sheet with one block behaves exactly as before, so no
existing sheet broke. `UseSubplots` was removed outright, along with the
subplot figure path and the commented-out slider layout it had been
tangled with -- it had been disabled and announcing itself on every run
for some time.

**`dash-3dof.xlsx`** was rebuilt as a proper viewer for the caller
project's telemetry (eight sheets, one per file, signals grouped rather
than one graph per column). It had arrived plotting nothing -- a copy of
`dash-config` with one sheet repointed at the wrong data file but still
naming the old file's column names.

**Two more bugs found:**

- Suppressing the numeric-input spinner arrows with WebKit-only CSS
  pseudo-elements looked done but did not work in every browser -- one
  browser drew its own stepper as stacked plus/minus controls the rules
  never touched. Fixed properly: the fields are plain text inputs, which
  no browser decorates, and the callback parses strings instead of
  assuming numeric input.
- A broad `git add -A` committed a LibreOffice lock file, which also
  revealed the workbook was open in LibreOffice while it was being rebuilt
  underneath the user. Untracked, and the pattern is now ignored.

**A verification-tooling limitation, recorded honestly:** the in-app
browser pane used for testing stopped rendering partway through this
stretch of work and then became unresponsive entirely, so drag-zoom and
rubber-band selection could not be driven or checked from inside the
session at all -- the user confirmed both by hand instead.

## Session, 2026-09-11 -- header-string generalisation and spectral-reader removal

Two small, user-directed changes to `readdatafile`, the space/comma-file
reader.

The header-stripping code tested three hardcoded column names
(`%Time`, `%CurrentSimTime`, `%t`) individually to remove a leading `%`.
Replaced with one generic pass that strips a leading `%` from whichever
column actually carries it, so the fix works for any column name rather
than three specific ones, and also corrects two latent bugs the old form
had: the old test only inspected the *first* column, so `%Time` in any
other position was missed and a name like `%TimeStamp` matched by
accident; and the old rename appended the corrected column at the end of
the frame instead of preserving its position.

The `.scd`/`.spc` spectral-data reading branch (wavelength/wavenumber/
transmission columns) was removed at the user's request -- unrelated to
the header fix, done as a separate, deliberate deletion in the same
commit.

Commit: `ad4bda8` on `feature/modernise-and-json`, pushed.

## Session, 2026-09-11 -- read-verified repository review

A full read-through review of the repository -- `dash-lineplot.py`, the
two `tools/` scripts, `assets/graphsync.js`, the repository layout -- for
defects, dead code, structural problems and modernisation opportunities.
No code was changed. Written up as `suggestedwork.md` in the repository
root, with a priority-summary table of 25 items and an eight-work-package
recommended order (WP1 deletions through WP8 documentation, with a tests/
tooling package deliberately sequenced early, ahead of the riskiest
structural changes).

**Explicitly flagged as read-verified only, not run-verified**: the
reviewing machine had no `pandas`, `dash`, `plotly` or `scipy` installed
and no conda environment for the project, so nothing in the review could
actually be executed. Every finding states the input that reaches it, so
each is checkable once an environment exists; building that environment
and adding the regression tests the review recommends (its WP6) is what
would turn the list from read-verified to run-verified.

Headline findings, most severe first: `readdatafile` runs its MATLAB and
comma-separated branches as two independent `if`s rather than one
dispatch, so a header carrying both a `%` and a comma silently discards
the first result; `dfData` can be returned unbound for an unrecognised
extension; `skiprows` can reach -1; extension dispatch is neither
case-folded nor exact-matched; six sites call `np.isnan` on configuration
cells that may hold text, so a single spreadsheet typo crashes the whole
page with an unhelpful numpy error; roughly half the registered Dash
callbacks target components that were never actually placed on the page,
hidden only by `suppress_callback_exceptions`; and eleven module-level
`global` statements carry per-instance state into module scope, which
makes the "use as a module" API the file's own docstring advertises unsafe
to use twice in one process.

Also flagged: the entire slider-callback block is dead code (the slider it
served was removed two sessions earlier); `dash-lineplot.spec` and its
`.bat` launchers describe a PySide2/PyQt5/visdcc build that no longer
exists; the vendored `pyInstaller/` tree is 122 MB and 3012 of the
repository's 3064 tracked files, including 1229 tracked `.pyc` files
compiled for Python 3.7; and `doc/*.tex` still documents the removed range
slider at length, with figures.

Commit: `3bc7304` on `feature/modernise-and-json`, pushed.

## Session, 2026-09-14 -- work history split into this repository's own handoff

The dash-lineplot work recorded above had been living entirely inside the
sibling `systemCHandbook` repository's own handoff, history files and
`docs/devplan/wp2-dashboard-fork.md`, because the two repositories were
being developed together in one session. At the user's request, that
material was consolidated and moved here -- this file and `handoff.md` --
plus a matching `prompt.md` capturing the original request, so work on
this tool can continue independently of that other project from now on.

Nothing was removed from `systemCHandbook`: it still correctly records WP2
as complete and points to this repository for detail. This is additive,
not a migration of record -- see the note at the end of `handoff.md`
section 8. Both new files are untracked in git as of this entry; whether
and how to commit them is the user's call, consistent with
`archive-no-commit/` being excluded from version control by convention.
