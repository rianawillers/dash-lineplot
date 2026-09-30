/*
 * Links the graphs on a page to each other.
 *
 * Two behaviours, both plain browser-side JavaScript talking to the Plotly
 * graphs already on the page. Dash serves every .js file in the assets
 * folder automatically, so neither needs a package or a callback. The first
 * replaces the visdcc.Run_js injection that did the same job before visdcc
 * stopped being maintained.
 *
 *   Hover        hovering any graph makes every other graph on the page show
 *                its own readout at the same x value.
 *
 *   Common x     graphs whose row carries the common-x class share one x
 *                range: zooming, panning or autoscaling any of them applies
 *                the same range to all the others. Set by commonX in the
 *                configuration.
 *
 * Each graph resolves an x against its own samples, so graphs recorded at
 * different rates each show their own nearest sample. Nothing is
 * interpolated, and no graph is assumed to share a time base, a sample rate
 * or a data type with any other.
 *
 * Graphs are re-created when a tab is selected, so a MutationObserver
 * re-attaches the handlers whenever the tab content changes.
 */

(function () {
    'use strict';

    // Guard against the feedback loop: driving another graph makes that graph
    // emit the same event in turn, which would come straight back here.
    //
    // The mark is per graph rather than one flag for the whole page, and it is
    // held until the drive that set it has actually finished. Plotly.relayout
    // is asynchronous, so a single shared flag reset on the next line would be
    // long clear by the time the echo arrived, and every synced graph would
    // re-broadcast to every other. A page-wide flag also means one wedged
    // graph silently disables syncing everywhere, hover included.
    function isDriven(gd) {
        return (gd._graphSyncDriving || 0) > 0;
    }

    function markDriven(gd) {
        gd._graphSyncDriving = (gd._graphSyncDriving || 0) + 1;
    }

    function releaseDriven(gd) {
        gd._graphSyncDriving = Math.max(0, (gd._graphSyncDriving || 1) - 1);
    }

    function plots() {
        return Array.prototype.slice.call(
            document.querySelectorAll('.js-plotly-plot'));
    }

    function isVisible(gd) {
        return gd.offsetParent !== null;
    }

    // Graphs sharing an x axis with this one: those inside a .common-x row.
    // A graph on a tab that did not ask for commonX is in no group at all.
    function xGroupOf(gd) {
        var row = gd.closest ? gd.closest('.graph-row.common-x') : null;
        if (!row || !row.parentNode) {
            return [];
        }
        return Array.prototype.slice.call(
            row.parentNode.querySelectorAll(
                '.graph-row.common-x .js-plotly-plot'));
    }

    // Every subplot of one graph, e.g. ['xy'] or ['xy', 'xy2', ...].
    function subplotsOf(gd) {
        if (!gd._fullLayout || !gd._fullLayout._plots) {
            return ['xy'];
        }
        return Object.keys(gd._fullLayout._plots);
    }

    function showAtX(gd, xval) {
        try {
            window.Plotly.Fx.hover(gd, { xval: xval }, subplotsOf(gd));
        } catch (err) {
            /* A graph whose x axis cannot resolve this value simply shows
               nothing. That is not an error worth reporting to the user. */
        }
    }

    function clear(gd) {
        try {
            window.Plotly.Fx.unhover(gd);
        } catch (err) {
            /* as above */
        }
    }

    function onHover(source, eventdata) {
        if (isDriven(source)) {
            return;
        }
        if (!eventdata || !eventdata.xvals || eventdata.xvals.length === 0) {
            return;
        }
        var xval = eventdata.xvals[0];

        plots().forEach(function (gd) {
            if (gd !== source && isVisible(gd)) {
                markDriven(gd);
                try {
                    showAtX(gd, xval);
                } finally {
                    releaseDriven(gd);
                }
            }
        });
    }

    function onUnhover(source) {
        if (isDriven(source)) {
            return;
        }
        plots().forEach(function (gd) {
            if (gd !== source) {
                markDriven(gd);
                try {
                    clear(gd);
                } finally {
                    releaseDriven(gd);
                }
            }
        });
    }

    // Apply one graph's new x range to every graph sharing its x axis.
    function onRelayout(source, eventdata) {
        if (isDriven(source) || !eventdata) {
            return;
        }

        var update = null;
        if (eventdata['xaxis.autorange'] === true) {
            update = { 'xaxis.autorange': true };
        } else if (eventdata['xaxis.range[0]'] !== undefined &&
                   eventdata['xaxis.range[1]'] !== undefined) {
            update = {
                'xaxis.range[0]': eventdata['xaxis.range[0]'],
                'xaxis.range[1]': eventdata['xaxis.range[1]']
            };
        } else if (eventdata['xaxis.range'] !== undefined) {
            update = {
                'xaxis.range[0]': eventdata['xaxis.range'][0],
                'xaxis.range[1]': eventdata['xaxis.range'][1]
            };
        }

        if (update === null) {
            // a relayout that did not touch the x axis, a dragmode change say
            return;
        }

        var group = xGroupOf(source);
        if (group.length < 2) {
            return;
        }

        // Hold each target's mark until its own relayout has settled, so the
        // echo it emits on completion is recognised as ours and dropped.
        group.forEach(function (gd) {
            if (gd === source) {
                return;
            }
            markDriven(gd);
            var done = function () { releaseDriven(gd); };
            try {
                Promise.resolve(window.Plotly.relayout(gd, update))
                    .then(done, done);
            } catch (err) {
                /* a graph that cannot take this range keeps its own */
                done();
            }
        });
    }

    function attach(gd) {
        if (gd._graphSyncAttached || typeof gd.on !== 'function') {
            return;
        }
        gd._graphSyncAttached = true;
        gd.on('plotly_hover', function (eventdata) { onHover(gd, eventdata); });
        gd.on('plotly_unhover', function () { onUnhover(gd); });
        gd.on('plotly_relayout', function (eventdata) { onRelayout(gd, eventdata); });
    }

    function attachAll() {
        if (!window.Plotly) {
            return;
        }
        plots().forEach(attach);
    }

    // Dash renders tab content through a callback, so the graphs of a tab do
    // not exist until that tab is first selected, and are replaced wholesale
    // on every later selection.
    function watch() {
        attachAll();
        var observer = new MutationObserver(function () { attachAll(); });
        observer.observe(document.body, { childList: true, subtree: true });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', watch);
    } else {
        watch();
    }
}());
