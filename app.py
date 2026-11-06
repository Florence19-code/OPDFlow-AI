
import streamlit as st
import pandas as pd
import joblib
import uuid
import qrcode
from io import BytesIO
from supabase import create_client
import plotly.express as px

# ---------------------------------
# PAGE CONFIGURATION
# ---------------------------------

st.set_page_config(
    page_title="OPDFlow AI",
    page_icon="🏥",
    layout="wide"
)
# ---------------------------------
# CUSTOM DASHBOARD DESIGN
# ---------------------------------

st.markdown("""
<style>

/* Overall page background */
.stApp {
    background: #F2F7FA;
}

/* Main dashboard content */
.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1400px;
}

/* Main content text and headings */
[data-testid="stAppViewContainer"] .main {
    background: #F2F7FA;
}

h1, h2, h3 {
    color: #173B57 !important;
    font-weight: 700 !important;
}

p, label, [data-testid="stMarkdownContainer"] {
    color: #29485D;
}

/* Metric cards */
[data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid #D8E6ED;
    padding: 18px;
    border-radius: 14px;
    box-shadow: 0 3px 12px rgba(23, 59, 87, 0.07);
}

/* Metric values and labels */
[data-testid="stMetricValue"] {
    color: #087E8B;
    font-weight: 750;
}
[data-testid="stMetricLabel"] {
    color: #526779;
}

/* Inputs and dropdowns */
.stTextInput input,
.stNumberInput input,
.stSelectbox div[data-baseweb="select"],
.stDateInput input,
.stTimeInput input,
.stTextArea textarea {
    border-radius: 10px;
    background-color: #FFFFFF;
}

/* Buttons */
.stButton button,
.stDownloadButton button {
    background-color: #087E8B;
    color: #FFFFFF;
    border: 1px solid #087E8B;
    border-radius: 10px;
    font-weight: 600;
    padding: 0.45rem 1rem;
    transition: all 0.2s ease;
}

.stButton button:hover,
.stDownloadButton button:hover {
    background-color: #173B57;
