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

# 1. THE LEXER REPAIR
# We intercept the string before it gets turned into a Symbol.
# We will search for that specific float string and replace it with a literal number
# so the symbolic engine never sees it as a 'Variable'.
ghost_val = "4.52193548387097"

original_lex = pyfrbus.lexing.lex_equation if hasattr(pyfrbus.lexing, 'lex_equation') else None

def patched_lex(eq_string, *args, **kwargs):
    # Forcibly clean the equation string of this specific float 'name'
    if ghost_val in eq_string:
        print(f"🩹 Lexer Patch: Neutralizing ghost in equation string...")
        # We wrap it in parentheses to ensure it's treated as a numeric literal
        eq_string = eq_string.replace(ghost_val, f"({ghost_val})")
    return original_lex(eq_string, *args, **kwargs)

if original_lex:
    pyfrbus.lexing.lex_equation = patched_lex
    print("🛡️ Lexer Patch Applied.")

# 2. DATA & SOLVE
data = load_data("data/LONGBASE.TXT")
data.columns = [str(c).strip().lower() for c in data.columns]

try:
    frbus = Frbus("models/model.xml")
    print("🚀 Attempting solve with Lexer Interception...")
    baseline_with_adds = frbus.init_trac("2023Q1", "2030Q4", data)
    sim = frbus.solve("2023Q1", "2030Q4", baseline_with_adds)
    sim.to_csv("results/output.csv")
    print("✨ Success!")
except Exception as e:
    print(f"❌ Failure: {e}")