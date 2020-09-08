@echo off

echo Starting the Dash Line Plot Graphing Tool ....
echo.
echo.

cd dash-lineplot

if [%1]==[] dash-lineplot.exe
if not [%1]==[] dash-lineplot.exe --configfile=%1

set /p DUMMY=done, hit ENTER to exit