@echo off

pyInstaller dash-lineplot.spec

echo .
echo .
echo Removing QtWebEngineProcess.exe from the PyQt5\Qt\bin\ path if present.
echo .

del dist\dash-lineplot\PyQt5\Qt\bin\QtWebEngineProcess.exe
move dist\dash-lineplot\startPlotTool.bat dist\startPlotTool.bat

set /p DUMMY=done, hit ENTER to exit  

