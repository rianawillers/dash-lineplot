# -*- mode: python ; coding: utf-8 -*-

# https://pyinstaller.readthedocs.io/en/stable/operating-mode.html
# https://pyinstaller.readthedocs.io/en/stable/spec-files.html
# https://realpython.com/pyinstaller-python
#
# PyInstaller reads a Python script written by you. It analyzes your code to discover 
# every other module and library your script needs in order to execute. Then it collects 
# copies of all those files – including the active Python interpreter! – and puts them 
# with your script in a single folder, or optionally in a single executable file.
#
# This file is the pyinstaller spec file for bundling p2TestbenchAssistant.py in one folder
# for distribution to the client. This folder contains all the script’s dependencies, 
# and an executable file named p2TestbenchAssistant.exe. The icons and templates data
# folders are included in the distribution. Note that this spec file was set up to run
# from folder C:\Temp\withOsc. Update this path if you create the bundled code from another
# folder. 
#
# usage: pyinstaller p2TestbenchAssistant.spec
#
# Initial usage to get first spec file:
#     pyinstaller --hidden-import=pyvisa --hidden-import=pyvisa-py p2TestbenchAssistant.py
#
# The code can also be bundled to one file:
#     pyinstaller --onefile --hidden-import=pyvisa --hidden-import=pyvisa-py p2TestbenchAssistant.py
# In this case p2TestbenchAssistant.py script and all its dependencies are bundled into a single executable 
# named p2TestbenchAssistant.exe. One sibgle file is distributed to the client.  When started it creates a 
# temporary folder in the appropriate temp-folder location for the OS. The folder is named _MEIxxxxxx, 
# where xxxxxx is a random number. The bootloader uncompresses the support files and writes copies into
# the the temporary folder. This can take a little time. That is why a one-file app is a little slower 
# to start than a one-folder app. After creating the temporary folder, the bootloader proceeds exactly 
# as for the one-folder bundle, in the context of the temporary folder. When the bundled code terminates, 
# the bootloader deletes the temporary folder.


block_cipher = None

added_files = [
         ( 'icons', 'icons' ),
         ( 'assets', 'assets'),
         ( 'data', 'data'),
         ( 'dash-config.xlsx', '.'),
         ( 'pyInstaller\\platforms', 'platforms' ),       
         ( 'pyInstaller\\dash\\dash_core_components', 'dash_core_components'),
         ( 'pyInstaller\\dash\\dash_html_components', 'dash_html_components'),
         ( 'pyInstaller\\dash\\dash_renderer', 'dash_renderer'), 
         ( 'pyInstaller\\dash\\dash', 'dash'),
         ( 'pyInstaller\\plotly', 'plotly'),
         ( 'pyInstaller\\qt\\translations', 'translations'),
         ( 'pyInstaller\\qt\\resources', 'resources'),
         ( 'pyInstaller\\qt\\qt.conf', '.'),
         ( 'pyInstaller\\qt\\QtWebEngineProcess.exe', '.'),
         ( 'pyInstaller\\visdcc', 'visdcc'),
         ( 'pyInstaller\\startPlotTool.bat', '.'),
         ]
         
a = Analysis(['dash-lineplot.py'],
             pathex=['C:\\Temp'],
             datas=added_files,
             hiddenimports=['PyQt5.QtWebEngineWidgets','PyQt5.QtNetwork','PyQt5.QtWebEngineCore', 'PyQt5.QtWebChannel','PyQt5.QtPrintSupport'],
             hookspath=[],
             runtime_hooks=[],
             excludes=['tkinter'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='dash-lineplot',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='dash-lineplot')
