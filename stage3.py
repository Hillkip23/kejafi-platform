# stage3.py - Portfolio Management with API integration
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import defaultdict

import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import requests

import logging
logging.getLogger("tornado.application").setLevel(logging.ERROR)

# =========================================================
# Setup & Paths
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
STAGE1_OUTPUT_DIR = BASE_DIR / "stage1_output"
STAGE2_OUTPUT_DIR = BASE_DIR / "stage2_output"
STAGE3_OUTPUT_DIR = BASE_DIR / "stage3_output"
API_URL = os.getenv("KEJAFI_API_URL", "http://127.0.0.1:8000")

STAGE3_OUTPUT_DIR.mkdir(exist_ok=True)

st.set_page_config(
    page_title="Kejafi Portfolio Management",
    layout="wide",
    page_icon="??"
)

# =========================================================
# Contract Addresses
# =========================================================

POOL_ADDRESS = "0x0Bf78f76c86153E433dAA5Ac6A88453D30968e27"
FINE5_ADDRESS = "0x0FB987BEE67FD839cb1158B0712d5e4Be483dd2E"
FINE6_ADDRESS = "0xe051C1eA47b246c79f3bac4e58E459cF2Aa20692"
CHAIN_ID = 11155111

# =========================================================
# Data Models
# =========================================================

@dataclass
class PortfolioAsset:
    asset_id: str
    name: str
    property_type: str
    metro: str
    property_value: float
    token_price: float
    market_cap: float
    expected_return_1y: float
    expected_return_5y: float
    volatility: float
    var95: float
    sharpe_ratio: float
    max_drawdown: float
    total_supply: int
    management_fee: float
    performance_fee: float
    token_symbol: str
    token_address: str
    rent_growth: float
    rent_volatility: float
    supply_elasticity: float
    risk_score: float
    portfolio_weight: float = 0.0
    tokens_held: int = 0
    
    @property
    def value_held(self) -> float:
        return self.tokens_held * self.token_price


@dataclass
class Portfolio:
    assets: List[PortfolioAsset]
    name: str = "My Portfolio"
    created_date: datetime = field(default_factory=datetime.now)
    
    @property
    def total_value(self) -> float:
        return sum(a.value_held for a in self.assets)
    
    @property
    def num_assets(self) -> int:
        return len(self.assets)


# =========================================================
# Import Functions
# =========================================================

def fetch_properties_from_api() -> List[Dict]:
    """Fetch properties from the backend API"""
    try:
        response = requests.get(f"{API_URL}/properties", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except Exception as e:
        st.warning(f"Could not fetch from API: {e}")
        return []


def convert_api_property_to_asset(prop: Dict) -> PortfolioAsset:
    """Convert API property to PortfolioAsset"""
    # Determine token info
    token_symbol = prop.get("token_symbol", "FINE5")
    token_address = prop.get("token_address", FINE5_ADDRESS)
    
    # Estimate returns based on metro (simplified)
    expected_return = 0.10  # default 10%
    volatility = 0.15  # default 15%
    
    return PortfolioAsset(
        asset_id=prop.get("id", "unknown"),
        name=prop.get("address", "Unknown Property")[:40],
        property_type="Multifamily",
        metro=prop.get("metro", "Unknown"),
        property_value=prop.get("list_price", 0),
        token_price=prop.get("token_price", 25.0) if prop.get("token_price") else 25.0,
        market_cap=prop.get("list_price", 0),
        expected_return_1y=expected_return,
        expected_return_5y=expected_return * 5,
        volatility=volatility,
        var95=prop.get("list_price", 0) * 0.8,
        sharpe_ratio=0.7,
        max_drawdown=-0.20,
        total_supply=100000,
        management_fee=0.02,
        performance_fee=0.20,
        token_symbol=token_symbol,
        token_address=token_address,
        rent_growth=0.04,
        rent_volatility=0.08,
        supply_elasticity=0.30,
        risk_score=50,
        tokens_held=0
    )


def load_stage2_files() -> List[PortfolioAsset]:
    """Load assets from Stage 2 JSON files"""
    assets = []
    if STAGE2_OUTPUT_DIR.exists():
        for f in STAGE2_OUTPUT_DIR.glob("*.json"):
            try:
                with open(f, 'r') as file:
                    data = json.load(file)
                    if "property" in data:
                        prop = data["property"]
                        asset = PortfolioAsset(
                            asset_id=f.stem,
                            name=prop.get("address", "Unknown")[:40],
                            property_type="Multifamily",
                            metro=prop.get("metro", "Unknown"),
                            property_value=prop.get("list_price", 0),
                            token_price=25.0,
                            market_cap=prop.get("list_price", 0),
                            expected_return_1y=0.10,
                            expected_return_5y=0.50,
                            volatility=0.15,
                            var95=prop.get("list_price", 0) * 0.8,
                            sharpe_ratio=0.7,
                            max_drawdown=-0.20,
                            total_supply=100000,
                            management_fee=0.02,
                            performance_fee=0.20,
                            token_symbol=prop.get("token_symbol", "FINE5"),
                            token_address=prop.get("token_address", FINE5_ADDRESS),
                            rent_growth=0.04,
                            rent_volatility=0.08,
                            supply_elasticity=0.30,
                            risk_score=50,
                            tokens_held=0
                        )
                        assets.append(asset)
            except Exception as e:
                pass
    return assets


# =========================================================
# Portfolio Analytics (simplified for demo)
# =========================================================

class PortfolioAnalyzer:
    def __init__(self, portfolio: Portfolio):
        self.portfolio = portfolio
    
    def calculate_diversification_score(self) -> float:
        if len(self.portfolio.assets) <= 1:
            return 0
        metros = set(a.metro for a in self.portfolio.assets)
        return min(100, len(metros) * 20 + len(self.portfolio.assets) * 5)
    
    def calculate_total_value(self) -> float:
        return self.portfolio.total_value


# =========================================================
# UI Components
# =========================================================

def render_import_section() -> List[PortfolioAsset]:
    st.header("?? Import Assets")
    
    # Option 1: Import from API
    st.subheader("Option 1: Import from API (Live)")
    if st.button("?? Fetch Properties from API"):
        with st.spinner("Fetching from API..."):
            api_properties = fetch_properties_from_api()
            if api_properties:
                assets = [convert_api_property_to_asset(p) for p in api_properties]
                st.success(f"Imported {len(assets)} properties from API!")
                return assets
            else:
                st.warning("No properties found in API. Run Stage 2 first.")
    
    # Option 2: Load demo assets
    st.subheader("Option 2: Load Demo Assets")
    if st.button("?? Load Demo Assets"):
        demo_assets = [
            PortfolioAsset(
                asset_id="demo_charlotte",
                name="Charlotte Luxury Apartments",
                property_type="Multifamily",
                metro="Charlotte",
                property_value=685000,
                token_price=25.00,
                market_cap=685000,
                expected_return_1y=0.12,
                expected_return_5y=0.60,
                volatility=0.15,
                var95=500000,
                sharpe_ratio=0.80,
                max_drawdown=-0.20,
                total_supply=100000,
                management_fee=0.02,
                performance_fee=0.20,
                token_symbol="FINE5",
                token_address=FINE5_ADDRESS,
                rent_growth=0.10,
                rent_volatility=0.08,
                supply_elasticity=0.35,
                risk_score=72,
                tokens_held=10000
            ),
            PortfolioAsset(
                asset_id="demo_austin",
                name="Austin Tech Towers",
                property_type="Multifamily",
                metro="Austin",
                property_value=1250000,
                token_price=22.00,
                market_cap=1250000,
                expected_return_1y=0.14,
                expected_return_5y=0.70,
                volatility=0.20,
                var95=900000,
                sharpe_ratio=0.70,
                max_drawdown=-0.22,
                total_supply=100000,
                management_fee=0.02,
                performance_fee=0.20,
                token_symbol="FINE6",
                token_address=FINE6_ADDRESS,
                rent_growth=0.14,
                rent_volatility=0.12,
                supply_elasticity=0.48,
                risk_score=78,
                tokens_held=8000
            )
        ]
        st.success("Loaded 2 demo assets!")
        return demo_assets
    
    # Option 3: Import from files
    st.subheader("Option 3: Import from Stage 2 Files")
    stage2_files = list(STAGE2_OUTPUT_DIR.glob("*.json")) if STAGE2_OUTPUT_DIR.exists() else []
    if stage2_files:
        selected = st.multiselect("Select files", stage2_files, format_func=lambda x: x.name)
        if st.button("Import Selected"):
            assets = load_stage2_files()
            if assets:
                st.success(f"Imported {len(assets)} assets from files!")
                return assets
    else:
        st.info("No Stage 2 files found. Run Stage 2 first.")
    
    return []


def render_allocation(portfolio: Portfolio) -> Portfolio:
    st.header("?? Portfolio Allocation")
    
    if not portfolio.assets:
        st.info("No assets. Import first.")
        return portfolio
    
    # Editable table
    data = []
    for a in portfolio.assets:
        data.append({
            "Asset": a.name[:25],
            "Metro": a.metro,
            "Token": a.token_symbol,
            "Price": f"${a.token_price:.2f}",
            "Tokens": a.tokens_held,
            "Value": f"${a.value_held:,.0f}"
        })
    
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Total value
    st.metric("Total Portfolio Value", f"${portfolio.total_value:,.0f}")
    
    return portfolio


# =========================================================
# Main
# =========================================================

def main():
    st.title("?? Kejafi Stage 3: Portfolio Management")
    st.markdown("Import assets from Stage 2 (API or files), then manage your portfolio.")
    
    if "portfolio" not in st.session_state:
        st.session_state.portfolio = Portfolio(assets=[])
    
    tab1, tab2 = st.tabs(["?? Import Assets", "?? Portfolio"])
    
    with tab1:
        imported = render_import_section()
        if imported:
            st.session_state.portfolio.assets = imported
            st.rerun()
    
    with tab2:
        st.session_state.portfolio = render_allocation(st.session_state.portfolio)
        
        if st.session_state.portfolio.total_value > 0:
            st.subheader("?? Portfolio Summary")
            analyzer = PortfolioAnalyzer(st.session_state.portfolio)
            col1, col2 = st.columns(2)
            col1.metric("Total Value", f"${st.session_state.portfolio.total_value:,.0f}")
            col2.metric("Diversification Score", f"{analyzer.calculate_diversification_score():.0f}/100")
    
    st.markdown("---")
    st.caption(f"Kejafi Stage 3 | Pool: {POOL_ADDRESS[:10]}... | Chain: Sepolia")

if __name__ == "__main__":
    main()
