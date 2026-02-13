import pandas as pd
from pyfrbus.frbus import Frbus
from pyfrbus.load_data import load_data
import sympy
import builtins
import os
import subprocess
import xml.etree.ElementTree as ET
# Inject Derivative into the global builtins so the lambdas in 
# pyfrbus/run_jac.py can see it regardless of import path issues.
builtins.Derivative = sympy.Derivative
builtins.symbols = sympy.symbols
builtins.exp = sympy.exp # Common in FRB/US models
builtins.log = sympy.log    


os.makedirs("results", exist_ok=True)
os.makedirs("external_data", exist_ok=True)

# 1. XML AUTOPSY & REPAIR
model_xml = "models/model.xml"
ghost_val = "4.52193548387097"

print(f"🕵️ Scanning {model_xml} for structural anomalies...")
tree = ET.parse(model_xml)
root = tree.getroot()

# Search for any tag or attribute that contains our ghost number
found = False
for elem in root.iter():
    # Check if the ghost is in the tag text or any attribute
    if ghost_val in (elem.text or "") or any(ghost_val in str(v) for v in elem.attrib.values()):
        print(f"🎯 Found ghost in element: {elem.tag} | Attribs: {elem.attrib}")
        # If it's a variable name, change it to a safe string
        if elem.get('name') == ghost_val:
            elem.set('name', 'GHOST_FIXED')
            found = True

if found:
    print("🩹 Patching XML and saving to models/model_fixed.xml")
    tree.write("models/model_fixed.xml")
    model_to_load = "models/model_fixed.xml"
else:
    print("ghost not found in literal XML strings. Using original model.")
    model_to_load = model_xml

# 2. LOAD DATA
data = load_data("data/LONGBASE.TXT")
data.columns = [str(c).strip().lower() for c in data.columns]
if 'dmptmax' not in data.columns:
    data['dmptmax'] = 0.0
# Ensure our fixed variable exists in data if we renamed it
if found:
    data['ghost_fixed'] = 4.52193548387097

# 3. SOLVE
try:
    frbus = Frbus(model_to_load)
    print("🚀 Executing solve...")
    baseline_with_adds = frbus.init_trac("2023Q1", "2030Q4", data)
    sim = frbus.solve("2023Q1", "2030Q4", baseline_with_adds)
    sim.to_csv("results/output.csv")
    print("✨ Success!")
except Exception as e:
    print(f"❌ Failure: {e}")