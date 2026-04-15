# KEJAFI — Tokenized Real Estate Platform

<div align="center">

![Kejafi](https://img.shields.io/badge/KEJAFI-Tokenized%20Real%20Estate-028090?style=for-the-badge&labelColor=0D1B3E)

[![Stage 1](https://img.shields.io/badge/Stage%201-Metro%20Risk%20Analysis-028090?style=flat-square)](https://kejafi-stage1.streamlit.app)
[![Stage 2](https://img.shields.io/badge/Stage%202-Property%20Tokenization-00A896?style=flat-square)](https://kejafi-stage2.streamlit.app)
[![Stage 3](https://img.shields.io/badge/Stage%203-Portfolio%20Management-1DBF73?style=flat-square)](https://kejafi-stage3.streamlit.app)
[![API](https://img.shields.io/badge/API-FastAPI-009688?style=flat-square)](https://kejafi-platform.onrender.com/docs)
[![Network](https://img.shields.io/badge/Network-Sepolia%20Testnet-F5A623?style=flat-square)](https://sepolia.etherscan.io)
[![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)

**An end-to-end platform bridging institutional-grade quantitative finance with live DeFi infrastructure.**

*Ornstein-Uhlenbeck rent modelling → ERC-20 token deployment → Monte Carlo portfolio analytics*

[**Live Demo**](https://kejafi-stage2.streamlit.app) · [**Research Paper**](paper/) · [**API Docs**](https://kejafi-platform.onrender.com/docs) · [**Frontend**](https://frontend-lilac-three-92.vercel.app)

</div>

---

## What is Kejafi?

Kejafi addresses three fundamental problems in real estate investment:

| Problem | Traditional Reality | Kejafi Solution |
|---|---|---|
| **Illiquidity** | 3–6 months to sell | Continuous AMM liquidity via Uniswap V3 |
| **High Barriers** | $100K+ minimum | Fractional ERC-20 token ownership |
| **No Analytics** | No standardized risk metrics | OU stochastic modelling + Monte Carlo VaR |

The three stages are sequentially integrated — Stage 1 cap rates feed Stage 2 pricing, and Stage 2 tokens form the Stage 3 portfolio universe.

```
stage1.py  →  Metro Risk Analysis  (OU Process, Risk Score)
                    │ cap rates + volatility
                    ▼
stage2.py  →  Property Tokenization  (NOI Valuation, ERC-20, Uniswap V3)
                    │ tokenized assets
                    ▼
stage3.py  →  Portfolio Management  (Monte Carlo VaR, Sharpe, Diversification)
```

---

## Repository Structure

```
kejafi-platform/
│
├── stage1.py               # Stage 1: Metro Risk Analysis (Streamlit app)
├── stage2.py               # Stage 2: Property Tokenization (Streamlit app)
├── stage3.py               # Stage 3: Portfolio Management (Streamlit app)
├── backend.py              # FastAPI backend with SQLite persistence
├── metro_lab_core.py       # Core OU + Jump-Diffusion modelling library
├── launch_all.py           # Launch all three stages simultaneously
├── requirements.txt        # Python dependencies
├── deploy.txt              # Deployment configuration notes
├── .gitignore
│
├── data/                   # Market data
│   ├── zori/               # Zillow Observed Rent Index (11 US metros)
│   └── population/         # US Census metropolitan population data
│
├── frontend/               # Next.js / React frontend
│   ├── pages/              # Next.js page routes
│   ├── components/         # React components
│   └── public/             # Static assets
│
└── paper/                  # Research paper
    ├── Kejafi_Paper.tex     # LaTeX source (25 pages)
    ├── Kejafi_Paper.pdf     # Compiled PDF
    ├── figures/             # Research figures (6 PNG files)
    └── references/
        └── references.bib
```

---

## Live Platform

| Component | URL |
|---|---|
| Stage 1 — Metro Risk | [kejafi-stage1.streamlit.app](https://kejafi-stage1.streamlit.app) |
| Stage 2 — Tokenization | [kejafi-stage2.streamlit.app](https://kejafi-stage2.streamlit.app) |
| Stage 3 — Portfolio | [kejafi-stage3.streamlit.app](https://kejafi-stage3.streamlit.app) |
| API (FastAPI/Swagger) | [kejafi-platform.onrender.com/docs](https://kejafi-platform.onrender.com/docs) |
| Frontend (MetaMask) | [frontend-lilac-three-92.vercel.app](https://frontend-lilac-three-92.vercel.app) |

---

## Smart Contracts — Sepolia Testnet

| Contract | Address |
|---|---|
| Network | Sepolia (Chain ID: 11155111) |
| Uniswap V3 Pool | `0x0Bf78f76c86153E433dAA5Ac6A88453D30968e27` |
| FINE5 Token (Charlotte) | `0x0FB987BEE67FD839cb1158B0712d5e4Be483dd2E` |
| FINE6 Token (Austin) | `0xe051C1eA47b246c79f3bac4e58E459cF2Aa20692` |

> All contracts are on Sepolia testnet. Mainnet deployment pending regulatory compliance review (Reg D / Reg A+).

---

## Stage 1: Metro Risk Analysis (`stage1.py`)

Rent dynamics are modelled using the **Ornstein-Uhlenbeck process** via `metro_lab_core.py`:

$$dX_t = \kappa(\theta - X_t)\,dt + \sigma\,dW_t$$

Two metro-specific adjustments:

$$\theta_{\text{adj}} = \theta + 0.5 \cdot g_{\text{pop}} \qquad \sigma_{\text{adj}} = \sigma \times (1 + (0.30 - \varepsilon))$$

Structural shocks via **jump-diffusion extension**:

$$dX_t = \kappa(\theta - X_t)\,dt + \sigma\,dW_t + J\,dN_t$$

**Results:**

| Metro | Pop. Growth | Elasticity | Volatility | Risk Score |
|---|---|---|---|---|
| Charlotte, NC | 10.2% | 0.35 | 8.5% | 50/100 |
| Austin, TX | 13.9% | 0.48 | 12.1% | 59/100 |
| San Francisco, CA | 2.8% | 0.08 | 15.2% | 35/100 |

> Population growth explains **R² = 0.73** of long-run rent variation (p < 0.01). Inelastic markets show 40–50% higher volatility.

---

## Stage 2: Property Tokenization (`stage2.py`)

Direct capitalisation valuation:

$$V = \frac{\text{NOI}_{\text{stabilised}}}{\text{Cap Rate}_{\text{metro}}} \qquad P_{\text{token}} = \frac{V \times 0.80}{100{,}000}$$

**Tokenized Properties:**

| Token | Location | Value | NOI | Cap Rate | IRR |
|---|---|---|---|---|---|
| **FINE5** | Charlotte, NC | $685,000 | $47,808 | 5.5% | **12.3%** |
| **FINE6** | Austin, TX | $1,250,000 | $78,000 | 5.2% | **14.1%** |

Each property tokenized as ERC-20 with 100,000 total supply, Uniswap V3 liquidity (0.3% fee tier), 12-month lockup, 80% collateralisation ratio.

---

## Stage 3: Portfolio Management (`stage3.py`)

Monte Carlo simulation — 10,000 scenarios with correlated return shocks:

$$\mathbf{R} = \boldsymbol{\mu} + \mathbf{L}\boldsymbol{\varepsilon}, \quad \boldsymbol{\varepsilon} \sim \mathcal{N}(\mathbf{0}, \mathbf{I})$$

**Portfolio Results:**

| Metric | Value |
|---|---|
| Total Portfolio Value | $193,486 |
| Expected Annual Return | 11.2% |
| Portfolio Volatility | 14.5% |
| Sharpe Ratio | **0.77** |
| VaR 95% (Monte Carlo) | **−12.8%** |
| Diversification Score | 50/100 |
| VaR Reduction vs. single asset | **32%** |

---

## Backend (`backend.py`)

FastAPI backend with SQLite persistence providing REST endpoints for property data, portfolio analytics, metro risk scores, and token economics.

```bash
uvicorn backend:app --reload
# Swagger UI → http://localhost:8000/docs
```

---

## Core Library (`metro_lab_core.py`)

Shared quantitative library used across all three stages:

- OU process simulation (Euler-Maruyama discretisation)
- Jump-diffusion parameter estimation (MLE)
- GPD/EVT tail estimation
- Kejafi Risk Score computation
- NOI and IRR calculation
- Monte Carlo simulation engine
- VaR and Expected Shortfall

---

## Installation & Running

### Requirements

- Python 3.11+
- Node.js 18+ (frontend only)

### Setup

```bash
git clone https://github.com/Hillkip23/kejafi-platform.git
cd kejafi-platform
pip install -r requirements.txt
```

### Launch All Three Stages at Once

```bash
python launch_all.py
```

### Launch Individually

```bash
streamlit run stage1.py --server.port 8501   # Metro Risk
streamlit run stage2.py --server.port 8502   # Tokenization
streamlit run stage3.py --server.port 8503   # Portfolio
uvicorn backend:app --reload --port 8000     # API
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

---

## Key Dependencies

```
streamlit>=1.28
numpy>=1.24
pandas>=2.0
scipy>=1.11
arch>=6.2           # GARCH estimation
matplotlib>=3.7
plotly>=5.17
web3>=6.11          # Ethereum interaction
fastapi>=0.104
uvicorn>=0.24
sqlalchemy>=2.0
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Streamlit Apps | Python 3.11, Streamlit |
| Quant Models | NumPy, SciPy, arch (GARCH), Pandas |
| Blockchain | Solidity 0.8.x, Hardhat, Web3.py |
| DEX | Uniswap V3 (concentrated liquidity) |
| Backend | FastAPI, SQLite, SQLAlchemy |
| Frontend | Next.js, React, Vercel |
| Deployment | Streamlit Cloud, Render, Vercel |

---

## Roadmap

- [x] Stage 1: OU + Jump-Diffusion metro risk model
- [x] Stage 2: NOI valuation + ERC-20 + Uniswap V3
- [x] Stage 3: Monte Carlo VaR + Sharpe + Diversification Score
- [x] FastAPI backend with SQLite persistence
- [x] Next.js MetaMask-enabled frontend
- [x] Research paper (25 pages, LaTeX)
- [ ] Chainlink oracle integration for live data feeds
- [ ] Mainnet deployment (Reg D compliance)
- [ ] ML rent prediction (LSTM / gradient boosting)
- [ ] Expand to 50+ US metros
- [ ] East African market expansion (Kenya, Tanzania, Rwanda)

---

## Research Paper

The full 25-page LaTeX research paper is in [`paper/`](paper/).

**Title:** *Kejafi: An End-to-End Platform for Tokenized Real Estate*  
**Course:** Urban Economics (MSRE/ECON/MBAD 6238), UNC Charlotte, Spring 2026  
**Instructor:** Prof. Chandler Lutz

---

## Author

**Hillary Cheruiyot**  
MS Mathematical Finance — University of North Carolina at Charlotte  
Founder, Kejafi · Founder, [Tokim Analytics](https://tokim.vercel.app)

[![Email](https://img.shields.io/badge/Email-hcheruiyot@uncc.edu-D14836?style=flat-square&logo=gmail&logoColor=white)](mailto:hcheruiyot@uncc.edu)

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">
<sub>Built at UNC Charlotte · Spring 2026 · <a href="https://kejafi-stage2.streamlit.app">Live Demo →</a></sub>
</div>
