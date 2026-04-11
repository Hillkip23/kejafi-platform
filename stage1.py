# -*- coding: utf-8 -*-
"""
Kejafi Research Engine
Stage 1: Metro-level risk analysis and stress testing

Features:
- Standard Mode: OU process, fixed cap rates (uses metro_lab_core if available)
- Stress Lab: Jump-diffusion, stochastic rates, liquidity crises, oracle risk
- County-level granularity for sub-market analysis
- Export pipeline to Stage 2 for single-asset tokenization

ENHANCED FEATURES (v5):
- Population growth integrated into rent growth forecasts
- Supply elasticity affects vacancy and cap rate assumptions
- Elasticity-adjusted risk scoring
- Pop growth affects long-term mean reversion (theta)
- Metro-only mode now correctly uses metro-level elasticity and pop growth
- CSV data loading for population and elasticity
- Custom UI styling with gradient buttons
- Progress bars for long simulations
- CSV/JSON export functionality
- Keyboard shortcuts help
- Performance tips
"""

import math
import json
import time
import hashlib
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go

import logging
logging.getLogger("tornado.application").setLevel(logging.ERROR)

# =========================================================
# Optional Core Integration
# =========================================================

HAS_CORE = False
core_module = None

try:
    import metro_lab_core as core_module
    HAS_CORE = True
except ImportError:
    pass


def use_core_for_standard() -> bool:
    """Check if we should use core module for standard mode."""
    return HAS_CORE and st.session_state.get("use_core_backend", True)


# =========================================================
# UI & Utility Functions
# =========================================================

def apply_custom_styling():
    """Apply custom CSS styling"""
    st.markdown("""
    <style>
    /* Better card styling */
    div[data-testid="stMetric"] {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Button styling */
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
    
    /* Success message styling */
    .stAlert {
        border-radius: 10px;
    }
    
    /* Progress bar styling */
    .stProgress > div > div {
        background-color: #667eea;
    }
    
    /* Info box styling */
    .stInfo {
        border-radius: 10px;
        background-color: #e8f4fd;
    }
    </style>
    """, unsafe_allow_html=True)


def format_currency(value):
    """Format number as currency"""
    return f"${value:,.0f}"


def format_percentage(value):
    """Format number as percentage"""
    return f"{value*100:.1f}%"


def export_to_csv(df, filename_prefix):
    """Export DataFrame to CSV with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return df.to_csv(index=False).encode('utf-8')


@st.cache_data
def get_cache_key(*args, **kwargs):
    """Generate cache key from arguments"""
    key_string = str(args) + str(sorted(kwargs.items()))
    return hashlib.md5(key_string.encode()).hexdigest()


# =========================================================
# Setup
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
ZORI_PATH = DATA_DIR / "Zillow_Observed_Rent_Index.csv"

STAGE1_OUTPUT_DIR = BASE_DIR / "stage1_output"
STAGE1_OUTPUT_DIR.mkdir(exist_ok=True)

FIG_DIR = BASE_DIR / "figures"
FIG_DIR.mkdir(exist_ok=True)

st.set_page_config(page_title="Kejafi Research Engine", layout="wide")


@st.cache_data
def load_zori():
    if not ZORI_PATH.exists():
        st.error(f"ZORI data not found at {ZORI_PATH}")
        st.stop()
    df = pd.read_csv(ZORI_PATH)
    if df.iloc[0, 2] == "RegionName":
        df.columns = df.iloc[0]
        df = df.iloc[1:].reset_index(drop=True)
    return df


zori_df = load_zori()
available_msas = sorted(
    zori_df[zori_df["RegionType"] == "msa"]["RegionName"].unique()
)

# =========================================================
# Target Cities & County Data
# =========================================================

TARGET_KEYWORDS = {
    "Charlotte": ["Charlotte", "Concord", "Gastonia"],
    "Nashville": ["Nashville", "Davidson", "Murfreesboro"],
    "Atlanta": ["Atlanta", "Sandy Springs", "Roswell"],
    "Dallas": ["Dallas", "Fort Worth", "Arlington"],
    "Miami": ["Miami", "Fort Lauderdale", "West Palm"],
    "San Francisco": ["San Francisco", "Oakland", "Berkeley"],
    "Austin": ["Austin", "Round Rock", "Georgetown"],
    "New York": ["New York", "Newark", "Jersey City"],
    "Los Angeles": ["Los Angeles", "Long Beach", "Anaheim"],
    "Chicago": ["Chicago", "Naperville", "Elgin"],
    "Seattle": ["Seattle", "Tacoma", "Bellevue"],
}

# Build FOUND_METROS first
FOUND_METROS: Dict[str, str] = {}
for city_name, keywords in TARGET_KEYWORDS.items():
    for msa in available_msas:
        if any(kw.lower() in msa.lower() for kw in keywords):
            FOUND_METROS[city_name] = msa
            break

# Population growth fallback (used if CSV not available)
POP_GROWTH_FALLBACK = {
    "Charlotte": 0.10,
    "Nashville": 0.12,
    "Atlanta": 0.08,
    "Dallas": 0.11,
    "Miami": 0.05,
    "San Francisco": 0.03,
    "Austin": 0.14,
    "New York": 0.02,
    "Los Angeles": 0.01,
    "Chicago": -0.01,
    "Seattle": 0.09,
}

# Elasticity fallback (used if CSV not available)
ELASTICITY_FALLBACK = {
    "San Francisco": 0.08,
    "New York": 0.10,
    "Los Angeles": 0.12,
    "Miami": 0.15,
    "Seattle": 0.15,
    "Chicago": 0.22,
    "Charlotte": 0.35,
    "Atlanta": 0.38,
    "Nashville": 0.42,
    "Dallas": 0.45,
    "Austin": 0.48,
}

COUNTY_DATA = {
    "Charlotte": [
        {"name": "Mecklenburg County, NC", "pci": 72000, "elasticity": 0.25, "tier": "Core Urban"},
        {"name": "Union County, NC",        "pci": 68000, "elasticity": 0.40, "tier": "Suburban"},
        {"name": "York County, SC",         "pci": 62000, "elasticity": 0.45, "tier": "Periphery"},
    ],
    "Nashville": [
        {"name": "Davidson County, TN",   "pci": 75000, "elasticity": 0.30, "tier": "Core Urban"},
        {"name": "Williamson County, TN", "pci": 82000, "elasticity": 0.38, "tier": "Suburban"},
        {"name": "Rutherford County, TN", "pci": 65000, "elasticity": 0.42, "tier": "Periphery"},
    ],
    "Atlanta": [
        {"name": "Fulton County, GA",   "pci": 78000, "elasticity": 0.22, "tier": "Core Urban"},
        {"name": "DeKalb County, GA",   "pci": 68000, "elasticity": 0.28, "tier": "Core Urban"},
        {"name": "Cobb County, GA",     "pci": 72000, "elasticity": 0.35, "tier": "Suburban"},
        {"name": "Gwinnett County, GA", "pci": 70000, "elasticity": 0.40, "tier": "Suburban"},
    ],
    "Dallas": [
        {"name": "Dallas County, TX",  "pci": 72000, "elasticity": 0.28, "tier": "Core Urban"},
        {"name": "Tarrant County, TX", "pci": 68000, "elasticity": 0.32, "tier": "Suburban"},
        {"name": "Collin County, TX",  "pci": 85000, "elasticity": 0.45, "tier": "Periphery"},
        {"name": "Denton County, TX",  "pci": 78000, "elasticity": 0.48, "tier": "Periphery"},
    ],
    "Miami": [
        {"name": "Miami-Dade County, FL", "pci": 68400, "elasticity": 0.12, "tier": "Core Urban"},
        {"name": "Broward County, FL",    "pci": 61200, "elasticity": 0.18, "tier": "Suburban"},
        {"name": "Palm Beach County, FL", "pci": 72300, "elasticity": 0.28, "tier": "Suburban"},
    ],
    "San Francisco": [
        {"name": "San Francisco County, CA", "pci": 121000, "elasticity": 0.08, "tier": "Core Urban"},
        {"name": "Alameda County, CA",       "pci": 98500,  "elasticity": 0.15, "tier": "Core Urban"},
        {"name": "Contra Costa County, CA",  "pci": 87500,  "elasticity": 0.22, "tier": "Suburban"},
        {"name": "San Mateo County, CA",     "pci": 142000, "elasticity": 0.10, "tier": "Core Urban"},
    ],
    "Austin": [
        {"name": "Travis County, TX",    "pci": 82000, "elasticity": 0.35, "tier": "Periphery"},
        {"name": "Williamson County, TX","pci": 76500, "elasticity": 0.42, "tier": "Periphery"},
        {"name": "Hays County, TX",      "pci": 68400, "elasticity": 0.38, "tier": "Periphery"},
    ],
    "New York": [
        {"name": "New York County, NY", "pci": 185000, "elasticity": 0.05, "tier": "Core Urban"},
        {"name": "Kings County, NY",    "pci": 78000,  "elasticity": 0.08, "tier": "Core Urban"},
        {"name": "Queens County, NY",   "pci": 82000,  "elasticity": 0.10, "tier": "Core Urban"},
        {"name": "Hudson County, NJ",   "pci": 89000,  "elasticity": 0.15, "tier": "Core Urban"},
    ],
    "Los Angeles": [
        {"name": "Los Angeles County, CA", "pci": 76000, "elasticity": 0.18, "tier": "Core Urban"},
        {"name": "Orange County, CA",      "pci": 92000, "elasticity": 0.25, "tier": "Suburban"},
    ],
    "Chicago": [
        {"name": "Cook County, IL",  "pci": 78000, "elasticity": 0.20, "tier": "Core Urban"},
        {"name": "DuPage County, IL","pci": 95000, "elasticity": 0.30, "tier": "Suburban"},
        {"name": "Lake County, IL",  "pci": 82000, "elasticity": 0.35, "tier": "Suburban"},
    ],
    "Seattle": [
        {"name": "King County, WA",      "pci": 95000, "elasticity": 0.15, "tier": "Core Urban"},
        {"name": "Snohomish County, WA", "pci": 78000, "elasticity": 0.25, "tier": "Suburban"},
        {"name": "Pierce County, WA",    "pci": 65000, "elasticity": 0.30, "tier": "Suburban"},
    ],
}

METRO_LIST = list(FOUND_METROS.values())
METRO_COUNTIES = {
    full: {"short_name": short, "counties": COUNTY_DATA.get(short, [])}
    for short, full in FOUND_METROS.items()
}

if len(METRO_LIST) < 2:
    st.error("Need at least 2 metros found")
    st.stop()


# =========================================================
# Data Loading Functions (CSV or Fallback)
# =========================================================

@st.cache_data
def load_population_data():
    """Load population growth data from CSV"""
    pop_path = DATA_DIR / "metro_population.csv"
    if pop_path.exists():
        df = pd.read_csv(pop_path)
        return df
    return None

@st.cache_data
def load_elasticity_data():
    """Load supply elasticity data from CSV"""
    elastic_path = DATA_DIR / "metro_elasticity.csv"
    if elastic_path.exists():
        df = pd.read_csv(elastic_path)
        return df
    return None


def get_pop_growth_for_metro(metro_short_name: str) -> float:
    """Get population growth for a metro from CSV or fallback"""
    pop_df = load_population_data()
    
    if pop_df is not None:
        # Try exact match
        match = pop_df[pop_df['metro_name'] == metro_short_name]
        if not match.empty:
            return float(match['pop_growth_5yr'].iloc[0])
        
        # Try partial match
        for _, row in pop_df.iterrows():
            if row['metro_name'].lower() in metro_short_name.lower():
                return float(row['pop_growth_5yr'])
    
    # Fallback to hardcoded dictionary
    return POP_GROWTH_FALLBACK.get(metro_short_name, 0.05)


def get_elasticity_for_metro(metro_short_name: str) -> float:
    """Get supply elasticity for a metro from CSV or fallback"""
    elastic_df = load_elasticity_data()
    
    if elastic_df is not None:
        # Try exact match
        match = elastic_df[elastic_df['metro_name'] == metro_short_name]
        if not match.empty:
            return float(match['elasticity'].iloc[0])
        
        # Try partial match
        for _, row in elastic_df.iterrows():
            if row['metro_name'].lower() in metro_short_name.lower():
                return float(row['elasticity'])
    
    # Fallback to hardcoded dictionary
    return ELASTICITY_FALLBACK.get(metro_short_name, 0.30)


def get_supply_bucket_for_metro(metro_short_name: str) -> str:
    """Get supply bucket category for a metro"""
    elastic_df = load_elasticity_data()
    
    if elastic_df is not None and 'supply_bucket' in elastic_df.columns:
        match = elastic_df[elastic_df['metro_name'] == metro_short_name]
        if not match.empty:
            return match['supply_bucket'].iloc[0]
    
    # Fallback logic
    elasticity = get_elasticity_for_metro(metro_short_name)
    if elasticity < 0.15:
        return "very inelastic"
    elif elasticity < 0.25:
        return "inelastic"
    elif elasticity > 0.40:
        return "elastic"
    else:
        return "neutral"


# =========================================================
# Enums & Configuration
# =========================================================

class EngineMode(Enum):
    STANDARD = "Standard Risk Engine (v1)"
    STRESS = "Advanced Stress Lab (v2)"


class StressScenario(Enum):
    BASE_CASE = "Base Case"
    COVID_SHOCK = "COVID-19 (2020-style)"
    GFC_2008 = "Global Financial Crisis (2008)"
    RATE_SHOCK_2022 = "Fed Rate Shock (2022)"
    CRYPTO_WINTER = "Crypto Contagion"
    STAGFLATION = "Stagflation (1970s-style)"


@dataclass
class TokenizationParams:
    total_supply: int = 1_000_000
    float_percent: float = 0.30
    lockup_months: int = 12
    redemption_gate_threshold: float = 0.15
    nav_penalty_tiers: List[Tuple[float, float]] = field(
        default_factory=lambda: [
            (0.05, 0.0),
            (0.10, 0.03),
            (0.20, 0.08),
            (0.30, 0.15),
            (1.00, 0.25),
        ]
    )
    amm_tvl: float = 1_000_000.0
    emergency_appraisal_cost: float = 50_000.0


# =========================================================
# Risk Models
# =========================================================

class JumpDiffusionRent:
    def __init__(self, lambda_jump=0.1, mu_jump=-0.20, sigma_jump=0.10):
        self.lambda_j = lambda_jump
        self.mu_j = mu_jump
        self.sigma_j = sigma_jump

    def simulate(self, X0, kappa, theta, sigma, T_years, steps, n_sims, seed=42):
        rng = np.random.default_rng(seed)
        dt = T_years / steps
        paths = np.zeros((n_sims, steps + 1))
        paths[:, 0] = X0
        for t in range(steps):
            dW = rng.normal(0, np.sqrt(dt), n_sims)
            dX = kappa * (theta - paths[:, t]) * dt + sigma * dW
            n_jumps = rng.poisson(self.lambda_j * dt, n_sims)
            for i in range(n_sims):
                if n_jumps[i] > 0:
                    jump = rng.normal(self.mu_j, self.sigma_j, n_jumps[i]).sum()
                    dX[i] += jump
            paths[:, t + 1] = paths[:, t] + dX
        return paths


class StochasticCapRate:
    def __init__(self, r0=0.05, kappa_r=0.5, theta_r=0.06, sigma_r=0.015):
        self.r0 = r0
        self.kappa = kappa_r
        self.theta = theta_r
        self.sigma = sigma_r

    def simulate(self, T_years, steps, n_sims, seed=42):
        rng = np.random.default_rng(seed)
        dt = T_years / steps
        rates = np.zeros((n_sims, steps + 1))
        rates[:, 0] = self.r0
        for t in range(steps):
            dW = rng.normal(0, np.sqrt(dt), n_sims)
            dr = (
                self.kappa * (self.theta - rates[:, t]) * dt
                + self.sigma * np.sqrt(np.maximum(rates[:, t], 0)) * dW
            )
            rates[:, t + 1] = np.maximum(rates[:, t] + dr, 0.001)
        return rates


class RedemptionQueueModel:
    def __init__(self, params: TokenizationParams):
        self.params = params

    def calculate_nav_discount(self, pct: float) -> float:
        for threshold, haircut in self.params.nav_penalty_tiers:
            if pct <= threshold:
                return haircut
        return 0.25

    def simulate_crisis(self, token_prices: np.ndarray, scenario: str):
        scenarios = {"minor": 0.05, "stress": 0.20, "bank_run": 0.50}
        demand = scenarios[scenario]
        nav_disc = self.calculate_nav_discount(demand)
        gated = demand > self.params.redemption_gate_threshold
        sell_pressure = (
            demand * self.params.total_supply * float(np.mean(token_prices))
        )
        amm_slip = min(sell_pressure / self.params.amm_tvl * 0.5, 0.30)
        total = nav_disc + amm_slip if not gated else 0.50
        return {
            "demand": demand,
            "nav_discount": nav_disc,
            "amm_slippage": amm_slip,
            "total_haircut": total,
            "gated": gated,
            "exit_price": float(np.mean(token_prices) * (1 - total)),
            "recovery_months": 3 if not gated else 18,
        }


# =========================================================
# Helper Functions
# =========================================================

def get_series(msa_name: str) -> Optional[pd.Series]:
    sub = zori_df[
        (zori_df["RegionName"] == msa_name) & (zori_df["RegionType"] == "msa")
    ]
    if sub.empty:
        return None
    date_cols = [c for c in sub.columns if str(c)[:4].isdigit()]
    values = sub[date_cols].iloc[0].astype(float).dropna()
    return pd.Series(values.values, index=pd.to_datetime(values.index))


def get_scenario_params(
    scenario: StressScenario, county_elasticity: float = 0.3
) -> Dict:
    base = {
        StressScenario.BASE_CASE: {
            "vacancy_shock": 0.0,
            "rent_growth_adj": 0.0,
            "cap_rate_shock": 0.0,
            "jump_intensity": 0.0,
            "liquidity_factor": 1.0,
            "description": "Normal market conditions with stable rents and typical vacancy rates.",
        },
        StressScenario.COVID_SHOCK: {
            "vacancy_shock": 0.12 * (county_elasticity / 0.3),
            "rent_growth_adj": -0.25,
            "cap_rate_shock": 0.005,
            "jump_intensity": 0.3,
            "jump_size": -0.30,
            "liquidity_factor": 0.5,
            "description": "March 2020-style pandemic shock with sudden rent drops and urban exodus.",
        },
        StressScenario.GFC_2008: {
            "vacancy_shock": 0.08,
            "rent_growth_adj": -0.15,
            "cap_rate_shock": 0.025,
            "jump_intensity": 0.15,
            "jump_size": -0.15,
            "liquidity_factor": 0.1,
            "description": "Credit freeze causing 250bps cap rate expansion and forced foreclosures.",
        },
        StressScenario.RATE_SHOCK_2022: {
            "vacancy_shock": 0.0,
            "rent_growth_adj": 0.05,
            "cap_rate_shock": 0.015,
            "jump_intensity": 0.05,
            "jump_size": -0.05,
            "crypto_correlation": 0.4,
            "liquidity_factor": 0.7,
            "description": "Fed hiking cycle crushing valuations despite modest rent growth.",
        },
        StressScenario.CRYPTO_WINTER: {
            "vacancy_shock": 0.02,
            "rent_growth_adj": 0.0,
            "cap_rate_shock": 0.010,
            "jump_intensity": 0.10,
            "jump_size": -0.10,
            "token_discount": 0.35,
            "liquidity_factor": 0.2,
            "crypto_correlation": 0.8,
            "description": "RWA tokens trade at 35% discount to NAV despite stable underlying rents.",
        },
        StressScenario.STAGFLATION: {
            "vacancy_shock": 0.05,
            "rent_growth_adj": 0.10,
            "cap_rate_shock": 0.030,
            "jump_intensity": 0.08,
            "jump_size": -0.08,
            "operating_cost_shock": 0.20,
            "liquidity_factor": 0.6,
            "description": "1970s-style stagflation with rising rents but widening cap rates.",
        },
    }
    return base.get(scenario, base[StressScenario.BASE_CASE])


def estimate_ou_params(logR: np.ndarray, dt_years: float) -> Dict[str, float]:
    x = logR[:-1]
    y = logR[1:]
    if len(x) < 5:
        return {"kappa": 0.5, "theta": float(np.mean(logR)), "sigma": 0.10}
    b = np.cov(x, y, ddof=1)[0, 1] / np.var(x, ddof=1)
    a = y.mean() - b * x.mean()
    b = float(np.clip(b, 1e-6, 0.999999))
    kappa = -math.log(b) / dt_years
    theta = a / (1.0 - b)
    resid = y - (a + b * x)
    sigma_eps = float(np.std(resid, ddof=1))
    var_factor = (
        (1.0 - math.exp(-2.0 * kappa * dt_years)) / (2.0 * kappa)
        if kappa > 1e-12
        else dt_years
    )
    sigma = sigma_eps / math.sqrt(var_factor)
    return {"kappa": float(kappa), "theta": float(theta), "sigma": float(sigma)}


def make_county_adj(county_info, metro_short_name=None):
    """Create county adjustment dict with elasticity and pop growth"""
    if county_info:
        return {
            "elasticity": county_info["elasticity"],
            "stress_factor": county_info["elasticity"] / 0.3,
            "pop_growth": get_pop_growth_for_metro(metro_short_name) if metro_short_name else 0.05,
        }
    # Use metro-level data when no county selected
    if metro_short_name:
        metro_elasticity = get_elasticity_for_metro(metro_short_name)
        metro_pop_growth = get_pop_growth_for_metro(metro_short_name)
        return {
            "elasticity": metro_elasticity,
            "stress_factor": metro_elasticity / 0.3,
            "pop_growth": metro_pop_growth,
        }
    # Ultimate fallback
    return {"elasticity": 0.30, "stress_factor": 1.0, "pop_growth": 0.05}


def run_simulation_standalone(
    series: pd.Series,
    T_years: float,
    n_sims: int,
    units: int,
    vacancy: float,
    op_cost: float,
    discount: float,
    mode: EngineMode,
    scenario_params: Dict,
    county_adj: Dict,
    metro_short_name: str = None,
    seed: int = 42,
) -> Dict[str, Any]:
    rent_hist = series.values
    logR = np.log(rent_hist)
    dt_years = 1.0 / 12.0

    ou = estimate_ou_params(logR, dt_years)
    kappa, theta, sigma = ou["kappa"], ou["theta"], ou["sigma"]
    
    # =========================================================
    # Population Growth Integration
    # =========================================================
    pop_growth = county_adj.get("pop_growth", get_pop_growth_for_metro(metro_short_name) if metro_short_name else 0.05)
    
    # Population growth affects long-term rent growth (theta)
    pop_growth_impact = pop_growth * 0.5
    theta_adj = theta + pop_growth_impact
    
    # =========================================================
    # Supply Elasticity Integration
    # =========================================================
    elasticity = county_adj.get("elasticity", 0.30)
    
    # Elasticity affects rent volatility
    elasticity_vol_factor = 1 + (0.30 - elasticity)
    sigma_adj = sigma * max(0.5, min(1.5, elasticity_vol_factor))
    
    # Elasticity affects vacancy assumptions
    base_vacancy_adj = vacancy * (0.8 + elasticity * 0.5)

    mean_reversion = scenario_params.get("mean_reversion", 0) or 0
    kappa_adj = kappa * (1 + mean_reversion)
    
    # Apply scenario adjustments
    theta_final = theta_adj + scenario_params.get("rent_growth_adj", 0)
    
    vacancy_adj = min(
        base_vacancy_adj
        + scenario_params.get("vacancy_shock", 0) * county_adj.get("stress_factor", 1),
        0.50,
    )

    steps = int(T_years * 12)
    X0 = math.log(float(rent_hist[-1]) * 12.0)

    if mode == EngineMode.STRESS and scenario_params.get("jump_intensity", 0) > 0:
        jd = JumpDiffusionRent(
            scenario_params["jump_intensity"],
            scenario_params.get("jump_size", -0.20),
            0.10,
        )
        paths = jd.simulate(
            X0, kappa_adj, theta_final, sigma_adj, T_years, steps, n_sims, seed
        )
    else:
        rng = np.random.default_rng(seed)
        dt = T_years / steps
        exp_k = math.exp(-kappa_adj * dt)
        ou_var = (
            (1.0 - math.exp(-2.0 * kappa_adj * dt)) / (2.0 * kappa_adj)
            if kappa_adj > 1e-12
            else dt
        )
        ou_std = sigma_adj * math.sqrt(ou_var)
        paths = np.zeros((n_sims, steps + 1))
        paths[:, 0] = X0
        
        # Add progress bar for long simulations
        if steps > 100:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for t in range(steps):
                # Update progress
                if t % max(1, steps // 100) == 0:
                    progress = (t + 1) / steps
                    progress_bar.progress(progress)
                    status_text.text(f"Simulating step {t+1} of {steps} ({progress*100:.0f}%)...")
                
                paths[:, t + 1] = (
                    theta_final
                    + (paths[:, t] - theta_final) * exp_k
                    + ou_std * rng.standard_normal(n_sims)
                )
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
        else:
            for t in range(steps):
                paths[:, t + 1] = (
                    theta_final
                    + (paths[:, t] - theta_final) * exp_k
                    + ou_std * rng.standard_normal(n_sims)
                )

    rent_T = np.exp(paths[:, -1])
    gross = rent_T * units
    noi = gross * (1 - vacancy_adj) * (1 - op_cost)

    if mode == EngineMode.STRESS:
        cr = StochasticCapRate(
            discount, theta_r=discount + scenario_params.get("cap_rate_shock", 0)
        )
        rates = cr.simulate(T_years, steps, n_sims, seed + 1)
        price = noi / ((1 + rates[:, -1]) ** T_years)
        token_discount = scenario_params.get("token_discount", 0)
        if token_discount:
            price *= (1 - token_discount)
    else:
        price = noi / ((1 + discount) ** T_years)

    var95 = float(np.quantile(price, 0.05))
    
    # Store enhanced params for display
    ou_enhanced = {
        "kappa": kappa_adj,
        "theta_original": theta,
        "theta_adjusted": theta_final,
        "theta_pop_impact": pop_growth_impact,
        "sigma_original": sigma,
        "sigma_adjusted": sigma_adj,
        "elasticity": elasticity,
        "pop_growth": pop_growth
    }
    
    return {
        "price": price,
        "mean": float(np.mean(price)),
        "var95": var95,
        "cvar": float(np.mean(price[price <= var95])),
        "noi": noi,
        "ou_params": ou,
        "ou_enhanced": ou_enhanced,
    }


def run_simulation_with_core(
    series: pd.Series,
    T_years: float,
    n_sims: int,
    units: int,
    vacancy: float,
    op_cost: float,
    discount: float,
    county_adj: Dict,
    seed: int = 42,
) -> Dict[str, Any]:
    if not HAS_CORE or core_module is None:
        raise RuntimeError("Core module not available")
    result = core_module.run_simulation(
        series=series,
        T_years=T_years,
        n_sims=n_sims,
        units=units,
        vacancy=vacancy,
        op_cost=op_cost,
        discount=discount,
        mode=core_module.EngineMode.STANDARD,
        scenario_params=core_module.get_scenario_params(
            core_module.StressScenario.BASE_CASE
        ),
        county_adj=county_adj,
        seed=seed,
    )
    logR = np.log(series.values)
    dt_years = 1.0 / 12.0
    result["ou_params"] = estimate_ou_params(logR, dt_years)
    return result


def run_simulation(
    series: pd.Series,
    T_years: float,
    n_sims: int,
    units: int,
    vacancy: float,
    op_cost: float,
    discount: float,
    mode: EngineMode,
    scenario_params: Dict,
    county_adj: Dict,
    metro_short_name: str = None,
    seed: int = 42,
) -> Dict[str, Any]:
    if mode == EngineMode.STANDARD and use_core_for_standard():
        try:
            return run_simulation_with_core(
                series, T_years, n_sims, units, vacancy, op_cost, discount,
                county_adj, seed,
            )
        except Exception as e:
            st.warning(f"Core simulation failed ({e}), using standalone")
    return run_simulation_standalone(
        series, T_years, n_sims, units, vacancy, op_cost, discount,
        mode, scenario_params, county_adj, metro_short_name, seed,
    )


def calculate_risk_score(result: Dict) -> float:
    tail_ratio = (result["mean"] - result["cvar"]) / max(result["mean"], 1e-6)
    base_score = max(0.0, 1.0 - tail_ratio) * 100.0
    
    # Adjust risk score based on elasticity and pop growth
    ou_enhanced = result.get("ou_enhanced", {})
    elasticity = ou_enhanced.get("elasticity", 0.30)
    pop_growth = ou_enhanced.get("pop_growth", 0.05)
    
    # Lower elasticity (supply constrained) = higher risk
    elasticity_penalty = max(0, (0.30 - elasticity) * 50)
    
    # Negative pop growth = higher risk, positive = lower risk
    pop_bonus = max(-20, min(20, pop_growth * 100))
    
    final_score = base_score - elasticity_penalty + pop_bonus
    return max(0.0, min(100.0, final_score))


# =========================================================
# Stage 2 Export Functions
# =========================================================

def convert_to_serializable(obj):
    """Convert numpy/pandas types to Python native types for JSON serialization"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pd.Series):
        return obj.to_dict()
    elif isinstance(obj, pd.Timestamp):
        return str(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    return obj


def export_metro_for_stage2(
    metro_short_name: str,
    simulation_result: Dict[str, Any],
    county_info: Optional[Dict] = None,
    supply_bucket_thresholds: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Convert Stage 1 simulation output to Stage 2 market input format."""
    ou = simulation_result.get("ou_params", {})
    ou_enhanced = simulation_result.get("ou_enhanced", {})
    county = county_info or COUNTY_DATA.get(metro_short_name, [{}])[0]
    
    if supply_bucket_thresholds is None:
        supply_bucket_thresholds = {"very_inelastic": 0.15, "inelastic": 0.25, "elastic": 0.40}
    
    elasticity = county.get("elasticity", ou_enhanced.get("elasticity", 0.30))
    if elasticity < supply_bucket_thresholds["very_inelastic"]:
        supply_bucket = "very inelastic"
    elif elasticity < supply_bucket_thresholds["inelastic"]:
        supply_bucket = "inelastic"
    elif elasticity > supply_bucket_thresholds["elastic"]:
        supply_bucket = "elastic"
    else:
        supply_bucket = "neutral"
    
    risk_score = calculate_risk_score(simulation_result)
    if risk_score > 70:
        risk_bucket = "Low"
    elif risk_score > 40:
        risk_bucket = "Moderate"
    else:
        risk_bucket = "High"
    
    # Use enhanced theta if available
    theta = ou_enhanced.get("theta_adjusted", ou.get("theta", 0.03))
    yoy_rent_growth = max(-0.02, min(theta, 0.15))
    
    pop_growth = ou_enhanced.get("pop_growth", get_pop_growth_for_metro(metro_short_name))
    
    return {
        "yoy_rent_growth": yoy_rent_growth,
        "rent_volatility": ou_enhanced.get("sigma_adjusted", ou.get("sigma", 0.08)),
        "trend_label": "expanding" if theta > 0 else "contracting",
        "pci_2023": county.get("pci"),
        "metro_elasticity": elasticity,
        "supply_bucket": supply_bucket,
        "pop_growth": pop_growth,
        "risk_score": risk_score,
        "risk_bucket": risk_bucket,
        "var95": simulation_result.get("var95"),
        "cvar": simulation_result.get("cvar"),
        "ou_kappa": ou.get("kappa"),
        "ou_theta_original": ou.get("theta"),
        "ou_theta_adjusted": ou_enhanced.get("theta_adjusted"),
        "pop_growth_impact": ou_enhanced.get("theta_pop_impact"),
    }


def save_stage1_results(
    metro_short_name: str,
    result: Dict,
    county_info: Optional[Dict] = None,
    supply_bucket_thresholds: Optional[Dict] = None,
    scenario_name: str = "analysis"
) -> Path:
    """Save Stage 1 results to JSON file for Stage 2."""
    market_data = export_metro_for_stage2(metro_short_name, result, county_info, supply_bucket_thresholds)
    
    export_data = {
        "metro_name": metro_short_name,
        "timestamp": datetime.now().isoformat(),
        "scenario": scenario_name,
        "simulation_results": {
            "mean": float(result["mean"]),
            "var95": float(result["var95"]),
            "cvar": float(result["cvar"]),
            "risk_score": calculate_risk_score(result),
            "ou_params": {
                "kappa": float(result["ou_params"]["kappa"]),
                "theta": float(result["ou_params"]["theta"]),
                "sigma": float(result["ou_params"]["sigma"])
            },
            "ou_enhanced": result.get("ou_enhanced", {})
        },
        "county_info": county_info,
        "market_data": market_data,
        "supply_bucket_thresholds": supply_bucket_thresholds
    }
    
    filename = STAGE1_OUTPUT_DIR / f"{metro_short_name.lower()}_{scenario_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(export_data, f, indent=2, default=convert_to_serializable)
    
    latest_file = STAGE1_OUTPUT_DIR / f"{metro_short_name.lower()}_latest.json"
    with open(latest_file, 'w') as f:
        json.dump(export_data, f, indent=2, default=convert_to_serializable)
    
    return filename


def save_comparison_results(
    metro_a_short: str,
    result_a: Dict,
    county_a: Optional[Dict],
    metro_b_short: str,
    result_b: Dict,
    county_b: Optional[Dict],
    supply_bucket_thresholds: Optional[Dict] = None,
    scenario_name: str = "comparison"
) -> Path:
    """Save comparison results for both metros."""
    market_data_a = export_metro_for_stage2(metro_a_short, result_a, county_a, supply_bucket_thresholds)
    market_data_b = export_metro_for_stage2(metro_b_short, result_b, county_b, supply_bucket_thresholds)
    
    comparison_data = {
        "timestamp": datetime.now().isoformat(),
        "scenario": scenario_name,
        "metros": {
            metro_a_short: {
                "simulation_results": {
                    "mean": float(result_a["mean"]),
                    "var95": float(result_a["var95"]),
                    "cvar": float(result_a["cvar"]),
                    "risk_score": calculate_risk_score(result_a)
                },
                "county_info": county_a,
                "market_data": market_data_a
            },
            metro_b_short: {
                "simulation_results": {
                    "mean": float(result_b["mean"]),
                    "var95": float(result_b["var95"]),
                    "cvar": float(result_b["cvar"]),
                    "risk_score": calculate_risk_score(result_b)
                },
                "county_info": county_b,
                "market_data": market_data_b
            }
        },
        "supply_bucket_thresholds": supply_bucket_thresholds
    }
    
    comparison_file = STAGE1_OUTPUT_DIR / f"comparison_{metro_a_short}_{metro_b_short}_{scenario_name}.json"
    with open(comparison_file, 'w') as f:
        json.dump(comparison_data, f, indent=2, default=convert_to_serializable)
    
    latest_comparison = STAGE1_OUTPUT_DIR / "latest_comparison.json"
    with open(latest_comparison, 'w') as f:
        json.dump(comparison_data, f, indent=2, default=convert_to_serializable)
    
    return comparison_file


# =========================================================
# UI Components
# =========================================================

def render_county_selector(
    metro_short_name: str, key_suffix: str = ""
) -> Optional[Dict]:
    counties = COUNTY_DATA.get(metro_short_name, [])
    if not counties:
        return None
    county_names = [c["name"] for c in counties]
    selected = st.selectbox(
        f"County in {metro_short_name}",
        county_names,
        key=f"county_{metro_short_name}_{key_suffix}",
    )
    county_info = next(c for c in counties if c["name"] == selected)
    col1, col2, col3 = st.columns(3)
    col1.metric("PCI", f"${county_info['pci']:,}")
    col2.metric("Elasticity", f"{county_info['elasticity']:.2f}")
    tier_colors = {
        "Core Urban": "#e74c3c",
        "Suburban": "#f39c12",
        "Periphery": "#27ae60",
    }
    color = tier_colors.get(county_info["tier"], "#666")
    col3.markdown(
        f"<div style='background-color:{color}20; padding:10px; "
        f"border-radius:5px; border-left:4px solid {color}; text-align:center;'>"
        f"<b>{county_info['tier']}</b></div>",
        unsafe_allow_html=True,
    )
    return county_info


def render_metro_card(
    short_name: str,
    result: Dict,
    county_info: Optional[Dict],
    col,
    show_risk_score: bool = True,
    supply_bucket_thresholds: Optional[Dict] = None,
):
    with col:
        st.subheader(short_name)
        c1, c2 = st.columns(2)
        c1.metric("Mean Price", f"${result['mean']:,.0f}")
        c2.metric("VaR95", f"${result['var95']:,.0f}")
        if show_risk_score:
            score = calculate_risk_score(result)
            st.metric("Risk Score", f"{score:.0f}/100")
        if county_info:
            st.caption(
                f"**{county_info['tier']}** | "
                f"PCI: ${county_info['pci']:,} | "
                f"Elasticity: {county_info['elasticity']}"
            )
        
        # Display enhanced parameters
        ou_enhanced = result.get("ou_enhanced", {})
        if ou_enhanced:
            with st.expander("📊 Enhanced Parameters"):
                st.write(f"Population Growth: {ou_enhanced.get('pop_growth', 0)*100:.1f}%")
                st.write(f"Supply Elasticity: {ou_enhanced.get('elasticity', 0):.3f}")
                st.write(f"Pop Growth Impact on Rents: {ou_enhanced.get('theta_pop_impact', 0)*100:.2f}%")
                st.write(f"Adjusted Volatility: {ou_enhanced.get('sigma_adjusted', 0)*100:.1f}% (original: {ou_enhanced.get('sigma_original', 0)*100:.1f}%)")
        
        if "ou_params" in result:
            ou = result["ou_params"]
            with st.expander("📈 OU Parameters"):
                st.write(f"κ (mean reversion): {ou['kappa']:.3f}")
                st.write(f"θ (long-run mean):   {ou['theta']:.3f}")
                st.write(f"σ (volatility):      {ou['sigma']:.3f}")
        
        # Export to Stage 2
        with st.expander("📤 Export to Stage 2"):
            market_data = export_metro_for_stage2(short_name, result, county_info, supply_bucket_thresholds)
            st.json(market_data)
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                st.download_button(
                    label="📥 Download JSON",
                    data=json.dumps(market_data, indent=2),
                    file_name=f"{short_name.lower()}_market.json",
                    mime="application/json",
                    key=f"download_{short_name}"
                )
            with col_btn2:
                if st.button(f"💾 Save to Stage 2", key=f"save_{short_name}"):
                    saved_path = save_stage1_results(short_name, result, county_info, supply_bucket_thresholds)
                    st.success(f"✅ Saved to {saved_path.name}")


def render_comparison_table(res_a: Dict, res_b: Dict, metro_a_short: str, metro_b_short: str):
    """Enhanced comparison table."""
    comparison_df = pd.DataFrame([
        {"Metric": "Mean Token Price", metro_a_short: res_a["mean"], metro_b_short: res_b["mean"]},
        {"Metric": "VaR95 (Risk)", metro_a_short: res_a["var95"], metro_b_short: res_b["var95"]},
        {"Metric": "CVaR (Tail Risk)", metro_a_short: res_a["cvar"], metro_b_short: res_b["cvar"]},
        {"Metric": "Risk Score", metro_a_short: calculate_risk_score(res_a), metro_b_short: calculate_risk_score(res_b)},
    ])
    st.dataframe(comparison_df.set_index("Metric"), use_container_width=True)


def render_stress_results_table(s_a_res: Dict, s_b_res: Dict, metro_a_short: str, metro_b_short: str, scenario: StressScenario):
    """Enhanced stress test results table."""
    results_df = pd.DataFrame([
        {"Metro": metro_a_short, "Mean Price": s_a_res["mean"], "VaR95": s_a_res["var95"], 
         "CVaR": s_a_res["cvar"], "Risk Score": calculate_risk_score(s_a_res)},
        {"Metro": metro_b_short, "Mean Price": s_b_res["mean"], "VaR95": s_b_res["var95"], 
         "CVaR": s_b_res["cvar"], "Risk Score": calculate_risk_score(s_b_res)},
    ])
    st.dataframe(results_df.set_index("Metro"), use_container_width=True)


def show_saved_results_status():
    """Display saved Stage 1 results."""
    if STAGE1_OUTPUT_DIR.exists():
        saved_files = list(STAGE1_OUTPUT_DIR.glob("*.json"))
        if saved_files:
            with st.expander("📁 Saved Stage 1 Results"):
                st.write(f"Found {len(saved_files)} saved result files:")
                for f in sorted(saved_files, reverse=True)[:5]:
                    st.code(f.name)
                st.caption(f"Location: `{STAGE1_OUTPUT_DIR}`")


# =========================================================
# Main App
# =========================================================

def main():
    # Apply custom styling
    apply_custom_styling()
    
    st.title("🏘️ Kejafi Research Engine")
    st.markdown(
        "Stage 1: Metro-level risk analysis and stress testing for tokenized real estate. "
        "Compare metros, analyze sub-markets, and run historical stress scenarios. "
        "Export results to Stage 2 for single-asset tokenization.\n\n"
        "**Enhanced with Population Growth & Supply Elasticity Integration**"
    )
    
    show_saved_results_status()

    if HAS_CORE:
        st.success("✅ Using metro_lab_core backend for Standard mode")
    else:
        st.info("ℹ️ Running in standalone mode")

    st.sidebar.header("Engine Configuration")
    
    # Add keyboard shortcuts help
    with st.sidebar.expander("⌨️ Keyboard Shortcuts"):
        st.markdown("""
        - `Ctrl+R` - Run Analysis
        - `Ctrl+S` - Save Results  
        - `Ctrl+E` - Export Data
        - `?` - Show this help
        """)
    
    # Add performance tip
    with st.sidebar.expander("⚡ Performance Tips"):
        st.markdown("""
        - Reduce simulations to 1,000 for faster results
        - Use Metro-only mode (faster than County-level)
        - Stress Lab with jumps takes longer
        - Results are cached for 1 hour
        """)

    engine_options = list(EngineMode)
    engine_index_key = "engine_mode_index"

    if engine_index_key not in st.session_state:
        st.session_state[engine_index_key] = 0

    mode_index = st.sidebar.radio(
        "Engine Mode",
        options=range(len(engine_options)),
        index=st.session_state[engine_index_key],
        format_func=lambda i: engine_options[i].value,
        key=engine_index_key,
    )
    mode = engine_options[mode_index]

    use_core = False
    if mode == EngineMode.STANDARD and HAS_CORE:
        use_core = st.sidebar.checkbox(
            "Use stable core backend",
            value=True,
            key="use_core_backend",
        )
        if not use_core:
            st.sidebar.warning("Using standalone implementation")

    if mode == EngineMode.STANDARD:
        st.sidebar.info(
            "**Standard Mode**: OU process, fixed cap rates, mean reversion.\n"
            "Enhanced with population growth and elasticity adjustments."
        )
    else:
        st.sidebar.info(
            "**Stress Lab**: Jump-diffusion, stochastic rates, liquidity crises."
        )

    st.sidebar.header("Geography")
    geo_mode = st.sidebar.radio("Analysis Level", ["MSA (Metro)", "MSA + County"])
    use_county = geo_mode == "MSA + County"

    # Supply bucket thresholds (adjustable)
    st.sidebar.header("Supply Bucket Mapping")
    very_inelastic_thresh = st.sidebar.number_input(
        "Very Inelastic (<)", value=0.15, min_value=0.01, max_value=0.50, step=0.01,
        help="Elasticity below this → 'very inelastic'"
    )
    inelastic_thresh = st.sidebar.number_input(
        "Inelastic (<)", value=0.25, min_value=0.01, max_value=0.50, step=0.01,
        help="Elasticity below this (but above very inelastic) → 'inelastic'"
    )
    elastic_thresh = st.sidebar.number_input(
        "Elastic (>)", value=0.40, min_value=0.01, max_value=0.50, step=0.01,
        help="Elasticity above this → 'elastic'"
    )
    supply_thresholds = {
        "very_inelastic": very_inelastic_thresh,
        "inelastic": inelastic_thresh,
        "elastic": elastic_thresh,
    }

    default_a = 0
    default_b = min(1, len(METRO_LIST) - 1)
    for short, full in FOUND_METROS.items():
        if short == "Charlotte":
            default_a = list(FOUND_METROS.values()).index(full)
        if short == "Atlanta":
            default_b = list(FOUND_METROS.values()).index(full)

    col1, col2 = st.columns(2)
    with col1:
        city_a = st.selectbox("Metro A", METRO_LIST, index=default_a)
        metro_a_short = METRO_COUNTIES[city_a]["short_name"]
        county_a = render_county_selector(metro_a_short, "a") if use_county else None

    with col2:
        city_b = st.selectbox("Metro B", METRO_LIST, index=default_b)
        metro_b_short = METRO_COUNTIES[city_b]["short_name"]
        county_b = render_county_selector(metro_b_short, "b") if use_county else None

    st.sidebar.header("Simulation Parameters")
    T_years = st.sidebar.slider("Horizon (years)", 0.25, 10.0, 2.0, 0.25)
    n_sims = st.sidebar.select_slider(
        "Simulations", [1000, 5000, 10000, 25000], value=5000
    )

    st.sidebar.header("Property Assumptions")
    units = st.sidebar.number_input("Units", 1, 10000, 100)
    base_vacancy = st.sidebar.slider("Base Vacancy", 0.0, 0.30, 0.05, 0.01)
    op_cost = st.sidebar.slider("Op Cost Ratio", 0.0, 0.50, 0.35, 0.01)
    discount = st.sidebar.slider("Cap Rate (Discount)", 0.03, 0.12, 0.055, 0.005)

    amm_params = None
    if mode == EngineMode.STRESS:
        st.sidebar.header("AMM Parameters")
        tvl = st.sidebar.number_input("Pool TVL ($)", 50000, 10000000, 1000000, 50000)
        redemption = st.sidebar.number_input("Redemption Size ($)", 5000, 500000, 100000, 5000)
        fee = st.sidebar.slider("AMM Fee", 0.0, 0.01, 0.003, 0.0005)
        amm_params = {"tvl": tvl, "redemption": redemption, "fee": fee}

    # Create county adjustment with metro name for fallback
    county_adj_a = make_county_adj(county_a, metro_a_short)
    county_adj_b = make_county_adj(county_b, metro_b_short)

    s_a, s_b = get_series(city_a), get_series(city_b)
    if s_a is None or s_b is None:
        st.error("Data loading failed for one or both metros.")
        st.stop()

    df_compare = pd.concat(
        {metro_a_short: s_a, metro_b_short: s_b},
        axis=1,
    ).dropna()

    if mode == EngineMode.STANDARD:
        render_standard_mode(
            df_compare, metro_a_short, metro_b_short,
            s_a, s_b, city_a, city_b,
            T_years, n_sims, units, base_vacancy, op_cost, discount,
            county_adj_a, county_adj_b, county_a, county_b,
            supply_thresholds,
        )
    else:
        if not amm_params:
            amm_params = {"tvl": 1_000_000.0, "redemption": 100_000.0, "fee": 0.003}
        render_stress_mode(
            df_compare, metro_a_short, metro_b_short,
            s_a, s_b, city_a, city_b,
            T_years, n_sims, units, base_vacancy, op_cost, discount,
            county_adj_a, county_adj_b, county_a, county_b,
            amm_params, supply_thresholds,
        )

    st.caption(
        f"Kejafi Research Engine | Mode: {mode.value} | "
        f"{'County-level' if use_county else 'Metro-level'} | "
        f"Backend: {'metro_lab_core' if use_core and mode == EngineMode.STANDARD else 'standalone'} | "
        f"Population Growth & Elasticity Integrated"
    )


def render_standard_mode(
    df_compare, metro_a_short, metro_b_short,
    s_a, s_b, city_a, city_b,
    T_years, n_sims, units,
    vacancy, op_cost, discount,
    county_adj_a, county_adj_b,
    county_a, county_b,
    supply_thresholds,
):
    st.header(f"Comparing: {metro_a_short} vs {metro_b_short}")
    
    # Get metro-level data for display (using the already-loaded county_adj which has pop_growth)
    pop_a = county_adj_a.get("pop_growth", get_pop_growth_for_metro(metro_a_short))
    pop_b = county_adj_b.get("pop_growth", get_pop_growth_for_metro(metro_b_short))
    elastic_a = county_adj_a.get("elasticity", get_elasticity_for_metro(metro_a_short))
    elastic_b = county_adj_b.get("elasticity", get_elasticity_for_metro(metro_b_short))
    
    col_info1, col_info2 = st.columns(2)
    with col_info1:
        st.info(f"📊 **{metro_a_short}**\n- Population Growth: {pop_a*100:.1f}%\n- Supply Elasticity: {elastic_a:.3f}")
    with col_info2:
        st.info(f"📊 **{metro_b_short}**\n- Population Growth: {pop_b*100:.1f}%\n- Supply Elasticity: {elastic_b:.3f}")
    
    if county_a or county_b:
        st.subheader(
            f"Sub-markets: {county_a['name'] if county_a else 'Full MSA'} vs "
            f"{county_b['name'] if county_b else 'Full MSA'}"
        )

    st.line_chart(df_compare)

    if st.button("🚀 Run Analysis", type="primary"):
        with st.spinner("Running standard analysis with population growth and elasticity adjustments..."):
            base_params = get_scenario_params(StressScenario.BASE_CASE)

            res_a = run_simulation(
                df_compare[metro_a_short], T_years, n_sims, units,
                vacancy, op_cost, discount,
                EngineMode.STANDARD, base_params, county_adj_a, metro_a_short, 123,
            )
            res_b = run_simulation(
                df_compare[metro_b_short], T_years, n_sims, units,
                vacancy, op_cost, discount,
                EngineMode.STANDARD, base_params, county_adj_b, metro_b_short, 456,
            )

            # Store in session state
            st.session_state["stage1_result_a"] = res_a
            st.session_state["stage1_result_b"] = res_b
            st.session_state["stage1_county_a"] = county_a
            st.session_state["stage1_county_b"] = county_b
            st.session_state["stage1_metro_a_short"] = metro_a_short
            st.session_state["stage1_metro_b_short"] = metro_b_short
            
            # Save to files
            save_comparison_results(
                metro_a_short, res_a, county_a,
                metro_b_short, res_b, county_b,
                supply_thresholds,
                "standard_analysis"
            )
            
            st.success("✅ Results saved to Stage 2!")

            col1, col2 = st.columns(2)
            render_metro_card(
                metro_a_short, res_a, county_a, col1,
                supply_bucket_thresholds=supply_thresholds,
            )
            render_metro_card(
                metro_b_short, res_b, county_b, col2,
                supply_bucket_thresholds=supply_thresholds,
            )

            st.subheader("Comparison Summary")
            render_comparison_table(res_a, res_b, metro_a_short, metro_b_short)
            
            # Add export buttons
            st.subheader("📊 Export Results")
            
            # Create comparison DataFrame
            comp_df = pd.DataFrame([
                {"Metric": "Mean Token Price", metro_a_short: res_a["mean"], metro_b_short: res_b["mean"]},
                {"Metric": "VaR95 (Risk)", metro_a_short: res_a["var95"], metro_b_short: res_b["var95"]},
                {"Metric": "CVaR (Tail Risk)", metro_a_short: res_a["cvar"], metro_b_short: res_b["cvar"]},
                {"Metric": "Risk Score", metro_a_short: calculate_risk_score(res_a), metro_b_short: calculate_risk_score(res_b)},
            ])
            
            col_exp1, col_exp2, col_exp3 = st.columns(3)
            
            with col_exp1:
                csv_data = comp_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download CSV",
                    data=csv_data,
                    file_name=f"comparison_{metro_a_short}_{metro_b_short}.csv",
                    mime="text/csv",
                    key="export_csv"
                )
            
            with col_exp2:
                export_json = {
                    "timestamp": datetime.now().isoformat(),
                    "metro_a": {"name": metro_a_short, "mean": res_a["mean"], "var95": res_a["var95"], "risk_score": calculate_risk_score(res_a)},
                    "metro_b": {"name": metro_b_short, "mean": res_b["mean"], "var95": res_b["var95"], "risk_score": calculate_risk_score(res_b)},
                    "ou_enhanced_a": res_a.get("ou_enhanced", {}),
                    "ou_enhanced_b": res_b.get("ou_enhanced", {})
                }
                json_str = json.dumps(export_json, indent=2, default=str)
                st.download_button(
                    label="📥 Download JSON",
                    data=json_str,
                    file_name=f"comparison_{metro_a_short}_{metro_b_short}.json",
                    mime="application/json",
                    key="export_json"
                )
            
            with col_exp3:
                st.info("💡 Results saved to stage1_output/ folder automatically")


def render_stress_mode(
    df_compare, metro_a_short, metro_b_short,
    s_a, s_b, city_a, city_b,
    T_years, n_sims, units,
    vacancy, op_cost, discount,
    county_adj_a, county_adj_b,
    county_a, county_b,
    amm_params,
    supply_thresholds,
):
    if not amm_params:
        amm_params = {"tvl": 1_000_000.0, "redemption": 100_000.0, "fee": 0.003}

    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Metro Analysis", "⚠️ Stress Scenarios", "💧 Liquidity Crisis", "🔮 Oracle Risk",
    ])

    base_params = get_scenario_params(StressScenario.BASE_CASE)

    with tab1:
        st.header("Base Case Analysis")
        
        # Get metro-level data for display
        pop_a = county_adj_a.get("pop_growth", get_pop_growth_for_metro(metro_a_short))
        pop_b = county_adj_b.get("pop_growth", get_pop_growth_for_metro(metro_b_short))
        elastic_a = county_adj_a.get("elasticity", get_elasticity_for_metro(metro_a_short))
        elastic_b = county_adj_b.get("elasticity", get_elasticity_for_metro(metro_b_short))
        
        col_info1, col_info2 = st.columns(2)
        with col_info1:
            st.info(f"📊 **{metro_a_short}**\n- Population Growth: {pop_a*100:.1f}%\n- Supply Elasticity: {elastic_a:.3f}")
        with col_info2:
            st.info(f"📊 **{metro_b_short}**\n- Population Growth: {pop_b*100:.1f}%\n- Supply Elasticity: {elastic_b:.3f}")
        
        st.line_chart(df_compare)

        if st.button("Run Base Case", key="base", type="primary"):
            with st.spinner("Running base case simulation with enhanced parameters..."):
                res_a = run_simulation(
                    df_compare[metro_a_short], T_years, n_sims, units,
                    vacancy, op_cost, discount,
                    EngineMode.STRESS, base_params, county_adj_a, metro_a_short, 123,
                )
                res_b = run_simulation(
                    df_compare[metro_b_short], T_years, n_sims, units,
                    vacancy, op_cost, discount,
                    EngineMode.STRESS, base_params, county_adj_b, metro_b_short, 456,
                )
                st.session_state["base_results"] = (res_a, res_b)
                st.session_state["stage1_result_a"] = res_a
                st.session_state["stage1_result_b"] = res_b
                st.session_state["stage1_county_a"] = county_a
                st.session_state["stage1_county_b"] = county_b
                st.session_state["stage1_metro_a_short"] = metro_a_short
                st.session_state["stage1_metro_b_short"] = metro_b_short
                
                save_comparison_results(
                    metro_a_short, res_a, county_a,
                    metro_b_short, res_b, county_b,
                    supply_thresholds,
                    "stress_base_case"
                )
                
                st.success("✅ Base case results saved to Stage 2!")

                col1, col2 = st.columns(2)
                render_metro_card(
                    metro_a_short, res_a, county_a, col1,
                    supply_bucket_thresholds=supply_thresholds,
                )
                render_metro_card(
                    metro_b_short, res_b, county_b, col2,
                    supply_bucket_thresholds=supply_thresholds,
                )

    with tab2:
        st.header("Historical Stress Scenarios")
        scenario = st.selectbox(
            "Select Scenario", list(StressScenario), format_func=lambda x: x.value
        )
        params = get_scenario_params(scenario, county_adj_a["elasticity"])
        
        st.info(f"**{scenario.value}**: {params['description']}")
        
        with st.expander("📋 Scenario Parameters"):
            param_df = pd.DataFrame([
                {"Parameter": "Vacancy Shock", "Value": f"{params.get('vacancy_shock', 0)*100:.1f}%"},
                {"Parameter": "Rent Growth Adjustment", "Value": f"{params.get('rent_growth_adj', 0)*100:.1f}%"},
                {"Parameter": "Cap Rate Shock", "Value": f"{params.get('cap_rate_shock', 0)*100:.1f}%"},
                {"Parameter": "Jump Intensity", "Value": f"{params.get('jump_intensity', 0)*100:.1f}%"},
                {"Parameter": "Liquidity Factor", "Value": f"{params.get('liquidity_factor', 1)*100:.0f}%"},
            ])
            st.dataframe(param_df.set_index("Parameter"), use_container_width=True, hide_index=False)

        if st.button("Run Stress Test", type="primary"):
            with st.spinner(f"Simulating {scenario.value} with pop growth & elasticity..."):
                s_a_res = run_simulation(
                    df_compare[metro_a_short], T_years, n_sims, units,
                    vacancy, op_cost, discount,
                    EngineMode.STRESS, params, county_adj_a, metro_a_short, 123,
                )
                s_b_res = run_simulation(
                    df_compare[metro_b_short], T_years, n_sims, units,
                    vacancy, op_cost, discount,
                    EngineMode.STRESS, params, county_adj_b, metro_b_short, 456,
                )
                
                save_comparison_results(
                    metro_a_short, s_a_res, county_a,
                    metro_b_short, s_b_res, county_b,
                    supply_thresholds,
                    f"stress_{scenario.name.lower()}"
                )
                
                st.success(f"✅ {scenario.value} results saved to Stage 2!")

                render_stress_results_table(s_a_res, s_b_res, metro_a_short, metro_b_short, scenario)

                fig, ax = plt.subplots(figsize=(10, 6))
                ax.hist(s_a_res["price"], bins=50, alpha=0.6, label=metro_a_short, color='#3498db')
                ax.hist(s_b_res["price"], bins=50, alpha=0.6, label=metro_b_short, color='#e74c3c')
                ax.axvline(s_a_res["var95"], color='#2980b9', linestyle="--", alpha=0.7, label=f"{metro_a_short} VaR95")
                ax.axvline(s_b_res["var95"], color='#c0392b', linestyle="--", alpha=0.7, label=f"{metro_b_short} VaR95")
                ax.set_title(f"Price Distribution: {scenario.value}", fontsize=14, fontweight='bold')
                ax.set_xlabel("Token Price ($)")
                ax.set_ylabel("Frequency")
                ax.legend()
                ax.grid(True, alpha=0.3)

                fname = FIG_DIR / f"stress_distribution_{metro_a_short}_{metro_b_short}_{scenario.name}.png"
                fig.savefig(fname, dpi=300, bbox_inches="tight")
                st.pyplot(fig)
                
                with open(fname, "rb") as file:
                    st.download_button(
                        label="📥 Download Plot",
                        data=file,
                        file_name=f"stress_test_{scenario.name}.png",
                        mime="image/png"
                    )

    with tab3:
        st.header("Redemption Queue Simulator")
        st.markdown("Simulate how different crisis levels affect token pricing and redemption mechanics.")

        crisis_level = st.radio(
            "Crisis Level",
            ["Minor (5%)", "Stress (20%)", "Bank Run (50%)"],
            horizontal=True,
        )
        crisis_map = {"Minor (5%)": "minor", "Stress (20%)": "stress", "Bank Run (50%)": "bank_run"}

        if st.button("Simulate Crisis", key="crisis", type="primary"):
            if "base_results" not in st.session_state:
                st.error("⚠️ Please run Base Case in 'Metro Analysis' tab first!")
            else:
                base_a, base_b = st.session_state["base_results"]
                token_p = TokenizationParams(
                    amm_tvl=amm_params.get("tvl", 1_000_000.0),
                    redemption_gate_threshold=0.15,
                )
                red_model = RedemptionQueueModel(token_p)

                crisis_a = red_model.simulate_crisis(base_a["price"], crisis_map[crisis_level])
                crisis_b = red_model.simulate_crisis(base_b["price"], crisis_map[crisis_level])

                st.subheader("Crisis Impact Analysis")
                c1, c2 = st.columns(2)
                
                for c, name, crisis in [(c1, metro_a_short, crisis_a), (c2, metro_b_short, crisis_b)]:
                    with c:
                        st.markdown(f"### {name}")
                        metric_col1, metric_col2 = st.columns(2)
                        metric_col1.metric("Redemption Demand", f"{crisis['demand']*100:.0f}%")
                        metric_col2.metric("Total Haircut", f"{crisis['total_haircut']*100:.1f}%", 
                                          delta="GATED" if crisis["gated"] else "ACTIVE")
                        st.metric("NAV Discount", f"{crisis['nav_discount']*100:.1f}%")
                        st.metric("AMM Slippage", f"{crisis['amm_slippage']*100:.1f}%")
                        st.metric("Exit Price", f"${crisis['exit_price']:,.0f}", 
                                 delta=f"{((crisis['exit_price']/base_a['mean'])-1)*100:.1f}%")
                        st.metric("Recovery Period", f"{crisis['recovery_months']} months")

                st.subheader("Value Destruction Waterfall")
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

                for ax, name, base, crisis in [(ax1, metro_a_short, base_a, crisis_a), (ax2, metro_b_short, base_b, crisis_b)]:
                    components = ["Base Value", "NAV Discount", "AMM Slippage", "Final Price"]
                    base_value = base["mean"]
                    nav_loss = -base_value * crisis["nav_discount"]
                    amm_loss = -base_value * crisis["amm_slippage"]
                    final_value = crisis["exit_price"]
                    values = [base_value, nav_loss, amm_loss, final_value]
                    colors = ['#2ecc71', '#e74c3c', '#f39c12', '#3498db']
                    bars = ax.bar(components, values, color=colors, alpha=0.7, edgecolor='black', linewidth=1)
                    ax.set_title(name, fontsize=12, fontweight='bold')
                    ax.axhline(0, color='black', linewidth=0.5)
                    ax.set_ylabel("Value ($)")
                    for bar, val in zip(bars, values):
                        if val != 0:
                            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + (base_value*0.02),
                                   f'${val:,.0f}', ha='center', va='bottom', fontsize=9)

                plt.tight_layout()
                fname = FIG_DIR / f"liquidity_waterfall_{metro_a_short}_{metro_b_short}_{crisis_map[crisis_level]}.png"
                fig.savefig(fname, dpi=300, bbox_inches="tight")
                st.pyplot(fig)
                
                with open(fname, "rb") as file:
                    st.download_button(
                        label="📥 Download Waterfall Chart",
                        data=file,
                        file_name=f"liquidity_waterfall_{crisis_map[crisis_level]}.png",
                        mime="image/png",
                        key="download_waterfall"
                    )

    with tab4:
        st.header("Oracle Risk Analysis")
        st.markdown("Analyze how data feed disruptions or manipulation could impact token pricing.")
        
        oracle_cond = st.selectbox(
            "Data Condition", 
            ["Normal", "Stale (30d)", "Stale (90d)", "Manipulated"],
            help="Simulate different oracle failure modes"
        )

        stale_days = {"Normal": 0, "Stale (30d)": 30, "Stale (90d)": 90, "Manipulated": 0}
        days = stale_days[oracle_cond]

        if days > 0:
            uncertainty = 0.05 * np.exp(days / 365 * 0.5)
            col1, col2, col3 = st.columns(3)
            col1.metric("Pricing Uncertainty", f"{uncertainty*100:.1f}%")
            col2.metric("Stale Data Age", f"{days} days")
            col3.metric("Confidence Interval", f"±{uncertainty*2*100:.1f}%")
            current_rent = s_a.iloc[-1]
            st.info(f"📊 Implied rent range: **${current_rent*(1-2*uncertainty):.0f}** - **${current_rent*(1+2*uncertainty):.0f}**")
            st.warning(f"⚠️ Stale data for {days} days increases pricing uncertainty significantly!")

        if oracle_cond == "Manipulated":
            st.error("🚨 **CRITICAL**: Detected 15% false premium in oracle feed. Correction crash imminent!")
            st.markdown("""
            **Impact Assessment:**
            - Token price inflated by 15% artificially
            - Expected correction: 20-25% drop
            - Liquidity providers at risk
            - Emergency appraisal triggered
            """)
            with st.expander("🛡️ Emergency Response Protocol"):
                st.markdown("""
                1. **Freeze** token minting/burning
                2. **Trigger** emergency appraisal ($50k cost)
                3. **Reset** oracle to verified feed
                4. **Revalue** portfolio at fair market value
                5. **Compensate** affected users from insurance fund
                """)


if __name__ == "__main__":
    main()
