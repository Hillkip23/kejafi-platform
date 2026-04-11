# -*- coding: utf-8 -*-
"""
Kejafi Single-Asset Tokenization Platform
Stage 2: Select a property, run valuation with metro fundamentals, publish to API.
"""

import math
import os
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import requests

from metro_lab_core import build_metro_profile, load_zori

# =========================================================
# UI & Utility Functions
# =========================================================

def apply_custom_styling():
    st.markdown("""
    <style>
    div[data-testid="stMetric"] {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stButton button {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 8px 24px;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    .stAlert {
        border-radius: 10px;
    }
    code {
        background-color: #1a1a2e;
        color: #00ff88;
        padding: 2px 6px;
        border-radius: 4px;
    }
    </style>
    """, unsafe_allow_html=True)

# =========================================================
# Setup
# =========================================================

st.set_page_config(page_title="Kejafi Single-Asset Tokenization", layout="wide")

BASE_DIR = Path(__file__).resolve().parent
API_URL = os.getenv("KEJAFI_API_URL", "http://127.0.0.1:8000")
FIG_DIR = BASE_DIR / "figures"
FIG_DIR.mkdir(exist_ok=True)

apply_custom_styling()

# =========================================================
# Deployed Contract Addresses (Sepolia)
# =========================================================

POOL_ADDRESS = "0x0Bf78f76c86153E433dAA5Ac6A88453D30968e27"
FINE5_ADDRESS = "0x0FB987BEE67FD839cb1158B0712d5e4Be483dd2E"
FINE6_ADDRESS = "0xe051C1eA47b246c79f3bac4e58E459cF2Aa20692"
CHAIN_ID = 11155111

# =========================================================
# API Health Check
# =========================================================

def check_api_health():
    try:
        response = requests.get(f"{API_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

# =========================================================
# Metro Mapping
# =========================================================

@st.cache_data
def resolve_metro_label_for_property(raw_metro_label: str) -> str:
    zori_df = load_zori()
    if (zori_df["RegionName"] == raw_metro_label).any():
        return raw_metro_label
    base = raw_metro_label.split(",")[0].split("\u2013")[0].split("-")[0].strip()
    candidates = zori_df[zori_df["RegionName"].str.contains(base, na=False)]
    if not candidates.empty:
        if "RegionType" in candidates.columns:
            msa_rows = candidates[candidates["RegionType"].astype(str).str.lower().str.contains("msa")]
            if not msa_rows.empty:
                return msa_rows["RegionName"].iloc[0]
        return candidates["RegionName"].iloc[0]
    return raw_metro_label

# =========================================================
# IRR Solver
# =========================================================

def compute_irr(cash_flows: List[float], guess: float = 0.10) -> float:
    if len(cash_flows) < 2:
        return 0.0
    rate = guess
    for _ in range(1000):
        npv = sum(cf / (1 + rate) ** t for t, cf in enumerate(cash_flows))
        dnpv = sum(-t * cf / (1 + rate) ** (t + 1) for t, cf in enumerate(cash_flows) if t > 0)
        if abs(dnpv) < 1e-12:
            break
        new_rate = rate - npv / dnpv
        if abs(new_rate - rate) < 1e-8:
            rate = new_rate
            break
        rate = new_rate
    if not (-0.5 < rate < 5.0):
        total_out = abs(cash_flows[0])
        total_in = sum(cf for cf in cash_flows[1:] if cf > 0)
        n = len(cash_flows) - 1
        rate = (total_in / max(total_out, 1e-6)) ** (1 / max(n, 1)) - 1
    return float(rate)

# =========================================================
# Property Database
# =========================================================

EXAMPLE_PROPERTIES = {
    "charlotte_mfk_001": {
        "address": "1421 N Caldwell St, Charlotte, NC 28206",
        "county": "Mecklenburg County, NC",
        "metro": "Charlotte-Concord-Gastonia, NC-SC",
        "property_type": "Multifamily",
        "units": 4,
        "beds": 2,
        "baths": 2,
        "sqft": 3200,
        "year_built": 2018,
        "lot_size": 0.25,
        "list_price": 685000,
        "current_rent": 4800,
        "market_rent": 5200,
        "occupancy": 1.0,
        "property_taxes": 4200,
        "insurance": 2400,
        "maintenance_reserve": 3000,
        "management_fee": 0.08,
        "photos": [],
        "walk_score": 78,
        "transit_score": 65,
        "school_rating": 7,
        "crime_index": "B-",
        "token_symbol": "FINE5",
        "token_address": FINE5_ADDRESS,
        "description": "Modern 4-unit multifamily in NoDa arts district. Fully occupied, recent renovation, strong rental demand.",
    },
    "austin_downtown_003": {
        "address": "1101 E 5th St, Austin, TX 78702",
        "county": "Travis County, TX",
        "metro": "Austin-Round Rock-Georgetown, TX",
        "property_type": "Multifamily",
        "units": 8,
        "beds": 1,
        "baths": 1,
        "sqft": 5600,
        "year_built": 2020,
        "lot_size": 0.45,
        "list_price": 1250000,
        "current_rent": 9600,
        "market_rent": 10400,
        "occupancy": 0.98,
        "property_taxes": 7200,
        "insurance": 3800,
        "maintenance_reserve": 5000,
        "management_fee": 0.08,
        "photos": [],
        "walk_score": 90,
        "transit_score": 70,
        "school_rating": 9,
        "crime_index": "B+",
        "token_symbol": "FINE6",
        "token_address": FINE6_ADDRESS,
        "description": "Luxury 8-unit building in downtown Austin. Strong tech-driven rental demand.",
    },
}

# =========================================================
# Valuation Engine
# =========================================================

@dataclass
class ValuationResult:
    list_price: float
    gross_rent: float
    noi: float
    cap_rate: float
    value_income: float
    value_per_door: float
    cash_on_cash: float
    irr_projected: float
    equity_multiple: float

def cap_rate_from_metro(prop: Dict, market: Dict) -> float:
    base = 0.055
    metro = prop["metro"]
    if "Miami" in metro:
        base = 0.050
    elif "Austin" in metro:
        base = 0.045
    elif "Charlotte" in metro:
        base = 0.055
    bucket = (market.get("supply_bucket") or "").lower()
    pci = market.get("pci_2023")
    if bucket == "very inelastic":
        base -= 0.0035
    elif bucket == "inelastic":
        base -= 0.0025
    elif bucket == "elastic":
        base += 0.0015
    us_metro_pci = 72275.0
    if pci is not None:
        rel = (pci - us_metro_pci) / us_metro_pci
        base -= 0.002 * float(np.clip(rel, -0.3, 0.3))
    return max(0.03, min(base, 0.09))

class PropertyValuation:
    def __init__(self, property_data: Dict, market_data: Dict):
        self.prop = property_data
        self.market = market_data

    def calculate_noi(self, use_market_rent: bool = False) -> float:
        monthly_rent = self.prop["market_rent"] if use_market_rent else self.prop["current_rent"]
        annual_rent = monthly_rent * 12 * self.prop["occupancy"]
        management = annual_rent * self.prop["management_fee"]
        opex = self.prop["property_taxes"] + self.prop["insurance"] + self.prop["maintenance_reserve"] + management
        return annual_rent - opex

    def full_valuation(self, leverage: float = 0.65, interest_rate: float = 0.075, hold_period: int = 5) -> ValuationResult:
        noi_stabilized = self.calculate_noi(use_market_rent=True)
        cap_rate = cap_rate_from_metro(self.prop, self.market)
        value_income = noi_stabilized / cap_rate
        value_per_door = value_income / self.prop["units"]
        loan_amount = self.prop["list_price"] * leverage
        equity = self.prop["list_price"] - loan_amount
        annual_debt_service = loan_amount * interest_rate
        zori_yoy = self.market["yoy_rent_growth"]
        pop_g = self.market.get("pop_growth")
        growth_adj = 0.0
        if pop_g is not None:
            if pop_g > 0.08:
                growth_adj = 0.01
            elif pop_g < 0:
                growth_adj = -0.01
        growth = max(-0.02, zori_yoy + growth_adj)
        annual_cash_flows = []
        for year in range(1, hold_period + 1):
            noi_growth = noi_stabilized * ((1 + growth) ** year)
            cf = noi_growth - annual_debt_service
            annual_cash_flows.append(cf)
        exit_noi = noi_stabilized * ((1 + growth) ** hold_period)
        exit_cap = cap_rate + 0.005
        exit_value = exit_noi / exit_cap
        exit_equity = exit_value - loan_amount
        terminal_cash_flows = annual_cash_flows[:-1] + [annual_cash_flows[-1] + exit_equity]
        total_cash = sum(annual_cash_flows) + exit_equity
        equity_multiple = total_cash / max(equity, 1e-6)
        irr_cash_flows = [-equity] + terminal_cash_flows
        irr = compute_irr(irr_cash_flows)
        cash_on_cash = annual_cash_flows[0] / max(equity, 1e-6)
        return ValuationResult(
            list_price=self.prop["list_price"],
            gross_rent=self.prop["current_rent"] * 12,
            noi=noi_stabilized,
            cap_rate=cap_rate,
            value_income=value_income,
            value_per_door=value_per_door,
            cash_on_cash=cash_on_cash,
            irr_projected=irr,
            equity_multiple=equity_multiple,
        )

# =========================================================
# API Publish Helper
# =========================================================

def _coerce(value, default=0.0):
    return value if value is not None else default

def push_property_to_api(prop_id: str, valuation: ValuationResult, market: Dict, prop: Dict):
    tokenized_equity_fraction = 0.8
    total_supply = 100_000
    nav_total = valuation.value_income * tokenized_equity_fraction
    nav_per_token = nav_total / total_supply if total_supply > 0 else 0.0
    initial_price = nav_per_token
    seed_tokens = int(total_supply * 0.2)
    seed_quote = seed_tokens * initial_price
    token_symbol = prop.get("token_symbol", "FINE5")
    token_address = prop.get("token_address", FINE5_ADDRESS)
    payload = {
        "id": prop_id,
        "address": prop["address"],
        "county": prop["county"],
        "metro": prop["metro"],
        "list_price": valuation.list_price,
        "noi": valuation.noi,
        "cap_rate": valuation.cap_rate,
        "irr": valuation.irr_projected,
        "equity_multiple": valuation.equity_multiple,
        "pci_2023": _coerce(market.get("pci_2023"), 0.0),
        "pop_growth": _coerce(market.get("pop_growth"), 0.0),
        "metro_elasticity": _coerce(market.get("metro_elasticity"), 0.0),
        "supply_bucket": market.get("supply_bucket") or "unknown",
        "risk_score": _coerce(market.get("risk_score"), 0.0),
        "risk_bucket": market.get("risk_bucket") or "unknown",
        "token_symbol": token_symbol,
        "token_price": initial_price,
        "total_supply": total_supply,
        "lockup_months": 12,
        "nav_total": nav_total,
        "nav_per_token": nav_per_token,
        "nav_currency": "USD",
        "amm": "uniswap_v3",
        "quote_asset": "USDC",
        "initial_price": initial_price,
        "seed_token_amount": seed_tokens,
        "seed_quote_amount": seed_quote,
        "fee_tier": 0.003,
        "price_range_low": initial_price * 0.85,
        "price_range_high": initial_price * 1.15,
        "token_address": token_address,
        "chain_id": CHAIN_ID,
        "pool_address": POOL_ADDRESS,
    }
    try:
        r = requests.post(f"{API_URL}/properties/", json=payload, timeout=10,
                         headers={"X-API-Key": os.environ.get("KEJAFI_PROD_KEY", "prod_key_placeholder")})
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        raise Exception(f"Cannot connect to API at {API_URL}. Is the FastAPI server running?")
    except requests.exceptions.Timeout:
        raise Exception("API request timed out after 10 seconds.")
    except requests.exceptions.HTTPError as e:
        raise Exception(f"API returned error: {e.response.status_code} - {e.response.text}")

# =========================================================
# Main UI
# =========================================================

st.title("🏠 Kejafi Single-Asset Tokenization Platform")
st.markdown("**Stage 2: Select a property, run valuation with metro fundamentals, publish to marketplace API.**")

with st.sidebar:
    st.header("⚙️ Settings & Tips")
    with st.expander("⌨️ Keyboard Shortcuts"):
        st.markdown("- `Ctrl+R` - Run Valuation\n- `Ctrl+P` - Publish to API\n- `?` - Show this help")
    with st.expander("💡 Pro Tips"):
        st.markdown("- **Import from Stage 1** for accurate metro data\n- **Adjust leverage** to see impact on returns\n- **Check API health** before publishing")
    with st.expander("🔗 Quick Links"):
        st.markdown(f"- [Pool on Etherscan](https://sepolia.etherscan.io/address/{POOL_ADDRESS})\n- [FINE5 Token](https://sepolia.etherscan.io/address/{FINE5_ADDRESS})\n- [FINE6 Token](https://sepolia.etherscan.io/address/{FINE6_ADDRESS})")

# Step 1: Select Property
st.header("Step 1: Select Property")
col1, col2 = st.columns([1, 2])
with col1:
    selected_key = st.selectbox("Available Properties", list(EXAMPLE_PROPERTIES.keys()),
        format_func=lambda x: f"{EXAMPLE_PROPERTIES[x]['address'][:30]}... ({EXAMPLE_PROPERTIES[x]['property_type']})")
    prop = EXAMPLE_PROPERTIES[selected_key]
    st.subheader("Property Details")
    st.write(f"**{prop['address']}**")
    st.write(f"County: {prop['county']}")
    st.write(f"Type: {prop['property_type']}")
    st.write(f"Units: {prop['units']}")
    st.write(f"SQFT: {prop['sqft']:,}")
    st.write(f"Year Built: {prop['year_built']}")
    st.metric("List Price", f"${prop['list_price']:,.0f}")
    st.metric("Current Monthly Rent", f"${prop['current_rent']:,.0f}")
    st.metric("Market Monthly Rent", f"${prop['market_rent']:,.0f}")
    st.metric("Token Symbol", prop.get("token_symbol", "N/A"))
    st.code(prop.get("token_address", "No address"))

with col2:
    st.subheader("Metro fundamentals & risk (from Stage 1)")
    st.info(prop["description"])
    zori_region_name = resolve_metro_label_for_property(prop["metro"])
    st.caption(f"Using ZORI RegionName: **{zori_region_name}**")
    try:
        metro_profile = build_metro_profile(zori_region_name)
    except:
        metro_profile = None
    if metro_profile is None:
        market = {"yoy_rent_growth": 0.03, "rent_volatility": 0.08, "trend_label": "stable", "pci_2023": None,
                  "metro_elasticity": None, "supply_bucket": None, "pop_growth": None, "risk_score": 75.0, "risk_bucket": "Moderate"}
    else:
        market = {"yoy_rent_growth": metro_profile["yoy_rent_growth"], "rent_volatility": metro_profile["rent_volatility"],
                  "trend_label": metro_profile["trend_label"], "pci_2023": metro_profile["pci_2023"],
                  "metro_elasticity": metro_profile["metro_elasticity"], "supply_bucket": metro_profile["supply_bucket"],
                  "pop_growth": metro_profile["pop_growth"], "risk_score": metro_profile["risk_score"], "risk_bucket": metro_profile["risk_bucket"]}
    
    c1, c2c, c3 = st.columns(3)
    c1.metric("Rent growth (YoY)", f"{market['yoy_rent_growth']*100:.1f}%", delta=market["trend_label"])
    c2c.metric("Rent volatility", f"{market['rent_volatility']*100:.1f}%")
    c3.metric("Walk Score", prop["walk_score"])
    c4, c5, c6 = st.columns(3)
    c4.metric("Metro PCI", f"${market['pci_2023']:,.0f}" if market["pci_2023"] else "n/a")
    c5.metric("Housing elasticity", f"{market['metro_elasticity']:.2f}" if market["metro_elasticity"] else "n/a", delta=market.get("supply_bucket", ""))
    c6.metric("Pop growth", f"{market['pop_growth']*100:.1f}%" if market["pop_growth"] else "n/a")
    r1, r2 = st.columns(2)
    with r1:
        st.metric("Kejafi risk score", f"{market['risk_score']:.0f}/100", delta=market["risk_bucket"])
    
    st.subheader("🔗 On-Chain Contract Info")
    st.success(f"**Pool Address:** `{POOL_ADDRESS[:10]}...{POOL_ADDRESS[-8:]}`")
    st.success(f"**Chain:** Sepolia (ID: {CHAIN_ID})")
    st.info(f"[View on Etherscan](https://sepolia.etherscan.io/address/{POOL_ADDRESS})")

# Step 2: Valuation
st.header("Step 2: Valuation & Underwriting")
col_v1, col_v2, col_v3 = st.columns(3)
with col_v1:
    leverage = st.slider("Leverage (LTV)", 0.0, 0.80, 0.65, 0.05)
with col_v2:
    interest_rate = st.slider("Interest Rate", 0.04, 0.12, 0.075, 0.005)
with col_v3:
    hold_period = st.slider("Hold Period (years)", 3, 10, 5, 1)

if st.button("🚀 Run Valuation", type="primary"):
    with st.spinner("Running valuation simulation..."):
        val_engine = PropertyValuation(prop, market)
        valuation = val_engine.full_valuation(leverage, interest_rate, hold_period)
        st.session_state["stage2_valuation"] = valuation
        st.session_state["stage2_property"] = prop
        st.session_state["stage2_market"] = market
        st.success("✅ Valuation complete!")
        
        col_r1, col_r2, col_r3, col_r4 = st.columns(4)
        col_r1.metric("Stabilized NOI", f"${valuation.noi:,.0f}")
        col_r2.metric("Value per door", f"${valuation.value_per_door:,.0f}")
        col_r3.metric("Cash-on-cash", f"{valuation.cash_on_cash*100:.1f}%")
        col_r4.metric("Projected IRR", f"{valuation.irr_projected*100:.1f}%")
        st.markdown(f"**Cap rate drivers:** Supply bucket ({market.get('supply_bucket', 'n/a')}) and PCI ${market.get('pci_2023') or 0:,.0f} shift the base cap rate to **{valuation.cap_rate*100:.2f}%**.")
        
        st.subheader("Valuation vs. list price")
        fig, ax = plt.subplots(figsize=(10, 4))
        categories = ["List price", "Income value", "Value/door × units"]
        values = [valuation.list_price / 1000, valuation.value_income / 1000, valuation.value_per_door * prop["units"] / 1000]
        colors = ["red" if values[0] > values[1] else "green", "blue", "gray"]
        bars = ax.bar(categories, values, color=colors, alpha=0.7)
        ax.set_ylabel("Value ($K)")
        ax.set_title("Valuation comparison")
        for bar, val_ in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2.0, bar.get_height() + 5, f"${val_:.0f}K", ha="center", va="bottom", fontsize=10)
        st.pyplot(fig)
        
        st.subheader("📊 Export Results")
        col_exp1, col_exp2 = st.columns(2)
        with col_exp1:
            export_data = {"property": prop, "valuation": {"list_price": valuation.list_price, "noi": valuation.noi,
                "cap_rate": valuation.cap_rate, "irr": valuation.irr_projected, "cash_on_cash": valuation.cash_on_cash,
                "equity_multiple": valuation.equity_multiple, "value_income": valuation.value_income, "value_per_door": valuation.value_per_door},
                "market": market, "timestamp": datetime.now().isoformat()}
            st.download_button("📥 Download JSON", data=json.dumps(export_data, indent=2, default=str),
                file_name=f"valuation_{selected_key}.json", mime="application/json", key="export_json")
        with col_exp2:
            metrics_df = pd.DataFrame([{"Metric": "List Price", "Value": valuation.list_price},
                {"Metric": "NOI", "Value": valuation.noi}, {"Metric": "Cap Rate", "Value": f"{valuation.cap_rate*100:.2f}%"},
                {"Metric": "IRR", "Value": f"{valuation.irr_projected*100:.1f}%"},
                {"Metric": "Cash-on-Cash", "Value": f"{valuation.cash_on_cash*100:.1f}%"},
                {"Metric": "Equity Multiple", "Value": f"{valuation.equity_multiple:.2f}x"}])
            st.download_button("📥 Download CSV", data=metrics_df.to_csv(index=False).encode('utf-8'),
                file_name=f"valuation_metrics_{selected_key}.csv", mime="text/csv", key="export_csv")

# Step 3: Publish to API
if "stage2_valuation" in st.session_state:
    st.header("Step 3: Publish to Marketplace API")
    st.markdown("Pushes property object to the FastAPI backend for the investor frontend.")
    api_healthy = check_api_health()
    if api_healthy:
        st.success("✅ API server is running")
    else:
        st.warning("⚠️ API server is not running")
        st.markdown("**To start API:** `python backend.py`")
    if st.button("📡 Publish to API", type="primary"):
        if not api_healthy:
            st.error("Cannot publish: API server is not running")
        else:
            try:
                with st.spinner("Publishing to API..."):
                    res = push_property_to_api(selected_key, st.session_state["stage2_valuation"],
                        st.session_state["stage2_market"], st.session_state["stage2_property"])
                st.success("✅ Published to API successfully!")
                with st.expander("📋 Published Data"):
                    st.json(res)
                st.info(f"🔗 View on Etherscan: [Pool Contract](https://sepolia.etherscan.io/address/{POOL_ADDRESS})")
            except Exception as e:
                st.error(f"Failed to publish: {e}")

st.markdown("---")
st.caption(f"Kejafi Single-Asset Tokenization | Stage 2 | Pool: {POOL_ADDRESS[:10]}... | Chain: Sepolia ({CHAIN_ID})")
