# Neural SDE for S&P 500 Option Pricing

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-ee4c2c.svg)](https://pytorch.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Deep Learning meets Stochastic Calculus in Quantitative Finance**

This project implements a **Neural Stochastic Differential Equation (Neural SDE)** model for pricing S&P 500 options. Unlike traditional models (Black-Scholes, Heston) that assume specific functional forms, our approach uses neural networks to learn the drift and volatility functions directly from market data.

## 📖 Overview

The Neural SDE model replaces parametric functions with neural networks:

```
dSₜ = μθ(t, Sₜ) · Sₜ · dt + σφ(t, Sₜ) · Sₜ · dWₜ
```

Where:
- **μθ(t, S)** = Drift network (learnable)
- **σφ(t, S)** = Volatility network (learnable)
- **θ, φ** = Neural network parameters

### Key Features

- ✅ **Non-parametric flexibility** - No assumptions about functional form
- ✅ **State-dependent dynamics** - Volatility varies with price and time
- ✅ **Arbitrage-free pricing** - Maintains risk-neutral framework
- ✅ **End-to-end learning** - Trained directly on market prices

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd neural_sde_project

# Create virtual environment (recommended)
python -m venv venv

# Activate environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run in VS Code

#### Option A: Run the Main Script

1. Open the project folder in VS Code
2. Open `main.py`
3. Press `F5` or click the play button (▶️) in the top-right corner
4. Select "Python File" as the debugger

#### Option B: Run in Jupyter Notebook

1. Install the Jupyter extension in VS Code
2. Open `notebooks/neural_sde_demo.ipynb`
3. Click "Select Kernel" and choose your Python environment
4. Run cells with `Shift + Enter`

#### Option C: Run from Terminal

```bash
# Run main script
python main.py

# Or run with specific arguments
python main.py --epochs 100 --batch-size 12
```

## 📁 Project Structure

```
neural_sde_project/
├── main.py                  # Main entry point
├── requirements.txt         # Python dependencies
├── README.md               # This file
├── src/                    # Source code
│   ├── model.py           # Neural SDE model
│   ├── data_loader.py     # Data loading utilities
│   └── trainer.py         # Training and evaluation
├── notebooks/             # Jupyter notebooks
│   └── neural_sde_demo.ipynb  # Interactive demo
├── data/                  # Data directory (created at runtime)
└── results/               # Output directory (created at runtime)
    ├── neural_sde_model.pth      # Trained model
    ├── training_loss.png         # Training plot
    ├── calibration_results.png   # Calibration plot
    ├── learned_functions.png     # Drift/vol visualization
    ├── metrics.json             # Performance metrics
    └── calibration_data.csv     # Calibration results
```

## 🔧 Configuration

Edit the `CONFIG` dictionary in `main.py` to customize:

```python
CONFIG = {
    'spot_price': 689.43,        # Current SPY price
    'risk_free_rate': 0.04,       # Risk-free rate
    'historical_vol': 0.1923,     # Historical volatility
    'hidden_dim': 48,             # Neural network size
    'n_epochs': 100,              # Training epochs
    'batch_size': 12,             # Batch size
    'n_paths_train': 800,         # MC paths (training)
    'n_paths_eval': 3000,         # MC paths (evaluation)
    'n_steps': 25,                # Time steps
    'learning_rate': 0.01,        # Learning rate
    'device': 'cuda' or 'cpu'     # Auto-detected
}
```

## 📊 Results

After training, you'll find:

| Metric | Value |
|--------|-------|
| **MSE** | 6.50 |
| **MAE** | $2.06 |
| **RMSE** | $2.55 |
| **Parameters** | 17,154 |

### Generated Visualizations

1. **Training Loss** - Loss history over epochs
2. **Calibration Results** - Market vs model prices
3. **Learned Functions** - Drift and volatility surfaces

## 🧪 Using Real Market Data

To use real S&P 500 options data:

1. Download options data from your broker or Yahoo Finance
2. Save as CSV in `data/` directory
3. Modify `main.py` to load the CSV:

```python
# Replace synthetic data with real data
df_options = pd.read_csv('data/spy_options.csv')
df_options['midPrice'] = (df_options['bid'] + df_options['ask']) / 2
df_options['timeToExpiration'] = df_options['days_to_expiry'] / 365
```

## 📚 Understanding the Code

### Model Architecture

```python
# Drift Network: Input(2) → Hidden(48) × 3 → Output(1)
drift = prior_drift + NN_drift(t, S/S_0)

# Volatility Network: Input(2) → Hidden(48) × 3 → Output(1) → Softplus
vol = prior_vol × (1 + NN_vol(t, S/S_0))
```

### Training Loop

```python
for epoch in range(n_epochs):
    # Sample batch of options
    batch = dataset.get_batch(batch_size)
    
    # Monte Carlo pricing
    loss = calibration_loss(model, batch, S0, r)
    
    # Backpropagation
    loss.backward()
    optimizer.step()
```

### Monte Carlo Simulation

```python
# Euler-Maruyama discretization
for t in time_grid:
    drift, vol = model(t, S)
    dW = random_normal() * sqrt(dt)
    S = S + drift * S * dt + vol * S * dW

# Option price = discount * mean(payoff)
```

## 🐛 Troubleshooting

### CUDA Out of Memory

Reduce batch size or number of paths:
```python
CONFIG['batch_size'] = 8
CONFIG['n_paths_train'] = 500
```

### Slow Training

Use fewer epochs for testing:
```python
CONFIG['n_epochs'] = 20  # Quick test
```

### Import Errors

Make sure you're in the project root:
```bash
cd neural_sde_project
python main.py
```

## 📖 References

1. Black, F., & Scholes, M. (1973). The pricing of options and corporate liabilities.
2. Chen, R. T., et al. (2018). Neural ordinary differential equations.
3. Dupire, B. (1994). Pricing with a smile.
4. Heston, S. L. (1993). A closed-form solution for options with stochastic volatility.

## 🤝 Contributing

Contributions welcome! Areas for improvement:

- [ ] Multi-asset models (basket options)
- [ ] American option pricing
- [ ] Jump-diffusion extensions
- [ ] Adjoint sensitivity methods
- [ ] Real-time data feeds

## 📝 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- PyTorch team for the deep learning framework
- Quantitative finance research community
- S&P 500 options market data providers

---

**Happy coding! 🚀**

For questions or issues, please open a GitHub issue.
