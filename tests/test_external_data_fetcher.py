"""
Tests for External Data Fetcher Agent
"""

import pytest
import pandas as pd
from src.agents.external_data_fetcher import (
    fetch_weather_data,
    fetch_holidays,
    fetch_promotions,
    get_store_coordinates
)

def test_fetch_weather_data():
    """Test weather data generation returns proper structure."""
    result = fetch_weather_data(
        lat=-33.8688,
        lng=151.2093,
        start_date="2025-06-01",
        end_date="2025-06-07"
    )
    assert result is not None
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 7
    assert {"date", "temperature", "rainfall", "location"}.issubset(result.columns)
    assert result["temperature"].between(0, 50).all()  # plausible range

def test_fetch_holidays():
    """Test holiday fetching for date range."""
    holidays = fetch_holidays("2025-12-20", "2025-12-31")
    assert isinstance(holidays, list)
    # Should include Christmas
    names = [h["name"] for h in holidays]
    assert "Christmas Day" in names

def test_fetch_promotions_no_filter():
    """Test fetching all promotions."""
    promos = fetch_promotions()
    assert isinstance(promos, list)
    # Should have entries for 2025 and 2026
    assert len(promos) > 0

def test_fetch_promotions_by_sku():
    """Test filtering promotions by SKU."""
    promos = fetch_promotions(sku_id="SKU_001")
    assert all(p["sku_id"] == "SKU_001" for p in promos)

def test_fetch_promotions_by_date_range():
    """Test filtering promotions by date range."""
    promos = fetch_promotions(start_date="2025-11-01", end_date="2025-12-31")
    assert all(p["start_date"] >= "2025-11-01" or p["end_date"] <= "2025-12-31" for p in promos)
    # Black Friday should be included
    assert any("Black Friday" in p["name"] for p in promos)

def test_get_store_coordinates():
    """Test store coordinate lookup."""
    lat, lng = get_store_coordinates("STORE_001")
    assert abs(lat - (-33.8688)) < 0.01
    assert abs(lng - 151.2093) < 0.01

    lat, lng = get_store_coordinates("UNKNOWN")
    assert lat == 0.0 and lng == 0.0
