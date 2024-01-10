# dash-lineplot

This script reads an Excel config file and one or more of the following file types:
    
    * matlab file with data in 'DATA', variable names in 'NAM' and time base in 'TIME'
    * csv files with column names in top row
    * first sheet of an xlsx file with column names in top row
    
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
This means that once the server is running, you can view the page with 
the PySide browser as used here, or in an external browser.

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
    https://plot.ly/python/range-slider/
    https://plot.ly/python/click-events/

This script requires openpyxl, PySide2 (PyQt5 is loaded if PySide2 not available), numpy, 
pandas, plotly, dash, threading, openpyxl and some system modules.

To install dash when connected to the internet:

    conda config --add channels conda-forge
    conda search dash-daq --channel conda-forge
    conda install dash
    conda install dash-html-components
    conda install dash-core-components
    conda install dash-table 
    conda install dash-daq

Jan 2024 install and test: build conda environment from the provided yml file

    cd dash-lineplot\pythonSetup
    conda env create -f dashplotenv.yml
    activate dashplotenv
    startPlotTool.bat


Jan 2023 install: some versions had to be downgraded due to a change in Werkzeug not compatible with Dash:

    https://github.com/plotly/dash/issues/1992  
    https://stackoverflow.com/questions/30564332/how-to-download-previous-version-of-werkzeug

    pip install Werkzeug==2.0.0
    pip install dash-table==4.11.2
    pip install dash-renderer==1.9.0
    pip install dash-html-components==1.1.2
    pip install dash-core-components==1.15.0

This package could not be installed with 

    conda install visdcc
    
Conflicts between versions. Installing from the bz2 file worked however.

    Jan 2023 succesfull: pip install visdcc

A mid-2019 off-line install required the following packages to be manually installed.

    conda install dash-0.39.0-py_0.tar.bz2
    conda install flask-compress-1.4.0-py_0.tar.bz2
    conda install plotly-4.1.1-py_0.tar.bz2
    conda install dash-html-components-0.14.0-py_0.tar.bz2
    conda install dash-core-components-0.44.0-py_0.tar.bz2
    conda install dash-table-3.6.0-py_0.tar.bz2
    conda install dash-daq-0.1.4-py_0.tar.bz2
    conda install plotly-orca-1.2.1-1.tar.bz2
    conda install retrying-1.3.3-py37_1.tar.bz2
    conda install dash-renderer-0.20.0-py_0.tar.bz2
    conda install visdcc-0.0.40-pyh516909a_0.tar.bz2

Plotly packages seem to be here:  

    https://anaconda.org/plotly  
    https://anaconda.org/plotly/repo  

There are 17 packages, located under the package name, Files tab:

    https://anaconda.org/plotly/plotly/files  
    
or   

    https://anaconda.org/plotly/dash/files 

To use as a module in another application:

1. Import the DashLinePlot and DashPlotWindow classes from the module
   
1. In your code implement something like:

        # create new window
        self.dashWidget = DashPlotWindow(port)
        self.dashWidget.show()

        # do actual plotting
        useCallBacks = True
        plotConfig = './dash-config.xlsx'
        port = '8050' 
        dashlineplotter = DashLinePlot()
        dashlineplotter.runPlotter(port, plotConfig, useCallBacks)

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

Python, scipy, numpy, pandas, and other 'standard' modules are licensed under the Python License: 

    https://docs.python.org/3.7/license.html.  

PySide: 'Qt for Python' is licensed under the LGPL3 license:

    https://www.gnu.org/licenses/lgpl-3.0.html
 
plotly/dash/visdcc is licensed under MIT 

    https://community.plot.ly/t/pricing-and-license/9714
    https://en.wikipedia.org/wiki/MIT_License
