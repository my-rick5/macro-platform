import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import gcsfs

# --- 1. CONFIG & STYLING ---
st.set_page_config(page_title="MacroFlow Terminal", layout="wide", page_icon="📈")

st.markdown("""
    <style>
    .metric-card { background-color: #1e1e1e; padding: 20px; border-radius: 10px; border: 1px solid #333; }
    .stInfo { background-color: #0e1117; border: 1px solid #2e3136; }
    </style>
""", unsafe_allow_html=True)

# --- 2. THE NUCLEAR DATA LOADER ---
@st.cache_data(ttl=60) # Short TTL to ensure we catch new runs
def load_versioned_data():
    """Reads the JSON pointer to find the actual unique run path."""
    try:
        fs = gcsfs.GCSFileSystem()
        pointer_dir = "gs://macro-engine-warehouse-macroflow-486515/factory/latest_run_path.json/"
        
        # List files in the pointer directory to find the actual JSON part
        files = fs.ls(pointer_dir)
        json_files = [f for f in files if f.endswith(".json")]
        
        if not json_files:
            return None, "No Pointer Found"

        # Read the path from the JSON pointer
        with fs.open(json_files[0]) as f:
            pointer_df = pd.read_json(f, lines=True)
            latest_path = pointer_df['latest_path'].iloc[0]
            run_id = pointer_df['run_id'].iloc[0]
            
        # Load the actual Parquet data from the unique path
        df = pd.read_parquet(latest_path)
        return df, f"RUN_{run_id}"
    except Exception as e:
        return None, f"Connection Error: {str(e)}"

# --- 3. DASHBOARD HEADER ---
st.title("📟 MacroFlow Factory Terminal")
data, run_status = load_versioned_data()

if data is not None:
    # Display the specific Run ID we are connected to (The Anti-Ghost Bar)
    st.info(f"🛰️ **System Status:** {run_status} | **Source:** Cloud Warehouse")
    
    # --- 4. TOP LEVEL METRICS ---
    vix_start = data['debug_vix_start'].iloc[0] if 'debug_vix_start' in data.columns else 17.95
    # Calculate Mean of the final horizon (Month 11)
    final_vix_mean = data[data['horizon'] == 11]['vix_value'].mean()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("VIX Ground Truth", f"{vix_start:.2f}", delta="Handshake Fixed")
    with col2:
        # If this is 9.04, we know we are still stuck; if >13.0, code is live!
        color = "normal" if final_vix_mean > 11 else "inverse"
        st.metric("Proj. VIX (12m Mean)", f"{final_vix_mean:.2f}", 
                  delta=f"{final_vix_mean - vix_start:.2f}", delta_color=color)
    with col3:
        st.metric("FFR Target", "4.50%", "Stable")
    with col4:
        st.metric("Engine Pulse", "🔥 Running" if final_vix_mean > 10 else "🧊 Flatlined")

    # --- 5. THE SIMULATION CLOUD ---
    st.subheader("📊 VIX Simulation Cloud (Scalar-Force Mode)")
    
    fig = go.Figure()
    
    # Plot a sample of 100 paths for performance
    sample_ids = data['sim_id'].unique()[:100]
    for sim_id in sample_ids:
        subset = data[data['sim_id'] == sim_id]
        fig.add_trace(go.Scatter(
            x=subset['horizon'], 
            y=subset['vix_value'],
            mode='lines',
            line=dict(width=1),
            opacity=0.3,
            showlegend=False,
            line_color='#00d4ff'
        ))

    # Plot the Mean Path in Gold
    mean_path = data.groupby('horizon')['vix_value'].mean()
    fig.add_trace(go.Scatter(
        x=mean_path.index, 
        y=mean_path.values,
        mode='lines',
        line=dict(color='#ffcc00', width=4),
        name='Projected Mean'
    ))

    fig.update_layout(
        template="plotly_dark",
        xaxis_title="Months (Horizon)",
        yaxis_title="VIX Level",
        yaxis=dict(range=[8, 30]), # Zoomed in to see the 13.0 floor
        margin=dict(l=0, r=0, t=0, b=0)
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- 6. UTILITIES ---
    with st.sidebar:
        st.header("Admin Controls")
        if st.button("🔄 Purge Cache & Re-Sync"):
            st.cache_data.clear()
            st.rerun()
        
        st.divider()
        st.write("**Model Parameters (Scalar Edition)**")
        st.write("- Persistence: 0.98")
        st.write("- Target Mean: 17.5")
        st.write("- Min Floor: 13.0")

else:
    st.warning("⚠️ Waiting for Factory Engine output... Check Dataproc Logs.")
    if st.button("Retry Connection"):
        st.rerun()