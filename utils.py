# utils.py - Shared utilities for all Kejafi stages

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import json
from pathlib import Path
import hashlib

# =========================================================
# UI Helpers
# =========================================================

def apply_custom_styling():
    """Apply custom CSS styling to all pages"""
    st.markdown("""
    <style>
    /* Better card styling */
    .stMetric {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Progress bar styling */
    .stProgress > div > div {
        background-color: #667eea;
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
        border-left: 4px solid #2ecc71;
    }
    
    /* Info box styling */
    .stInfo {
        border-radius: 10px;
        background-color: #e8f4fd;
    }
    
    /* Custom tooltip */
    .tooltip {
        position: relative;
        display: inline-block;
        cursor: help;
        border-bottom: 1px dotted #999;
    }
    </style>
    """, unsafe_allow_html=True)


def show_loading(message="Loading..."):
    """Show a loading spinner with message"""
    return st.spinner(message)


def show_success(message, duration=3):
    """Show success message and auto-clear"""
    success = st.success(message)
    return success


def format_currency(value):
    """Format number as currency"""
    return f"${value:,.0f}"


def format_percentage(value):
    """Format number as percentage"""
    return f"{value*100:.1f}%"


def format_metric(label, value, help_text=None):
    """Display a formatted metric with tooltip"""
    return st.metric(label, value, help=help_text)


# =========================================================
# Data Export Helpers
# =========================================================

def export_to_csv(df, filename):
    """Export DataFrame to CSV with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    full_filename = f"{filename}_{timestamp}.csv"
    df.to_csv(full_filename, index=False)
    return full_filename


def export_to_json(data, filename):
    """Export data to JSON with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    full_filename = f"{filename}_{timestamp}.json"
    with open(full_filename, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    return full_filename


# =========================================================
# Validation Helpers
# =========================================================

def validate_input(value, min_val=None, max_val=None, name="Value"):
    """Validate user input with bounds checking"""
    if value is None:
        st.error(f"{name} cannot be empty")
        return False
    
    if min_val is not None and value < min_val:
        st.error(f"{name} must be at least {min_val}")
        return False
    
    if max_val is not None and value > max_val:
        st.error(f"{name} must be at most {max_val}")
        return False
    
    return True


def safe_divide(numerator, denominator, default=0):
    """Safe division with fallback"""
    try:
        return numerator / denominator if denominator != 0 else default
    except:
        return default


# =========================================================
# Performance Helpers
# =========================================================

def timing_decorator(func):
    """Decorator to measure function execution time"""
    import time
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        st.caption(f"⏱️ {func.__name__} took {end-start:.2f} seconds")
        return result
    return wrapper


# =========================================================
# Cache Helpers
# =========================================================

def get_cache_key(*args, **kwargs):
    """Generate cache key from arguments"""
    key_string = str(args) + str(sorted(kwargs.items()))
    return hashlib.md5(key_string.encode()).hexdigest()


# =========================================================
# Error Handling
# =========================================================

def handle_error(error, fallback_value=None):
    """Graceful error handling"""
    st.error(f"Error: {str(error)}")
    return fallback_value