import os
import sys
import re 


# 1. FORCE THE ENVIRONMENT (Before any other imports)
try:
    import numpy as np
    import sympy
    import scipy
    import builtins
    import pyfrbus.symbolic
    builtins.Derivative = sympy.Derivative
    builtins.symbols = sympy.symbols
    builtins.exp = sympy.exp # Common in FRB/US models
    builtins.log = sympy.log
    print(f"✅ Environment Check: NumPy {np.__version__} is active.")
except ImportError as e:
    print(f"🚨 CRITICAL MISSING DEPENDENCY: {e}")
    # In a containerized env, we want to fail fast if the base image is broken
    sys.exit(1)

# 2. THE PATCH (Our safety net for the specific ghost value)

os.makedirs("results", exist_ok=True)
os.makedirs("external_data", exist_ok=True)

try:
    # 1. FORCE THE INNER PATH
    sys.path.insert(0, "/home/app/pyfrbus/pyfrbus")
    
    import lexing
    import symbolic
    from frbus import Frbus
    from load_data import load_data
    
    print(f"✅ Lexer found at: {lexing.__file__}")

    # 2. THE LEXER GUARD
    # We intercept the function that identifies symbols.
    # If it sees a string that starts with a number, we force it to be a 'Number' type.
    if hasattr(lexing, 'get_symbols'):
        original_get_symbols = lexing.get_symbols
        def patched_get_symbols(expr_str):
            symbols = original_get_symbols(expr_str)
            # Filter out anything that looks like a float/number
            safe_symbols = [s for s in symbols if not s[0].isdigit()]
            return safe_symbols
        lexing.get_symbols = patched_get_symbols
        print("🛡️ Lexer Symbol-Guard active. Numeric 'variables' will be blocked.")

    # 3. THE SYMBOLIC BACKSTOP
    # Just in case, we tell SymEngine's wrapper to return 0 for any numeric derivative
    original_diff = symbolic.take_symengine_partial
    def patched_diff(eq, w_resp_to, data_hash):
        if str(w_resp_to)[0].isdigit():
            return "0"
        return original_diff(eq, w_resp_to, data_hash)
    symbolic.take_symengine_partial = patched_diff

    # 4. RUN SOLVE
    data = load_data("data/LONGBASE.TXT")
    data.columns = [str(col).strip().lower() for col in data.columns]
    
    frbus = Frbus("models/model.xml")
    
    print("🚀 Running solver (Build #936)...")
    baseline = frbus.init_trac("2023Q1", "2030Q4", data)
    sim = frbus.solve("2023Q1", "2030Q4", baseline)
    
    sim.to_csv("results/output.csv")
    print("✨ SUCCESS!")

except Exception as e:
    print(f"❌ FATAL: {e}")
    with open("external_data/failure_log.txt", "w") as f:
        f.write(str(e))
    sys.exit(1)