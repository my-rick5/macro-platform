import pandas as pd
from pyfrbus.frbus import Frbus
from pyfrbus.load_data import load_data
import sympy
import builtins
import os
import subprocess

# Inject Derivative into the global builtins so the lambdas in 
# pyfrbus/run_jac.py can see it regardless of import path issues.
builtins.Derivative = sympy.Derivative
builtins.symbols = sympy.symbols
builtins.exp = sympy.exp # Common in FRB/US models
builtins.log = sympy.log    


# 1. SEARCH THE CODEBASE
print("🔎 Searching for the ghost number in the library source...")
try:
    # Search all python files in the pyfrbus directory for the number
    search_results = subprocess.check_output(
        ['grep', '-r', '4.52193548387097', 'pyfrbus/'], 
        stderr=subprocess.STDOUT
    ).decode()
    print(f"✅ Found in code:\n{search_results}")
except subprocess.CalledProcessError:
    print("❌ Not found in library source code.")

# 2. SEARCH THE MODEL AGAIN (Line by line with context)
print("🔎 Searching model.xml with context...")
try:
    # -C 2 shows 2 lines of context before and after the match
    model_match = subprocess.check_output(
        ['grep', '-C', '2', '4.52193548387097', 'models/model.xml'],
        stderr=subprocess.STDOUT
    ).decode()
    print(f"✅ Found in model.xml:\n{model_match}")
except subprocess.CalledProcessError:
    print("❌ Not found in model.xml.")