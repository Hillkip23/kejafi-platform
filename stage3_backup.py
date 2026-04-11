# -*- coding: utf-8 -*-
"""
Kejafi Portfolio Management Platform
Stage 3: Multi-asset portfolio management and reporting

Features:
- Import assets from Stage 2 (JSON files)
- Portfolio-level risk aggregation
- Performance analytics and reporting
- Stress testing across portfolio
- Investor dashboard simulation
- Export for institutional reporting

Integrates with:
- Stage 1: Metro risk data via stage1_output/
- Stage 2: Property valuations via stage2_output/
- Deployed contracts: FINE5/FINE6 on Sepolia
"""

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

import logging
logging.getLogger("tornado.application").setLevel(logging.ERROR)

# =========================================================
# Setup & Paths
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
STAGE1_OUTPUT_DIR = BASE_DIR / "stage1_output"
STAGE2_OUTPUT_DIR = BASE_DIR / "stage2_output"
STAGE3_OUTPUT_DIR = BASE_DIR / "stage3_output"
FIG_DIR = BASE_DIR / "figures"

# Create directories
STAGE3_OUTPUT_DIR.mkdir(exist_ok=True)
FIG_DIR.mkdir(exist_ok=True)

st.set_page_config(
    page_title="Kejafi Portfolio Management",
    layout="wide",
    page_icon="📊"
)

# =========================================================
# Your Deployed Contract Addresses (from Stage 2)
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
    """Single asset in the portfolio"""
    asset_id: str
    name: str
    property_type: str
    metro: str
    
    # Valuation metrics
    property_value: float
    token_price: float
    market_cap: float
    
    # Risk metrics
    expected_return_1y: float
    expected_return_5y: float
    volatility: float
    var95: float
    sharpe_ratio: float
    max_drawdown: float
    
    # Token economics
    total_supply: int
    management_fee: float
    performance_fee: float
    token_symbol: str
    token_address: str
    
    # Market data (from Stage 1)
    rent_growth: float
    rent_volatility: float
    supply_elasticity: float
    risk_score: float
    
    # Allocation
    portfolio_weight: float = 0.0
    tokens_held: int = 0
    
    @property
    def value_held(self) -> float:
        return self.tokens_held * self.token_price


@dataclass
class Portfolio:
    """Complete portfolio of assets"""
    assets: List[PortfolioAsset]
    name: str = "My Portfolio"
    created_date: datetime = field(default_factory=datetime.now)
    total_capital: float = 0.0
    
    @property
    def total_value(self) -> float:
        return sum(a.value_held for a in self.assets)
    
    @property
    def num_assets(self) -> int:
        return len(self.assets)
    
    @property
    def weighted_avg_volatility(self) -> float:
        if self.total_value == 0:
            return 0
        return sum(a.volatility * a.value_held for a in self.assets) / self.total_value
    
    @property
    def weighted_avg_return(self) -> float:
        if self.total_value == 0:
            return 0
        return sum(a.expected_return_1y * a.value_held for a in self.assets) / self.total_value


# =========================================================
# Import Functions (Stage 1 & Stage 2)
# =========================================================

def list_stage2_files() -> List[Path]:
    """List all available Stage 2 output files"""
    files = []
    if STAGE2_OUTPUT_DIR.exists():
        files.extend(STAGE2_OUTPUT_DIR.glob("*.json"))
    if STAGE1_OUTPUT_DIR.exists():
        files.extend(STAGE1_OUTPUT_DIR.glob("*.json"))
    return files


def load_stage2_asset(filepath: Path) -> Optional[PortfolioAsset]:
    """Load asset data from Stage 2 JSON file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different formats
        if "property" in data and "valuation" in data:
            # Stage 2 export format
            prop = data.get("property", {})
            val = data.get("valuation", {})
            market = data.get("market_data", {})
            
            # Determine token based on metro or property
            token_symbol = "FINE5" if "charlotte" in str(prop.get("address", "")).lower() else "FINE6"
            token_address = FINE5_ADDRESS if token_symbol == "FINE5" else FINE6_ADDRESS
            
            return PortfolioAsset(
                asset_id=filepath.stem,
                name=prop.get("address", "Unknown Property")[:30],
                property_type=prop.get("property_type", "Multifamily"),
                metro=prop.get("metro", "Unknown Metro"),
                property_value=val.get("value_income", 0),
                token_price=val.get("token_price", 25.0),
                market_cap=val.get("market_cap", 0),
                expected_return_1y=market.get("yoy_rent_growth", 0.08),
                expected_return_5y=market.get("yoy_rent_growth", 0.08) * 5,
                volatility=market.get("rent_volatility", 0.15),
                var95=val.get("var95", 0),
                sharpe_ratio=0.8,
                max_drawdown=-0.20,
                total_supply=100_000,
                management_fee=0.02,
                performance_fee=0.20,
                token_symbol=token_symbol,
                token_address=token_address,
                rent_growth=market.get("yoy_rent_growth", 0.04),
                rent_volatility=market.get("rent_volatility", 0.08),
                supply_elasticity=market.get("metro_elasticity", 0.30),
                risk_score=market.get("risk_score", 50),
                tokens_held=0
            )
        elif "market_data" in data:
            # Stage 1 format
            market = data.get("market_data", {})
            sim = data.get("simulation_results", {})
            token_symbol = "FINE5" if "charlotte" in str(data.get("metro_name", "")).lower() else "FINE6"
            token_address = FINE5_ADDRESS if token_symbol == "FINE5" else FINE6_ADDRESS
            
            return PortfolioAsset(
                asset_id=filepath.stem,
                name=data.get("metro_name", "Unknown Metro"),
                property_type="Multifamily",
                metro=data.get("metro_name", "Unknown"),
                property_value=sim.get("mean", 10_000_000),
                token_price=sim.get("mean", 25.0),
                market_cap=sim.get("mean", 10_000_000),
                expected_return_1y=market.get("yoy_rent_growth", 0.08),
                expected_return_5y=market.get("yoy_rent_growth", 0.08) * 5,
                volatility=market.get("rent_volatility", 0.15),
                var95=sim.get("var95", 0),
                sharpe_ratio=0.7,
                max_drawdown=-0.20,
                total_supply=100_000,
                management_fee=0.02,
                performance_fee=0.20,
                token_symbol=token_symbol,
                token_address=token_address,
                rent_growth=market.get("yoy_rent_growth", 0.04),
                rent_volatility=market.get("rent_volatility", 0.08),
                supply_elasticity=market.get("metro_elasticity", 0.30),
                risk_score=market.get("risk_score", 50),
                tokens_held=0
            )
        else:
            return None
            
    except Exception as e:
        st.warning(f"Error loading {filepath.name}: {e}")
        return None


def load_multiple_assets(filepaths: List[Path]) -> List[PortfolioAsset]:
    """Load multiple assets from selected files"""
    assets = []
    for fp in filepaths:
        asset = load_stage2_asset(fp)
        if asset:
            assets.append(asset)
    return assets


# =========================================================
# Portfolio Analytics
# =========================================================

class PortfolioAnalyzer:
    """Advanced portfolio analytics and risk aggregation"""
    
    def __init__(self, portfolio: Portfolio):
        self.portfolio = portfolio
    
    def calculate_portfolio_returns(self, n_sims: int = 10000) -> np.ndarray:
        """Monte Carlo simulation of portfolio returns"""
        np.random.seed(42)
        
        if len(self.portfolio.assets) == 0 or self.portfolio.total_value == 0:
            return np.zeros(n_sims)
        
        returns = [a.expected_return_1y for a in self.portfolio.assets]
        volatilities = [a.volatility for a in self.portfolio.assets]
        weights = [a.value_held / self.portfolio.total_value for a in self.portfolio.assets]
        
        # Simple correlation (assets in same metro have higher correlation)
        n_assets = len(self.portfolio.assets)
        corr_matrix = np.eye(n_assets)
        for i, a1 in enumerate(self.portfolio.assets):
            for j, a2 in enumerate(self.portfolio.assets):
                if i != j and a1.metro == a2.metro:
                    corr_matrix[i, j] = 0.5
                    corr_matrix[j, i] = 0.5
        
        try:
            L = np.linalg.cholesky(corr_matrix)
        except np.linalg.LinAlgError:
            L = np.eye(n_assets)
        
        portfolio_returns = np.zeros(n_sims)
        for sim in range(n_sims):
            z = np.random.normal(0, 1, n_assets)
            correlated_shocks = L @ z
            asset_returns = np.array(returns) + np.array(volatilities) * correlated_shocks
            portfolio_returns[sim] = np.sum(weights * asset_returns)
        
        return portfolio_returns
    
    def calculate_risk_metrics(self, returns: np.ndarray) -> Dict:
        """Calculate portfolio risk metrics"""
        if len(returns) == 0 or np.all(returns == 0):
            return {
                "expected_return": 0.0, "volatility": 0.0, "var95": 0.0,
                "cvar": 0.0, "sharpe_ratio": 0.0, "probability_loss": 0.0,
                "max_return": 0.0, "min_return": 0.0
            }
        
        var95 = np.percentile(returns, 5)
        cvar = np.mean(returns[returns <= var95])
        
        return {
            "expected_return": float(np.mean(returns)),
            "volatility": float(np.std(returns)),
            "var95": float(var95),
            "cvar": float(cvar),
            "sharpe_ratio": float(np.mean(returns) / (np.std(returns) + 1e-6)),
            "probability_loss": float(np.mean(returns < 0)),
            "max_return": float(np.max(returns)),
            "min_return": float(np.min(returns))
        }
    
    def calculate_diversification_score(self) -> float:
        """Calculate portfolio diversification score (0-100)"""
        if len(self.portfolio.assets) <= 1 or self.portfolio.total_value == 0:
            return 0
        
        metros = set(a.metro for a in self.portfolio.assets)
        asset_score = min(100, len(self.portfolio.assets) * 15)
        metro_score = min(100, len(metros) * 25)
        
        weights = [a.value_held / self.portfolio.total_value for a in self.portfolio.assets]
        herfindahl = sum(w**2 for w in weights)
        concentration_penalty = min(50, herfindahl * 100)
        
        score = (asset_score * 0.5 + metro_score * 0.5) - concentration_penalty
        return max(0, min(100, score))
    
    def calculate_correlation_matrix(self) -> pd.DataFrame:
        """Calculate asset correlation matrix"""
        n = len(self.portfolio.assets)
        corr_matrix = np.eye(n)
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    same_metro = self.portfolio.assets[i].metro == self.portfolio.assets[j].metro
                    corr = 0.5 if same_metro else 0.1
                    corr_matrix[i, j] = corr
                    corr_matrix[j, i] = corr
        
        return pd.DataFrame(
            corr_matrix,
            index=[a.name for a in self.portfolio.assets],
            columns=[a.name for a in self.portfolio.assets]
        )


# =========================================================
# UI Components
# =========================================================

def render_asset_import_section() -> List[PortfolioAsset]:
    """Render the asset import interface"""
    st.header("📥 Import Assets from Stage 2")
    
    stage2_files = list_stage2_files()
    
    if not stage2_files:
        st.warning("⚠️ No Stage 2 assets found. Run Stage 2 analysis first.")
        
        # Demo assets for testing
        if st.button("Load Demo Assets", type="secondary"):
            demo_assets = [
                PortfolioAsset(
                    asset_id="demo_charlotte",
                    name="Charlotte Luxury Apartments",
                    property_type="Multifamily",
                    metro="Charlotte",
                    property_value=25_000_000,
                    token_price=25.00,
                    market_cap=25_000_000,
                    expected_return_1y=0.12,
                    expected_return_5y=0.60,
                    volatility=0.15,
                    var95=18_000_000,
                    sharpe_ratio=0.80,
                    max_drawdown=-0.20,
                    total_supply=1_000_000,
                    management_fee=0.02,
                    performance_fee=0.20,
                    token_symbol="FINE5",
                    token_address=FINE5_ADDRESS,
                    rent_growth=0.10,
                    rent_volatility=0.08,
                    supply_elasticity=0.25,
                    risk_score=72,
                    tokens_held=100000
                ),
                PortfolioAsset(
                    asset_id="demo_austin",
                    name="Austin Tech Towers",
                    property_type="Multifamily",
                    metro="Austin",
                    property_value=22_000_000,
                    token_price=22.00,
                    market_cap=22_000_000,
                    expected_return_1y=0.14,
                    expected_return_5y=0.70,
                    volatility=0.20,
                    var95=15_000_000,
                    sharpe_ratio=0.70,
                    max_drawdown=-0.22,
                    total_supply=1_000_000,
                    management_fee=0.02,
                    performance_fee=0.20,
                    token_symbol="FINE6",
                    token_address=FINE6_ADDRESS,
                    rent_growth=0.14,
                    rent_volatility=0.12,
                    supply_elasticity=0.35,
                    risk_score=78,
                    tokens_held=80000
                )
            ]
            st.success("✅ Loaded demo assets!")
            return demo_assets
        
        return []
    
    selected_files = st.multiselect(
        "Select Stage 2 Assets to Import",
        options=stage2_files,
        format_func=lambda x: x.name.replace(".json", ""),
        help="Select one or more JSON files exported from Stage 2"
    )
    
    # Allocation strategy
    col1, col2 = st.columns(2)
    with col1:
        allocation_strategy = st.selectbox(
            "Allocation Strategy",
            ["equal_value", "proportional_value"],
            format_func=lambda x: "Equal Dollar Value" if x == "equal_value" else "Proportional to Property Value"
        )
    with col2:
        total_investment = st.number_input(
            "Total Investment ($)", min_value=100_000, max_value=50_000_000,
            value=1_000_000, step=100_000, format="%d"
        )
    
    if selected_files and st.button("🚀 Import Assets", type="primary"):
        assets = load_multiple_assets(selected_files)
        if assets:
            # Auto-allocate tokens
            if allocation_strategy == "equal_value":
                value_per_asset = total_investment / len(assets)
                for asset in assets:
                    asset.tokens_held = int(value_per_asset / asset.token_price)
            else:
                total_value = sum(a.property_value for a in assets)
                for asset in assets:
                    proportion = asset.property_value / total_value
                    value_allocated = total_investment * proportion
                    asset.tokens_held = int(value_allocated / asset.token_price)
            
            st.success(f"✅ Imported {len(assets)} assets!")
            return assets
    
    return []


def render_portfolio_allocation(portfolio: Portfolio) -> Portfolio:
    """Render portfolio allocation interface"""
    st.header("💰 Portfolio Allocation")
    
    if not portfolio.assets:
        st.info("No assets in portfolio. Import assets first.")
        return portfolio
    
    st.subheader("Current Holdings")
    
    allocation_data = []
    for asset in portfolio.assets:
        allocation_data.append({
            "Asset": asset.name[:30],
            "Metro": asset.metro,
            "Token": asset.token_symbol,
            "Token Price": asset.token_price,
            "Tokens Held": asset.tokens_held,
            "Value": asset.value_held,
            "Portfolio %": asset.portfolio_weight * 100
        })
    
    alloc_df = pd.DataFrame(allocation_data)
    
    # Editable tokens held
    edited_df = st.data_editor(
        alloc_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Asset": st.column_config.TextColumn("Asset", disabled=True),
            "Metro": st.column_config.TextColumn("Metro", disabled=True),
            "Token": st.column_config.TextColumn("Token", disabled=True),
            "Token Price": st.column_config.NumberColumn("Token Price", format="$%.2f", disabled=True),
            "Tokens Held": st.column_config.NumberColumn("Tokens Held", step=1000, min_value=0),
            "Value": st.column_config.NumberColumn("Value", format="$%.0f", disabled=True),
            "Portfolio %": st.column_config.NumberColumn("Portfolio %", format="%.1f%%", disabled=True)
        }
    )
    
    # Update portfolio
    for i, asset in enumerate(portfolio.assets):
        asset.tokens_held = int(edited_df.iloc[i]["Tokens Held"])
    
    total_value = sum(a.value_held for a in portfolio.assets)
    for asset in portfolio.assets:
        asset.portfolio_weight = asset.value_held / total_value if total_value > 0 else 0
    
    if total_value > 0:
        st.subheader("Allocation Breakdown")
        
        # Create two separate pie charts using matplotlib (avoid plotly subplot issues)
        col1, col2 = st.columns(2)
        
        with col1:
            fig1, ax1 = plt.subplots(figsize=(6, 6))
            labels1 = [a.name[:20] for a in portfolio.assets]
            sizes1 = [a.value_held for a in portfolio.assets]
            colors1 = plt.cm.Set3(range(len(labels1)))
            ax1.pie(sizes1, labels=labels1, autopct='%1.1f%%', colors=colors1, startangle=90)
            ax1.set_title('By Asset')
            st.pyplot(fig1)
            plt.close(fig1)
        
        with col2:
            fig2, ax2 = plt.subplots(figsize=(6, 6))
            metro_values = defaultdict(float)
            for asset in portfolio.assets:
                metro_values[asset.metro] += asset.value_held
            labels2 = list(metro_values.keys())
            sizes2 = list(metro_values.values())
            colors2 = plt.cm.Set2(range(len(labels2)))
            ax2.pie(sizes2, labels=labels2, autopct='%1.1f%%', colors=colors2, startangle=90)
            ax2.set_title('By Metro')
            st.pyplot(fig2)
            plt.close(fig2)
        
        # Portfolio summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Portfolio Value", f"${total_value:,.0f}")
        with col2:
            st.metric("Number of Assets", len(portfolio.assets))
        with col3:
            avg_price = np.mean([a.token_price for a in portfolio.assets])
            st.metric("Avg Token Price", f"${avg_price:.2f}")
        with col4:
            total_tokens = sum(a.tokens_held for a in portfolio.assets)
            st.metric("Total Tokens Held", f"{total_tokens:,.0f}")
    
    return portfolio


def render_portfolio_analytics(portfolio: Portfolio):
    """Render portfolio analytics dashboard"""
    st.header("📊 Portfolio Analytics")
    
    if not portfolio.assets or portfolio.total_value == 0:
        st.warning("No assets with allocation. Configure portfolio allocation first.")
        return None, None
    
    analyzer = PortfolioAnalyzer(portfolio)
    
    with st.spinner("Running Monte Carlo simulation..."):
        returns = analyzer.calculate_portfolio_returns(n_sims=10000)
        risk_metrics = analyzer.calculate_risk_metrics(returns)
    
    st.subheader("Risk & Return Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Expected Annual Return", f"{risk_metrics['expected_return']*100:.1f}%")
    with col2:
        st.metric("Portfolio Volatility", f"{risk_metrics['volatility']*100:.1f}%")
    with col3:
        st.metric("Sharpe Ratio", f"{risk_metrics['sharpe_ratio']:.2f}")
    with col4:
        st.metric("Diversification Score", f"{analyzer.calculate_diversification_score():.0f}/100")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("VaR (95%)", f"{risk_metrics['var95']*100:.1f}%")
    with col2:
        st.metric("CVaR (95%)", f"{risk_metrics['cvar']*100:.1f}%")
    with col3:
        st.metric("Prob. of Loss", f"{risk_metrics['probability_loss']*100:.1f}%")
    with col4:
        st.metric("Best/Worst", f"+{risk_metrics['max_return']*100:.0f}% / {risk_metrics['min_return']*100:.0f}%")
    
    # Return distribution plot using matplotlib
    st.subheader("Portfolio Return Distribution")
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(returns * 100, bins=50, alpha=0.7, color='#3498db', edgecolor='black')
    ax.axvline(risk_metrics['expected_return'] * 100, color='green', linestyle='--', linewidth=2, 
               label=f"Mean: {risk_metrics['expected_return']*100:.1f}%")
    ax.axvline(risk_metrics['var95'] * 100, color='red', linestyle='--', linewidth=2,
               label=f"VaR95: {risk_metrics['var95']*100:.1f}%")
    ax.set_xlabel("Annual Return (%)")
    ax.set_ylabel("Frequency")
    ax.set_title("Monte Carlo Simulation (10,000 scenarios)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)
    plt.close(fig)
    
    # Correlation matrix heatmap
    if len(portfolio.assets) > 1:
        st.subheader("Asset Correlation Matrix")
        corr_df = analyzer.calculate_correlation_matrix()
        fig, ax = plt.subplots(figsize=(8, 6))
        im = ax.imshow(corr_df.values, cmap='RdBu', vmin=-1, vmax=1)
        ax.set_xticks(range(len(corr_df.columns)))
        ax.set_yticks(range(len(corr_df.index)))
        ax.set_xticklabels(corr_df.columns, rotation=45, ha='right')
        ax.set_yticklabels(corr_df.index)
        plt.colorbar(im, ax=ax)
        st.pyplot(fig)
        plt.close(fig)
    
    return risk_metrics, analyzer


def render_stress_testing(portfolio: Portfolio, analyzer: PortfolioAnalyzer):
    """Render stress testing scenarios"""
    st.header("⚠️ Portfolio Stress Testing")
    
    if not portfolio.assets:
        st.warning("No assets in portfolio")
        return
    
    scenarios = {
        "Base Case": {"rent_multiplier": 1.0, "cap_rate_shock": 0.0, "vacancy_shock": 0.0, "liquidity_shock": 1.0},
        "Mild Recession": {"rent_multiplier": 0.95, "cap_rate_shock": 0.005, "vacancy_shock": 0.05, "liquidity_shock": 0.8},
        "Severe Recession": {"rent_multiplier": 0.85, "cap_rate_shock": 0.025, "vacancy_shock": 0.12, "liquidity_shock": 0.5},
        "Rate Shock": {"rent_multiplier": 1.02, "cap_rate_shock": 0.015, "vacancy_shock": 0.02, "liquidity_shock": 0.7},
        "COVID Style": {"rent_multiplier": 0.90, "cap_rate_shock": 0.005, "vacancy_shock": 0.10, "liquidity_shock": 0.4}
    }
    
    selected_scenario = st.selectbox("Select Stress Scenario", list(scenarios.keys()))
    
    if st.button("Run Stress Test", type="primary"):
        scenario = scenarios[selected_scenario]
        
        stressed_values = []
        base_values = []
        
        for asset in portfolio.assets:
            base_value = asset.value_held
            stress_factor = (scenario["rent_multiplier"] * (1 - scenario["cap_rate_shock"] * 10) * 
                            (1 - scenario["vacancy_shock"]) * scenario["liquidity_shock"])
            stressed_values.append(base_value * stress_factor)
            base_values.append(base_value)
        
        results_df = pd.DataFrame({
            "Asset": [a.name[:25] for a in portfolio.assets],
            "Current Value": base_values,
            "Stressed Value": stressed_values,
            "Change %": [(s/b - 1) * 100 for s, b in zip(stressed_values, base_values)]
        })
        
        st.dataframe(results_df, use_container_width=True, hide_index=True,
                    column_config={"Current Value": st.column_config.NumberColumn(format="$%.0f"),
                                  "Stressed Value": st.column_config.NumberColumn(format="$%.0f"),
                                  "Change %": st.column_config.NumberColumn(format="%.1f%%")})
        
        total_current = sum(base_values)
        total_stressed = sum(stressed_values)
        total_change_pct = (total_stressed / total_current - 1) * 100
        
        if total_change_pct < -30:
            st.error(f"🚨 CRITICAL: Portfolio would lose {total_change_pct:.1f}%")
        elif total_change_pct < -15:
            st.warning(f"⚠️ HIGH RISK: Portfolio would lose {total_change_pct:.1f}%")
        elif total_change_pct < -5:
            st.info(f"📊 MODERATE RISK: Portfolio would lose {total_change_pct:.1f}%")
        else:
            st.success(f"✅ RESILIENT: Portfolio impact {total_change_pct:.1f}%")


def render_investor_dashboard(portfolio: Portfolio):
    """Render investor-facing dashboard"""
    st.header("👥 Investor Dashboard")
    
    if not portfolio.assets or portfolio.total_value == 0:
        st.info("Configure portfolio to see dashboard")
        return
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total AUM", f"${portfolio.total_value:,.0f}")
    with col2:
        st.metric("Number of Assets", portfolio.num_assets)
    with col3:
        st.metric("Avg Token Price", f"${np.mean([a.token_price for a in portfolio.assets]):.2f}")
    with col4:
        st.metric("Pool TVL", f"${portfolio.total_value * 0.15:,.0f}")
    
    # Historical NAV chart
    st.subheader("Historical NAV (Simulated)")
    dates = pd.date_range(start='2024-01-01', end=datetime.now(), freq='M')
    nav_history = portfolio.total_value * (1 + np.random.normal(0.01, 0.05, len(dates)).cumsum() / 100)
    
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(dates, nav_history, color='#2ecc71', linewidth=2)
    ax.fill_between(dates, nav_history, alpha=0.3, color='#2ecc71')
    ax.set_xlabel("Date")
    ax.set_ylabel("NAV ($)")
    ax.set_title("Net Asset Value History")
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)
    plt.close(fig)
    
    # Fee projections
    st.subheader("Fee Structure")
    annual_fees = portfolio.total_value * np.mean([a.management_fee for a in portfolio.assets])
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Annual Management Fees", f"${annual_fees:,.0f}")
    with col2:
        st.metric("Est. Performance Fees", f"${annual_fees * 0.3:,.0f}")
    with col3:
        st.metric("Total Annual Revenue", f"${annual_fees * 1.3:,.0f}")


def render_report_export(portfolio: Portfolio, risk_metrics: Dict, analyzer: PortfolioAnalyzer):
    """Render report export section"""
    st.header("📄 Generate Reports")
    
    if not portfolio.assets:
        st.warning("No assets to report")
        return
    
    if st.button("Generate Portfolio Report", type="primary"):
        report = f"""
        KEFAJI PORTFOLIO REPORT
        =======================
        Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        Portfolio: {portfolio.name}
        
        PORTFOLIO OVERVIEW
        -----------------
        Total Value: ${portfolio.total_value:,.2f}
        Number of Assets: {portfolio.num_assets}
        
        PERFORMANCE
        -----------
        Expected Return: {risk_metrics.get('expected_return', 0)*100:.1f}%
        Volatility: {risk_metrics.get('volatility', 0)*100:.1f}%
        Sharpe Ratio: {risk_metrics.get('sharpe_ratio', 0):.2f}
        VaR (95%): {risk_metrics.get('var95', 0)*100:.1f}%
        Probability of Loss: {risk_metrics.get('probability_loss', 0)*100:.1f}%
        
        DIVERSIFICATION
        ---------------
        Score: {analyzer.calculate_diversification_score():.0f}/100
        
        ASSETS
        ------
        """
        for asset in portfolio.assets:
            report += f"\n  {asset.name}\n    Value: ${asset.value_held:,.0f} ({asset.portfolio_weight*100:.1f}%)\n    Expected Return: {asset.expected_return_1y*100:.1f}%"
        
        st.download_button("📥 Download Report", report, file_name=f"portfolio_report_{datetime.now().strftime('%Y%m%d')}.txt")
        st.success("Report generated!")


# =========================================================
# Main App
# =========================================================

def main():
    st.title("📊 Kejafi Stage 3: Portfolio Management")
    st.markdown("Manage your tokenized real estate portfolio, analyze risk, and generate professional reports.")
    
    # Initialize session state
    if "portfolio" not in st.session_state:
        st.session_state.portfolio = Portfolio(assets=[])
    if "risk_metrics" not in st.session_state:
        st.session_state.risk_metrics = None
    if "analyzer" not in st.session_state:
        st.session_state.analyzer = None
    
    # Sidebar
    st.sidebar.header("📁 Portfolio")
    portfolio_name = st.sidebar.text_input("Portfolio Name", st.session_state.portfolio.name)
    st.session_state.portfolio.name = portfolio_name
    
    if st.session_state.portfolio.assets:
        st.sidebar.metric("Total Value", f"${st.session_state.portfolio.total_value:,.0f}")
        st.sidebar.metric("Assets", len(st.session_state.portfolio.assets))
    
    st.sidebar.markdown("---")
    st.sidebar.info("**Deployed Contracts (Sepolia)**")
    st.sidebar.code(f"FINE5: {FINE5_ADDRESS[:10]}...")
    st.sidebar.code(f"FINE6: {FINE6_ADDRESS[:10]}...")
    st.sidebar.markdown(f"[View Pool](https://sepolia.etherscan.io/address/{POOL_ADDRESS})")
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📥 Import", "💰 Allocation", "📊 Analytics", "⚠️ Stress", "📄 Reporting"
    ])
    
    with tab1:
        imported_assets = render_asset_import_section()
        if imported_assets:
            st.session_state.portfolio.assets = imported_assets
            st.rerun()
    
    with tab2:
        st.session_state.portfolio = render_portfolio_allocation(st.session_state.portfolio)
    
    with tab3:
        if st.session_state.portfolio.assets:
            has_allocation = any(a.tokens_held > 0 for a in st.session_state.portfolio.assets)
            if has_allocation:
                result = render_portfolio_analytics(st.session_state.portfolio)
                if result:
                    risk_metrics, analyzer = result
                    st.session_state.risk_metrics = risk_metrics
                    st.session_state.analyzer = analyzer
            else:
                st.warning("⚠️ No tokens allocated. Go to Allocation tab first.")
        else:
            st.info("📌 Import assets first (Import tab)")
    
    with tab4:
        if st.session_state.portfolio.assets and st.session_state.analyzer:
            render_stress_testing(st.session_state.portfolio, st.session_state.analyzer)
        else:
            st.info("📌 Run analytics first (Analytics tab)")
    
    with tab5:
        if st.session_state.portfolio.assets and st.session_state.risk_metrics:
            render_investor_dashboard(st.session_state.portfolio)
            st.markdown("---")
            render_report_export(st.session_state.portfolio, st.session_state.risk_metrics, st.session_state.analyzer)
        else:
            st.info("📌 Complete analytics first (Analytics tab)")
    
    st.markdown("---")
    st.caption(f"Kejafi Stage 3 | Portfolio: {st.session_state.portfolio.name} | Total Value: ${st.session_state.portfolio.total_value:,.0f}")


if __name__ == "__main__":
    main()