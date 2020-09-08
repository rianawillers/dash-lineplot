@echo off

echo Starting the Dash Line Plot Graphing Tool ...
echo.
echo.

if [%1]==[] python dash-lineplot.py
if not [%1]==[] python dash-lineplot.py --configfile=%1

set /p DUMMY=done, hit ENTER to exit  