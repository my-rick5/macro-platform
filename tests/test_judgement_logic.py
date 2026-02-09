import pandas as pd
import pytest

def apply_alert_logic(df, threshold=0.5):
    """Replicates the logic inside engine.py for testing"""
    df['judgment_alert'] = df['LUR_trac'].apply(
        lambda x: '🚨 HIGH JUDGMENT' if abs(x) > threshold else '✅ MODEL DRIVEN'
    )
    return df

def test_alert_thresholds():
    # Setup mock data: 0.1 (Low), 0.6 (High Positive), -0.7 (High Negative)
    mock_data = pd.DataFrame({
        'LUR_trac': [0.1, 0.6, -0.7, 0.49]
    })
    
    result = apply_alert_logic(mock_data)
    
    # 1. Test low values
    assert result.loc[0, 'judgment_alert'] == '✅ MODEL DRIVEN'
    assert result.loc[3, 'judgment_alert'] == '✅ MODEL DRIVEN'
    
    # 2. Test high positive (Pessimism)
    assert result.loc[1, 'judgment_alert'] == '🚨 HIGH JUDGMENT'
    
    # 3. Test high negative (Optimism/Suppression)
    assert result.loc[2, 'judgment_alert'] == '🚨 HIGH JUDGMENT'

def test_empty_dataframe():
    """Ensure the logic doesn't crash on an empty result set"""
    empty_df = pd.DataFrame(columns=['LUR_trac'])
    try:
        apply_alert_logic(empty_df)
    except Exception as e:
        pytest.fail(f"Alert logic crashed on empty DataFrame: {e}")import pandas as pd
import pytest

def apply_alert_logic(df, threshold=0.5):
    """Replicates the logic inside engine.py for testing"""
    df['judgment_alert'] = df['LUR_trac'].apply(
        lambda x: '🚨 HIGH JUDGMENT' if abs(x) > threshold else '✅ MODEL DRIVEN'
    )
    return df

def test_alert_thresholds():
    # Setup mock data: 0.1 (Low), 0.6 (High Positive), -0.7 (High Negative)
    mock_data = pd.DataFrame({
        'LUR_trac': [0.1, 0.6, -0.7, 0.49]
    })
    
    result = apply_alert_logic(mock_data)
    
    # 1. Test low values
    assert result.loc[0, 'judgment_alert'] == '✅ MODEL DRIVEN'
    assert result.loc[3, 'judgment_alert'] == '✅ MODEL DRIVEN'
    
    # 2. Test high positive (Pessimism)
    assert result.loc[1, 'judgment_alert'] == '🚨 HIGH JUDGMENT'
    
    # 3. Test high negative (Optimism/Suppression)
    assert result.loc[2, 'judgment_alert'] == '🚨 HIGH JUDGMENT'

def test_empty_dataframe():
    """Ensure the logic doesn't crash on an empty result set"""
    empty_df = pd.DataFrame(columns=['LUR_trac'])
    try:
        apply_alert_logic(empty_df)
    except Exception as e:
        pytest.fail(f"Alert logic crashed on empty DataFrame: {e}")import pandas as pd
import pytest

def apply_alert_logic(df, threshold=0.5):
    """Replicates the logic inside engine.py for testing"""
    df['judgment_alert'] = df['LUR_trac'].apply(
        lambda x: '🚨 HIGH JUDGMENT' if abs(x) > threshold else '✅ MODEL DRIVEN'
    )
    return df

def test_alert_thresholds():
    # Setup mock data: 0.1 (Low), 0.6 (High Positive), -0.7 (High Negative)
    mock_data = pd.DataFrame({
        'LUR_trac': [0.1, 0.6, -0.7, 0.49]
    })
    
    result = apply_alert_logic(mock_data)
    
    # 1. Test low values
    assert result.loc[0, 'judgment_alert'] == '✅ MODEL DRIVEN'
    assert result.loc[3, 'judgment_alert'] == '✅ MODEL DRIVEN'
    
    # 2. Test high positive (Pessimism)
    assert result.loc[1, 'judgment_alert'] == '🚨 HIGH JUDGMENT'
    
    # 3. Test high negative (Optimism/Suppression)
    assert result.loc[2, 'judgment_alert'] == '🚨 HIGH JUDGMENT'

def test_empty_dataframe():
    """Ensure the logic doesn't crash on an empty result set"""
    empty_df = pd.DataFrame(columns=['LUR_trac'])
    try:
        apply_alert_logic(empty_df)
    except Exception as e:
        pytest.fail(f"Alert logic crashed on empty DataFrame: {e}")import pandas as pd
import pytest

def apply_alert_logic(df, threshold=0.5):
    """Replicates the logic inside engine.py for testing"""
    df['judgment_alert'] = df['LUR_trac'].apply(
        lambda x: '🚨 HIGH JUDGMENT' if abs(x) > threshold else '✅ MODEL DRIVEN'
    )
    return df

def test_alert_thresholds():
    # Setup mock data: 0.1 (Low), 0.6 (High Positive), -0.7 (High Negative)
    mock_data = pd.DataFrame({
        'LUR_trac': [0.1, 0.6, -0.7, 0.49]
    })
    
    result = apply_alert_logic(mock_data)
    
    # 1. Test low values
    assert result.loc[0, 'judgment_alert'] == '✅ MODEL DRIVEN'
    assert result.loc[3, 'judgment_alert'] == '✅ MODEL DRIVEN'
    
    # 2. Test high positive (Pessimism)
    assert result.loc[1, 'judgment_alert'] == '🚨 HIGH JUDGMENT'
    
    # 3. Test high negative (Optimism/Suppression)
    assert result.loc[2, 'judgment_alert'] == '🚨 HIGH JUDGMENT'

def test_empty_dataframe():
    """Ensure the logic doesn't crash on an empty result set"""
    empty_df = pd.DataFrame(columns=['LUR_trac'])
    try:
        apply_alert_logic(empty_df)
    except Exception as e:
        pytest.fail(f"Alert logic crashed on empty DataFrame: {e}")import pandas as pd
import pytest

def apply_alert_logic(df, threshold=0.5):
    """Replicates the logic inside engine.py for testing"""
    df['judgment_alert'] = df['LUR_trac'].apply(
        lambda x: '🚨 HIGH JUDGMENT' if abs(x) > threshold else '✅ MODEL DRIVEN'
    )
    return df

def test_alert_thresholds():
    # Setup mock data: 0.1 (Low), 0.6 (High Positive), -0.7 (High Negative)
    mock_data = pd.DataFrame({
        'LUR_trac': [0.1, 0.6, -0.7, 0.49]
    })
    
    result = apply_alert_logic(mock_data)
    
    # 1. Test low values
    assert result.loc[0, 'judgment_alert'] == '✅ MODEL DRIVEN'
    assert result.loc[3, 'judgment_alert'] == '✅ MODEL DRIVEN'
    
    # 2. Test high positive (Pessimism)
    assert result.loc[1, 'judgment_alert'] == '🚨 HIGH JUDGMENT'
    
    # 3. Test high negative (Optimism/Suppression)
    assert result.loc[2, 'judgment_alert'] == '🚨 HIGH JUDGMENT'

def test_empty_dataframe():
    """Ensure the logic doesn't crash on an empty result set"""
    empty_df = pd.DataFrame(columns=['LUR_trac'])
    try:
        apply_alert_logic(empty_df)
    except Exception as e:
        pytest.fail(f"Alert logic crashed on empty DataFrame: {e}")import pandas as pd
import pytest

def apply_alert_logic(df, threshold=0.5):
    """Replicates the logic inside engine.py for testing"""
    df['judgment_alert'] = df['LUR_trac'].apply(
        lambda x: '🚨 HIGH JUDGMENT' if abs(x) > threshold else '✅ MODEL DRIVEN'
    )
    return df

def test_alert_thresholds():
    # Setup mock data: 0.1 (Low), 0.6 (High Positive), -0.7 (High Negative)
    mock_data = pd.DataFrame({
        'LUR_trac': [0.1, 0.6, -0.7, 0.49]
    })
    
    result = apply_alert_logic(mock_data)
    
    # 1. Test low values
    assert result.loc[0, 'judgment_alert'] == '✅ MODEL DRIVEN'
    assert result.loc[3, 'judgment_alert'] == '✅ MODEL DRIVEN'
    
    # 2. Test high positive (Pessimism)
    assert result.loc[1, 'judgment_alert'] == '🚨 HIGH JUDGMENT'
    
    # 3. Test high negative (Optimism/Suppression)
    assert result.loc[2, 'judgment_alert'] == '🚨 HIGH JUDGMENT'

def test_empty_dataframe():
    """Ensure the logic doesn't crash on an empty result set"""
    empty_df = pd.DataFrame(columns=['LUR_trac'])
    try:
        apply_alert_logic(empty_df)
    except Exception as e:
        pytest.fail(f"Alert logic crashed on empty DataFrame: {e}")import pandas as pd
import pytest

def apply_alert_logic(df, threshold=0.5):
    """Replicates the logic inside engine.py for testing"""
    df['judgment_alert'] = df['LUR_trac'].apply(
        lambda x: '🚨 HIGH JUDGMENT' if abs(x) > threshold else '✅ MODEL DRIVEN'
    )
    return df

def test_alert_thresholds():
    # Setup mock data: 0.1 (Low), 0.6 (High Positive), -0.7 (High Negative)
    mock_data = pd.DataFrame({
        'LUR_trac': [0.1, 0.6, -0.7, 0.49]
    })
    
    result = apply_alert_logic(mock_data)
    
    # 1. Test low values
    assert result.loc[0, 'judgment_alert'] == '✅ MODEL DRIVEN'
    assert result.loc[3, 'judgment_alert'] == '✅ MODEL DRIVEN'
    
    # 2. Test high positive (Pessimism)
    assert result.loc[1, 'judgment_alert'] == '🚨 HIGH JUDGMENT'
    
    # 3. Test high negative (Optimism/Suppression)
    assert result.loc[2, 'judgment_alert'] == '🚨 HIGH JUDGMENT'

def test_empty_dataframe():
    """Ensure the logic doesn't crash on an empty result set"""
    empty_df = pd.DataFrame(columns=['LUR_trac'])
    try:
        apply_alert_logic(empty_df)
    except Exception as e:
        pytest.fail(f"Alert logic crashed on empty DataFrame: {e}")import pandas as pd
import pytest

def apply_alert_logic(df, threshold=0.5):
    """Replicates the logic inside engine.py for testing"""
    df['judgment_alert'] = df['LUR_trac'].apply(
        lambda x: '🚨 HIGH JUDGMENT' if abs(x) > threshold else '✅ MODEL DRIVEN'
    )
    return df

def test_alert_thresholds():
    # Setup mock data: 0.1 (Low), 0.6 (High Positive), -0.7 (High Negative)
    mock_data = pd.DataFrame({
        'LUR_trac': [0.1, 0.6, -0.7, 0.49]
    })
    
    result = apply_alert_logic(mock_data)
    
    # 1. Test low values
    assert result.loc[0, 'judgment_alert'] == '✅ MODEL DRIVEN'
    assert result.loc[3, 'judgment_alert'] == '✅ MODEL DRIVEN'
    
    # 2. Test high positive (Pessimism)
    assert result.loc[1, 'judgment_alert'] == '🚨 HIGH JUDGMENT'
    
    # 3. Test high negative (Optimism/Suppression)
    assert result.loc[2, 'judgment_alert'] == '🚨 HIGH JUDGMENT'

def test_empty_dataframe():
    """Ensure the logic doesn't crash on an empty result set"""
    empty_df = pd.DataFrame(columns=['LUR_trac'])
    try:
        apply_alert_logic(empty_df)
    except Exception as e:
        pytest.fail(f"Alert logic crashed on empty DataFrame: {e}")import pandas as pd
import pytest

def apply_alert_logic(df, threshold=0.5):
    """Replicates the logic inside engine.py for testing"""
    df['judgment_alert'] = df['LUR_trac'].apply(
        lambda x: '🚨 HIGH JUDGMENT' if abs(x) > threshold else '✅ MODEL DRIVEN'
    )
    return df

def test_alert_thresholds():
    # Setup mock data: 0.1 (Low), 0.6 (High Positive), -0.7 (High Negative)
    mock_data = pd.DataFrame({
        'LUR_trac': [0.1, 0.6, -0.7, 0.49]
    })
    
    result = apply_alert_logic(mock_data)
    
    # 1. Test low values
    assert result.loc[0, 'judgment_alert'] == '✅ MODEL DRIVEN'
    assert result.loc[3, 'judgment_alert'] == '✅ MODEL DRIVEN'
    
    # 2. Test high positive (Pessimism)
    assert result.loc[1, 'judgment_alert'] == '🚨 HIGH JUDGMENT'
    
    # 3. Test high negative (Optimism/Suppression)
    assert result.loc[2, 'judgment_alert'] == '🚨 HIGH JUDGMENT'

def test_empty_dataframe():
    """Ensure the logic doesn't crash on an empty result set"""
    empty_df = pd.DataFrame(columns=['LUR_trac'])
    try:
        apply_alert_logic(empty_df)
    except Exception as e:
        pytest.fail(f"Alert logic crashed on empty DataFrame: {e}")
