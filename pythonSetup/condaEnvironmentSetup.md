## conda dashplotenv environment

The dashenv conda environment is used for dash-plotly work.

This environment is set up as follows:

    conda create --name dashplotenv
    conda activate dashplotenv

    conda config --add channels conda-forge

    conda install numpy
    conda install pandas
    conda install openpyxl

    pip install PyQt5
    pip install PyQtWebEngine

    conda install dash
    conda install dash-daq
    conda install dash-table 

    pip install visdcc

To use the environment

    conda activate dashplotenv

Terminate with

    conda deactivate 

### Using a yml export

https://shandou.medium.com/export-and-create-conda-environment-with-yml-5de619fe5a2

Export environment

    conda env export > dashplotenv.yml

Creating the environment with a yml file:

    conda env create -f dashplotenv.yml
