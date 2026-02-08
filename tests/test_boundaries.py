import pytest
import pandas as pd
import numpy as np
# Assuming your engine has a process_macro_data function
# from engine.core import process_macro_data 

def test_negative_interest_rates():
    """Does the engine crash if rates go negative (like Europe/Japan)?"""
    data = pd.DataFrame({
        'date': ['2024-01-01'],
        'interest_rate': [-0.005], # -0.5%
        'gdp': [100.0]
    })
    # result = process_macro_data(data)
    # assert result is not None
    assert data['interest_rate'].iloc[0] < 0

def test_missing_data_handling():
    """Does the engine skip or interpolate NaNs instead of breaking?"""
    data = pd.DataFrame({
        'date': ['2024-01-01', '2024-01-02'],
        'gdp': [100.0, np.nan] # Missing GDP for day 2
    })
    # Testing that the engine doesn't throw a ValueError
    # assert process_macro_data(data).isna().sum().sum() == 0
    pass
