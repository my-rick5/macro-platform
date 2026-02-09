import pytest
import os
from pyfrbus.frbus import Frbus

# Path to the model file fetched in your Jenkins pipeline
MODEL_PATH = "models/model.xml"

def test_model_file_exists():
    """Verify that the Jenkins stage successfully fetched the model.xml."""
    assert os.path.exists(MODEL_PATH), f"❌ Critical Failure: {MODEL_PATH} not found. Check Jenkins Fetch stage."

def test_pyfrbus_parsing():
    """Verify that pyfrbus can initialize the model without syntax errors."""
    try:
        model = Frbus(MODEL_PATH)
        assert model is not None
    except Exception as e:
        pytest.fail(f"❌ pyfrbus failed to parse model.xml: {e}")

def test_required_variables():
    """Ensure the model contains the core variables for the 'Add Factor' calculation."""
    model = Frbus(MODEL_PATH)
    # These are the codes identified in the HTML docs
    required_vars = ['LUR', 'LEH', 'LF', 'XGAP']
    
    # model.endog is a list of all endogenous variables in the model
    missing = [var for var in required_vars if var not in model.endog and var not in model.exog]
    
    assert not missing, f"❌ Model missing critical variables: {missing}. Verify model.xml version."

def test_python_equation_mapping():
    """FRB/US XML files sometimes only contain EViews code. This checks for Python logic."""
    import xml.etree.ElementTree as ET
    tree = ET.parse(MODEL_PATH)
    root = tree.getroot()
    
    # Search for the python_equation tag which pyfrbus relies on
    py_eqs = root.findall(".//python_equation")
    assert len(py_eqs) > 0, "❌ model.xml contains no <python_equation> tags. pyfrbus cannot solve this file."

if __name__ == "__main__":
    # Allow manual running
    pytest.main([__file__])
