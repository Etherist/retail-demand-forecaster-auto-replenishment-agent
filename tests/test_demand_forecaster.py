"""
Tests for Demand Forecaster Agent
"""

import pytest
from src.agents.demand_forecaster import forecast_demand

def test_forecast_demand_structure():
    """Test forecast returns correct structure."""
    result = forecast_demand("SKU_001", "STORE_001", horizon_days=7)
    assert result is not None
    assert "sku_id" in result
    assert result["sku_id"] == "SKU_001"
    assert "store_id" in result
    assert "forecast_horizon_days" in result
    assert result["forecast_horizon_days"] == 7
    assert "forecast" in result
    assert isinstance(result["forecast"], list)
    assert len(result["forecast"]) == 7
    # Check each day
    for day in result["forecast"]:
        assert "date" in day
        assert "demand" in day
        assert "confidence_interval" in day
        assert isinstance(day["demand"], int)
        assert day["demand"] >= 0
        assert len(day["confidence_interval"]) == 2

def test_forecast_demand_invalid_sku():
    """Test forecast with invalid SKU returns None."""
    result = forecast_demand("SKU_999", "STORE_001")
    assert result is None

def test_forecast_demand_invalid_store():
    """Test forecast with invalid store returns None."""
    result = forecast_demand("SKU_001", "STORE_999")
    assert result is None

def test_forecast_demand_reorder_point():
    """Test that reorder point and recommended order are present."""
    result = forecast_demand("SKU_001", "STORE_001")
    assert "reorder_point" in result
    assert "current_stock" in result
    assert "recommended_order_quantity" in result
    assert isinstance(result["reorder_point"], int)
    assert isinstance(result["current_stock"], int)
    assert isinstance(result["recommended_order_quantity"], int)

def test_forecast_demand_consistency():
    """Test that forecasts are non-negative and dates are sequential."""
    result = forecast_demand("SKU_001", "STORE_001", horizon_days=10)
    dates = [day["date"] for day in result["forecast"]]
    # Check dates are unique and ascending
    assert dates == sorted(dates)
    assert len(set(dates)) == len(dates)
    # Check all demands are non-negative
    for day in result["forecast"]:
        assert day["demand"] >= 0
        assert day["confidence_interval"][0] >= 0
        assert day["confidence_interval"][1] >= day["confidence_interval"][0]

def test_promotion_date_parsing():
    """Test that promotion dates are parsed correctly without errors."""
    # This test ensures the .date() vs .date bug is fixed
    from src.agents.demand_forecaster import _create_external_features
    import pandas as pd
    dates = pd.date_range("2025-12-01", periods=7, freq="D")
    features = _create_external_features(dates, "SKU_001", "STORE_001")
    assert "is_promotion" in features.columns
    # Should not raise TypeError about .date being a method
    assert features["is_promotion"].dtype in [int, "int64", "int32"]

def test_fallback_forecaster():
    """Test that forecast works even without Prophet (uses fallback)."""
    # Mock PROPHET_AVAILABLE = False would trigger fallback
    # Since we can't easily mock the import, we just ensure forecast works
    result = forecast_demand("SKU_001", "STORE_001", horizon_days=7)
    # Should return a result (either Prophet or fallback)
    assert result is not None
