import streamlit as st
import pandas as pd
import numpy as np
import pickle

st.set_page_config(page_title="MSU Football Analytics", layout="wide")

# ==============================================================================
# 🔒 SECURE PASSCODE GATEWAY
# ==============================================================================
st.sidebar.title("🔐 Program Security")
password_input = st.sidebar.text_input("Enter Staff Passcode", type="password")

# Set whatever password you want the coaching staff to use here
if password_input != "GoGreen2026": 
    st.title("🟢 Spartan Football Analytics Platform")
    st.info("Please enter the secure coaching staff credential in the sidebar to unlock the live EPA forecasting engine.")
    st.image("https://fssta.com", width=150) # Displays an MSU logo placeholder
    st.stop()  # 🛑 CRUCIAL: This halts the script immediately so no data or model loads
# ==============================================================================


# ==============================================================================
# 🏈 THE FULL MODEL DASHBOARD (Only runs if password is correct!)
# ==============================================================================
st.title("🟢 Spartan Real-Time Pre-Snap EPA Forecaster")
st.caption("Driven by Real PFF Play-by-Play Model Weights")

@st.cache_resource
def load_model_assets():
    with open("msu_formation_epa_model.pkl", "rb") as f:
        model = pickle.load(f)
    with open("model_columns.pkl", "rb") as f:
        model_columns = pickle.load(f)
    return model, model_columns

try:
    model, model_columns = load_model_assets()
    
    available_formations = sorted([col.replace("pff_OFFFORMATIONNAME_", "") for col in model_columns if "pff_OFFFORMATIONNAME_" in col])
    available_personnel = sorted([col.replace("pff_OFFPERSONNELBASIC_", "") for col in model_columns if "pff_OFFPERSONNELBASIC_" in col])
    available_coverage = sorted([col.replace("pff_PASSCOVERAGEBASIC_", "") for col in model_columns if "pff_PASSCOVERAGEBASIC_" in col])

    if not available_formations: available_formations = ["Spread", "Tight", "Heavy"]
    if not available_personnel: available_personnel = ["11", "12", "21"]
    if not available_coverage: available_coverage = ["Man", "Zone", "Quarters"]

    col_input, col_pred = st.columns(2)

    with col_input:
        st.header("📋 Pre-Snap Inputs")
        
        down = st.radio("Down", [1, 2, 3, 4], horizontal=True)
        distance = st.number_input("Distance to Go", min_value=1, max_value=99, value=10)
        yardline = st.slider("Distance to Goal Line (Yards)", 1, 99, 50)
        
        st.divider()
        
        off_formation = st.selectbox("Offensive Formation Name", available_formations)
        personnel = st.selectbox("Offensive Personnel Group", available_personnel)
        
        st.divider()
        
        box_count = st.slider("Defenders in Box", 3, 10, 6)
        shell = st.radio("Secondary Defensive Shell", available_coverage, horizontal=True)

    with col_pred:
        st.header("📊 Live Predictive Forecast")
        
        input_row = pd.DataFrame(0, index=[0], columns=model_columns)
        
        input_row['pff_DOWN'] = down
        input_row['pff_DISTANCE'] = distance
        input_row['pff_YARDSTOGOALLINE'] = yardline
        input_row['pff_NUMBOXPLAYERS'] = box_count
        
        form_col = f"pff_OFFFORMATIONNAME_{off_formation}"
        pers_col = f"pff_OFFPERSONNELBASIC_{personnel}"
        cov_col = f"pff_PASSCOVERAGEBASIC_{shell}"
        
        if form_col in input_row.columns: input_row[form_col] = 1
        if pers_col in input_row.columns: input_row[pers_col] = 1
        if cov_col in input_row.columns: input_row[cov_col] = 1
        
        predicted_epa = float(model.predict(input_row)[0])
        success_rate = int(min(max((predicted_epa + 0.25) * 100, 20), 85))

        kpi_1, kpi_2 = st.columns(2)
        if predicted_epa >= 0:
            kpi_1.metric(label="Predicted EPA/Play", value=f"+{predicted_epa:.3f}", delta="Advantage Offense")
        else:
            kpi_1.metric(label="Predicted EPA/Play", value=f"{predicted_epa:.3f}", delta="Advantage Defense", delta_color="inverse")
            
        kpi_2.metric(label="Play Success Probability", value=f"{success_rate}%")

        st.subheader("💡 Tactical Adjustments")
        if predicted_epa < 0:
            st.error(f"⚠️ Warning: Historical configurations map this as an inefficient matchup. Adjust formation spacing or check leverage ratios.")
        elif predicted_epa > 0.15:
            st.success(f"✅ Green Light: High offensive threshold calculated. Front or shell indicates a major efficiency ceiling.")
        else:
            st.info(f"⚡ Neutral Expectation: Baseline tactical efficiency. Success depends directly on player execution.")

except Exception as e:
    st.error(f"Error initializing assets: {e}")