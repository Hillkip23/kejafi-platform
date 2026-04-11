# metro_lab_core.py - Local replacement for metro analysis functions
import pandas as pd
import numpy as np
from pathlib import Path
import streamlit as st

def load_zori():
    """Load Zillow Observed Rent Index data"""
    BASE_DIR = Path(__file__).resolve().parent
    ZORI_PATH = BASE_DIR / "data" / "Zillow_Observed_Rent_Index.csv"
    
    if not ZORI_PATH.exists():
        st.error(f"ZORI data not found at {ZORI_PATH}")
        return pd.DataFrame()
    
    df = pd.read_csv(ZORI_PATH)
    if len(df.columns) > 2 and df.iloc[0, 2] == "RegionName":
        df.columns = df.iloc[0]
        df = df.iloc[1:].reset_index(drop=True)
    return df

def build_metro_profile(metro_name: str) -> dict:
    """Build metro profile from ZORI data"""
    zori_df = load_zori()
    
    default_profile = {
        "yoy_rent_growth": 0.04,
        "rent_volatility": 0.08,
        "trend_label": "stable",
        "pci_2023": None,
        "metro_elasticity": 0.30,
        "supply_bucket": "neutral",
        "pop_growth": 0.05,
        "risk_score": 50.0,
        "risk_bucket": "Moderate",
    }
    
    if zori_df.empty:
        return default_profile
    
    # Find metro in data
    metro_row = zori_df[zori_df["RegionName"] == metro_name]
    if metro_row.empty:
        base = metro_name.split(",")[0].split("-")[0].strip()
        metro_row = zori_df[zori_df["RegionName"].str.contains(base, na=False)]
    
    if metro_row.empty:
        return default_profile
    
    # Extract time series
    date_cols = [c for c in metro_row.columns if str(c)[:4].isdigit()]
    if not date_cols:
        return default_profile
    
    values = metro_row[date_cols].iloc[0].astype(float).dropna()
    
    if len(values) < 12:
        return default_profile
    
    # Calculate metrics
    recent = values.iloc[-12:].mean()
    older = values.iloc[-24:-12].mean() if len(values) >= 24 else values.iloc[:12].mean()
    yoy_growth = (recent - older) / older if older > 0 else 0.04
    yoy_growth = max(-0.05, min(yoy_growth, 0.15))
    
    # Calculate volatility
    pct_changes = values.pct_change().dropna()
    volatility = float(pct_changes.std() * np.sqrt(12)) if len(pct_changes) > 0 else 0.08
    volatility = max(0.03, min(volatility, 0.25))
    
    # Determine trend
    if yoy_growth > 0.03:
        trend_label = "expanding"
    elif yoy_growth > 0:
        trend_label = "stable"
    else:
        trend_label = "contracting"
    
    # Elasticity based on metro
    elasticity_map = {
        "San Francisco": 0.08, "New York": 0.10, "Los Angeles": 0.12,
        "Miami": 0.15, "Seattle": 0.15, "Chicago": 0.22,
        "Charlotte": 0.35, "Atlanta": 0.38, "Nashville": 0.42,
        "Dallas": 0.45, "Austin": 0.48,
    }
    
    elasticity = 0.30
    for key, val in elasticity_map.items():
        if key in metro_name:
            elasticity = val
            break
    
    # Supply bucket
    if elasticity < 0.15:
        supply_bucket = "very inelastic"
    elif elasticity < 0.25:
        supply_bucket = "inelastic"
    elif elasticity > 0.40:
        supply_bucket = "elastic"
    else:
        supply_bucket = "neutral"
    
    # Risk score
    risk_score = 100 - (yoy_growth * 200 + (1 - volatility * 2) * 50)
    risk_score = max(0, min(100, risk_score))
    
    if risk_score > 70:
        risk_bucket = "Low"
    elif risk_score > 40:
        risk_bucket = "Moderate"
    else:
        risk_bucket = "High"
    
    return {
        "yoy_rent_growth": yoy_growth,
        "rent_volatility": volatility,
        "trend_label": trend_label,
        "pci_2023": None,
        "metro_elasticity": elasticity,
        "supply_bucket": supply_bucket,
        "pop_growth": 0.05,
        "risk_score": risk_score,
        "risk_bucket": risk_bucket,
    }