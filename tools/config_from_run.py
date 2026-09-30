"""
Generate a plot configuration for a directory of JSON telemetry files.

Each data group becomes one tab, and each of its columns becomes one graph,
with the time column on the x axis. The result is a first useful page for
any data set without hand-authoring a configuration; edit it afterwards to
group related signals onto shared axes.

Two JSON shapes are handled, and which one a file uses is read from the
file's own structure rather than inferred from its contents:

    a top-level list          one record array, one tab
    a top-level object        named groups, one tab per group, each
                              referenced as 'file.json#group'

Every group keeps its own time column. Nothing is merged across groups or
files and nothing is resampled: groups may sample at completely different
rates, and a zero-order hold belongs to the process that caused it, not to
the plotting layer.

Columns whose values are text are treated as enumerations. They are
plotted, not skipped: the viewer maps the labels onto codes and writes the
labels back onto the y axis.

Usage:
    python tools/config_from_run.py <directory> [-o out.json] [-x t]

Serve the result with the matching --datadir:

    python dash-lineplot.py --configfile out.json --datadir <directory>
"""

import argparse
import json
import os
import sys

SKIP_FILES = {'manifest.json'}


def groupsOf(filename, content):
    """
    Split one JSON file's content into (reference, records) pairs.

    A top-level list yields a single unnamed group referenced by the plain
    file name. A top-level object yields one group per key, each referenced
    with a '#group' fragment.
    """
    if isinstance(content, list):
        return [(filename, os.path.splitext(filename)[0], content)]
    if isinstance(content, dict):
        return [(f'{filename}#{name}', name, records)
                for name, records in content.items()
                if isinstance(records, list)]
    return []


def columnsOf(records, xcolumn):
    """
    Split a record array's keys into numeric and enumeration columns.

    A column is numeric if its first non-null value is a number or a
    boolean; anything else is an enumeration of text labels.
    """
    numeric, enumerated = [], []
    keys = []
    for record in records:
        for key in record:
            if key not in keys:
                keys.append(key)
    for key in keys:
        if key == xcolumn:
            continue
        value = next((r[key] for r in records if r.get(key) is not None), None)
        if isinstance(value, bool) or isinstance(value, (int, float)):
            numeric.append(key)
        else:
            enumerated.append(key)
    return numeric, enumerated


def sheetFor(dataref, groupName, records, xcolumn, height):
    """Build the row list for one group's tab."""
    numeric, enumerated = columnsOf(records, xcolumn)

    rows = [
        {'Variable': 'Height', 'Value': height},
        {'Variable': 'Datafile', 'Value': dataref},
        {'Variable': 'xLabel', 'Value': 'Time [s]', 'Format': '.4f'},
        {'Variable': 'xValue', 'Value': xcolumn},
    ]

    period = ''
    if len(records) > 1:
        step = records[1].get(xcolumn, 0) - records[0].get(xcolumn, 0)
        period = f', sampled every {step * 1000.0:.0f} ms'
    note = f'### {groupName}\n\n{len(records)} samples{period}.'
    if enumerated:
        note += ('\n\nEnumerations, drawn as steps with their labels on the '
                 'y axis: ' + ', '.join(f'`{name}`' for name in enumerated)
                 + '.')
    rows.append({'Variable': 'GraphTop', 'Value': note})

    for column in numeric:
        rows.append({'Variable': 'Title', 'Value': column})
        rows.append({'Variable': 'yLabel', 'Value': column, 'Format': '.6f'})
        rows.append({'Variable': 'yValue', 'Value': column})

    for column in enumerated:
        rows.append({'Variable': 'Title', 'Value': f'{column} (enumeration)'})
        rows.append({'Variable': 'yLabel', 'Value': column})
        rows.append({'Variable': 'yValue', 'Value': column})

    rows.append({'Variable': 'Include', 'Value': True})
    rows.append({'Variable': 'ToDisk', 'Value': False})
    rows.append({'Variable': 'UseSubplots', 'Value': False})
    return rows, numeric, enumerated


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Generate a plot configuration for a telemetry directory.')
    parser.add_argument('datadir', help='Directory holding the JSON telemetry.')
    parser.add_argument('-o', '--output', default=None,
                        help='Output configuration filename (default: '
                             '<directory name>.json in the working directory).')
    parser.add_argument('-x', '--xcolumn', default='t',
                        help='Name of the time column (default: t).')
    parser.add_argument('--height', type=int, default=300,
                        help='Graph height in pixels (default: 300).')
    parser.add_argument('--density', default='compact',
                        choices=['compact', 'comfortable'],
                        help='Page density (default: compact).')
    args = parser.parse_args(argv)

    if not os.path.isdir(args.datadir):
        print(f'not a directory: {args.datadir}')
        return 1

    filenames = sorted(f for f in os.listdir(args.datadir)
                       if f.endswith('.json') and f not in SKIP_FILES)
    if not filenames:
        print(f'no telemetry files found in {args.datadir}')
        return 1

    runName = os.path.basename(os.path.normpath(args.datadir))
    output = args.output or f'{runName}.json'

    sheets = {}
    totalGraphs = 0
    totalEnums = 0
    for filename in filenames:
        with open(os.path.join(args.datadir, filename), 'r',
                  encoding='utf-8') as fjson:
            content = json.load(fjson)

        groups = groupsOf(filename, content)
        if not groups:
            print(f'  {filename}: not a record array or group object, skipped')
            continue

        for dataref, groupName, records in groups:
            if not records:
                print(f'  {dataref}: empty, skipped')
                continue
            rows, numeric, enumerated = sheetFor(dataref, groupName, records,
                                                 args.xcolumn, args.height)
            sheets[f'graph-{groupName}'] = rows
            totalGraphs += len(numeric) + len(enumerated)
            totalEnums += len(enumerated)
            enumNote = f', {len(enumerated)} enumeration' if enumerated else ''
            print(f'  {dataref}: {len(records)} samples, '
                  f'{len(numeric) + len(enumerated)} graphs{enumNote}')

    config = {
        'header': {
            'Pagetitle': f'{runName} telemetry',
            'PageTop': (f'# {runName}\n\nOne tab per data group, one graph per '
                        'column. Each group keeps its own time base: groups '
                        'may sample at different rates, and nothing is '
                        'interpolated between them.'),
            'PageBottom': f'Generated from `{args.datadir}`.',
            'Datafile': 'none',
            'Density': args.density,
        },
        'sheets': sheets,
    }

    with open(output, 'w', encoding='utf-8') as fjson:
        json.dump(config, fjson, indent=2)
        fjson.write('\n')

    print(f'\nwrote {output}: {len(sheets)} tabs, {totalGraphs} graphs '
          f'({totalEnums} enumeration)')
    print(f'serve with:\n'
          f'  python dash-lineplot.py --configfile {output} '
          f'--datadir {args.datadir}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
