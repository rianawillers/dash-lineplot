# dash-lineplot

## Quick start

```bash
conda env create -f environment.yml
conda activate dashplot
python dash-lineplot.py --configfile dash-config.xlsx
```

Then open `http://127.0.0.1:8050/`. The page is served to the system
browser; there is no desktop-window build. The options are `--configfile`,
`--port` and `--datadir`.

To plot a directory of JSON telemetry without writing a config by hand,
generate one and point the server at the same directory:

```bash
python tools/config_from_run.py path/to/run-directory -o run.json
python dash-lineplot.py --configfile run.json --datadir path/to/run-directory
```

Relative data file names in a config are resolved against `--datadir`, so a
config never has to carry a path into somebody's data tree.

To move an existing Excel config to the text format:

```bash
python tools/xlsx_config_to_json.py dash-config.xlsx
```

`dash-config.xlsx` and its converted `dash-config.json` both work against
the bundled `data/` folder.

`commonx-example.json` demonstrates `commonX`, which ties every graph on a
tab to one x scale. Its first tab is linked and its second holds the same
three graphs unlinked, for comparison:

```bash
python dash-lineplot.py --configfile commonx-example.json
```

## What it does

This script reads a config file, in Excel or JSON form, and one or more of
the following data file types:

    * csv files with column names in top row
    * first sheet of an xlsx file with column names in top row
    * json files holding a record array: a list of flat objects, one per sample
    * json files holding named groups, one per sample rate, selected as file.json#group

Matlab (`.mat`) files are no longer supported: the reader that loaded
`DATA`/`NAM`/`TIME` from a Matlab file, and the `scipy` dependency it
needed, were both removed. See [docs/userguide.md](docs/userguide.md) for
the current list, including a known limitation in the plain-CSV reader.

Text-valued columns are treated as enumerations: they are drawn as steps
with the state names on the y axis. Every graph on a page shares the hover
readout, so one pointer position reads the whole page. See
[docs/userguide.md](docs/userguide.md).

It the then proceeds to create and serve a Dash portal. 
The page served has several elements, all constructed from the 
information provided in the config file.

The config file has any number of sheets where each sheet defines
a different set of line graphs to be rendered on a separate tab 
(except for the header sheet, which defines the page header.)
Each graph sheet defines the height of the graphs, axes labels,
one x-value column name and any number of sets of y-value column names.
Each line has a number of attributes with default values if not supplied.
Each tab can be switched on/off for display purposes.
Each graph set can be exported to an html file.

The data file is read and a set of Dash data structures are formed
according to the Excel config file specifications.

In the present script the default config filename is './dash-config.xlsx'.
Any other filename can be provided on the commandline using the -f input flag.

Dash starts a Flask server at the specified port, so the browser must be
pointing to the appropriate port number
localhost:port
Once the server is running, view the page in any browser. The PySide2/PyQt5
desktop window that used to wrap the server has been removed: PySide2 has no
support beyond Python 3.10, and the window offered nothing the browser does
not already do.

This module requires the following data in the current directory:

  * icons/logoSet2long.png
  * assets/bWLwgP.css

It will create folder 'graphs' for output. 

There are numerous Dash and Plotly resources on the Internet: 

    https://dash.plot.ly/integrating-dash
    https://plot.ly/python/reference/
    https://www.datacamp.com/community/tutorials/learn-build-dash-python
    https://github.com/plotly/dash-recipes
    https://github.com/plotly/dash-recipes/blob/master/multiple-hover-data.py
    https://plot.ly/python/subplots/
    https://towardsdatascience.com/creating-an-interactive-data-app-using-plotlys-dash-356428b4699c
    https://dash.plot.ly/dash-core-components/tabs
    https://dash.plot.ly/getting-started-part-2
    https://plot.ly/python/click-events/

This script requires dash, plotly, pandas, numpy, openpyxl and some system
modules. Build the environment from `environment.yml` in this folder, which
pins version floors only and carries no `prefix`, so it solves on Linux and
on Windows alike:

    conda env create -f environment.yml
    conda activate dashplot

See [docs/userguide.md](docs/userguide.md#installation) for updating,
exporting and removing the environment, running without `conda init`, and
the packages earlier versions installed that this one deliberately does
not.

The install notes that used to sit here described pinning Werkzeug 2.0.0
against a Dash 1.x incompatibility, and installing `visdcc` from a bz2
file. Both belonged to a dependency set this version no longer has, and
neither applies to a current solve.

To use as a module in another application:

1. Import the `DashLinePlot` class from the module. There is no
   `DashPlotWindow`: the class that wrapped the server in a Qt desktop
   window was removed along with PySide2/PyQt5 (see above), and nothing
   replaces it, since the browser is the window now.

1. In your code implement something like:

        # do actual plotting
        useCallbacks = True
        plotConfig = './dash-config.xlsx'
        port = '8050' 
        dashlineplotter = DashLinePlot()
        dashlineplotter.runPlotter(port, plotConfig, useCallbacks)

Notes from https://dash.plot.ly/getting-started:

    * The layout is composed of a tree of "components" like html.Div and dcc.Graph.
    * The dash_html_components library has a component for every HTML tag. 
      Each html.xxx(children='yyy') component generates a <h1>yyy</h1> HTML element in your application.
    * Not all components are pure HTML. The dash_core_components describe higher-level components that 
      are interactive and are generated with JavaScript, HTML, and CSS through the React.js library.
    * Each component is described entirely through keyword attributes. 
      Dash is declarative: you will primarily describe your application through these attributes.
    * The children property is special. By convention, it's always the first attribute which means that you can omit it: 
       html.xxx(children='yyy') is the same as html.xxx('yyy'). 
      Also, it can contain a string, a number, a single component, or a list of components.
    * The fonts in the application can be set with a custom CSS stylesheet to modify the default styles of the elements. 
      external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
      app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

https://dash.plot.ly/dash-html-components

The dash layout is composed of a tree of "components" like html.Div and dcc.Graph.
The dash_html_components library contains a component class for every HTML tag as well as keyword arguments 
for all of the HTML arguments.

https://dash.plot.ly/dash-core-components

The dash_core_components includes a set of higher-level components like dropdowns, graphs, markdown blocks, and more.
Graph renders interactive data visualizations using the open source plotly.js JavaScript graphing library. 
Plotly.js supports over 35 chart types and renders charts in both vector-quality SVG and high-performance WebGL.
The figure argument in the dash_core_components.Graph component is the same figure argument that is used by plotly.py, 
Plotly's open source Python graphing library. Check out the plotly.py documentation and gallery to learn more.

Notes on callbacks https://dash.plot.ly/getting-started-part-2:

    https://dash.plot.ly/dash-core-components/tabs
 
A Div component is a wrapper for the HTML5 element.
  
    Div(
        [
            # The Tabs component hold a collection of Tab components.
            Tabs
            (
                # children (list of a list of or a singular dash component, string or numbers | a list of or a singular dash component, 
                # string or number; optional): Array that holds Tab components
                children=
                [
                    # The Tab component controls the style and value of the individual tab 
                    # id (string; optional): The ID of this component, used to identify dash components in callbacks. 
                    #                        The ID needs to be unique across all of the components in an app.
                    # label (string; optional): The tab's label
                    # value (string; optional): Value for determining which Tab is currently selected
                    #
                    # Possible properties of Tab# ['children', 'id', 'label', 'value', 'disabled', 'disabled_style', 'disabled_className', 'className', 'selected_className', 'style', 'selected_style', 'loading_state']

                    Tab(id='RelativePosition', label='RelativePosition', value='Tab 0'), 
                    Tab(id='Velocity', label='Velocity', value='Tab 1'), 
                    Tab(id='MissilePosition', label='MissilePosition', value='Tab 2'), 
                    Tab(id='gimbalFromxls', label='gimbalFromxls', value='Tab 3')
                ], 

                # id (string; optional): The ID of this component, used to identify dash components in callbacks. 
                # The ID needs to be unique across all of the components in an app.
                id='tabs', 

                # value (string; optional): The value of the currently selected Tab
                value='Tab 0'
            ), 

            # id (string; optional): The ID of this component, used to identify dash components in callbacks. 
                                     The ID needs to be unique across all of the components in an app.
            Div(id='tabs-content')
        ]
    )
    
This code is subject to the licenses listed below.
You may not use this file except in compliance with these Licenses. 

Python, numpy, pandas, openpyxl and other 'standard' modules are licensed under the Python License: 

    https://docs.python.org/3/license.html

plotly/dash is licensed under MIT 

    https://community.plot.ly/t/pricing-and-license/9714
    https://en.wikipedia.org/wiki/MIT_License

PySide/Qt and visdcc were dependencies of earlier versions and have been
removed; their licence notices went with them.
