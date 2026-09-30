"""
Convert an .xlsx plot configuration into the equivalent .json configuration.

The JSON schema mirrors the workbook one for one, so a converted file
describes the same plot in the same words: a 'header' object of
Variable/Value pairs, and a 'sheets' object mapping each graph sheet name to
the list of row objects that sheet held. Empty cells are omitted rather than
written as null, because the loader reinstates any missing column as NaN.

Usage:
    python tools/xlsx_config_to_json.py dash-config.xlsx [-o out.json]

Writing the JSON beside the workbook, with the same stem, is the default.
"""

import argparse
import json
import math
import os
import sys

import numpy as np
import openpyxl as oxl
import pandas as pd


def cellValue(value):
    """Convert one spreadsheet cell to a JSON-representable value."""
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        value = float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def isEmpty(value):
    """True for a cell the workbook left blank."""
    return value is None or (isinstance(value, float) and math.isnan(value))


def workbookToDict(configfile):
    """Read a configuration workbook into the JSON schema's dictionary form."""
    cxls = pd.ExcelFile(configfile)

    dfHeader = pd.read_excel(cxls, 'header')
    header = {}
    for _, row in dfHeader.iterrows():
        header[str(row['Variable'])] = cellValue(row['Value'])

    # openpyxl rather than pd.ExcelFile.sheet_names, to keep the workbook's
    # own sheet order
    cwb = oxl.load_workbook(configfile)

    sheets = {}
    for sheetname in [sn for sn in cwb.sheetnames if 'graph' in sn]:
        dft = pd.read_excel(cxls, sheetname)
        rows = []
        for _, row in dft.iterrows():
            entry = {}
            for column in dft.columns:
                value = cellValue(row[column])
                if not isEmpty(value):
                    entry[str(column)] = value
            if entry:
                rows.append(entry)
        sheets[sheetname] = rows

    return {'header': header, 'sheets': sheets}


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Convert an .xlsx plot configuration to .json.')
    parser.add_argument('configfile', help='Configuration workbook to convert.')
    parser.add_argument('-o', '--output', default=None,
                        help='Output filename (default: alongside the input, '
                             'with a .json suffix).')
    args = parser.parse_args(argv)

    output = args.output
    if output is None:
        output = os.path.splitext(args.configfile)[0] + '.json'

    config = workbookToDict(args.configfile)
    with open(output, 'w', encoding='utf-8') as fjson:
        json.dump(config, fjson, indent=2)
        fjson.write('\n')

    sheets = config['sheets']
    print(f'{args.configfile} -> {output}')
    print(f'  header variables: {len(config["header"])}')
    print(f'  graph sheets    : {len(sheets)}')
    for name, rows in sheets.items():
        print(f'    {name}: {len(rows)} rows')
    return 0


if __name__ == '__main__':
    sys.exit(main())
