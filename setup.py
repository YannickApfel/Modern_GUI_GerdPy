import sys
import os
from cx_Freeze import setup, Executable

# ADD FILES
files = ['ZAE.ico', 'main.ui', 'resources.qrc', 'requirements.txt', 'images/', 'themes/', 'GERDPy/', 'modules/', 'progress/', 'widgets/']

# TARGET
target = Executable(
    script="guimain.py",
    base="Win32GUI",
    icon="ZAE.ico"
)

# SETUP CX FREEZE
setup(
    name = "GERDPy",
    version = "2.0.0",
    description = "Simulation Tool for Geothermal Heat Pipe Surface Heating Systems",
    author = "Yannick Apfel, Meike Martin",
    options = {'build_exe' : {'include_files' : files}},
    executables = [target]
    
)
