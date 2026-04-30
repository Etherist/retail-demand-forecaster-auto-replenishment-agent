"""
pytest conftest.py

Shared fixtures for all tests.
"""

import pytest
import pandas as pd
from pathlib import Path

@pytest.fixture(scope="session")
def test_data_dir():
    """Path to test_data directory."""
    return Path(__file__).parent.parent / "test_data"

@pytest.fixture(scope="session")
def project_root():
    """Project root directory."""
    return Path(__file__).parent.parent

@pytest.fixture
def sample_sales_df():
    """Returns a small sample sales DataFrame for testing."""
    data = {
        "date": pd.date_range("2025-05-01", periods=10, freq="D"),
        "sku_id": ["SKU_001"] * 10,
        "store_id": ["STORE_001"] * 10,
        "quantity_sold": [30, 35, 32, 28, 40, 45, 38, 42, 36, 34],
        "price": [2.50] * 10,
        "cost": [2.00] * 10
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_sku_metadata():
    """Returns sample SKU metadata dict."""
    return {
        "SKU_001": {
            "name": "Milk 2L Full Cream",
            "category": "Dairy",
            "supplier": "Metcash",
            "lead_time_days": 2,
            "reorder_point": 30,
            "unit_cost": 2.00,
            "selling_price": 2.50,
            "min_order_quantity": 10,
            "shelf_life_days": 14,
            "bulk_discounts": {"50": 0.05, "100": 0.10}
        }
    }
