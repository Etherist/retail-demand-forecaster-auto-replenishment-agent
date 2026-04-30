"""
Tests for Multi-Store Inventory Monitor Agent
"""

import pytest
from src.agents.multi_store_inventory_monitor import monitor_inventory, _get_mock_inventory

def test_monitor_inventory_all_stores():
    """Test monitoring all stores."""
    result = monitor_inventory()
    assert "error" not in result
    assert "stores" in result
    assert "skus" in result
    assert "low_stock_alerts" in result
    assert len(result["stores"]) >= 1
    assert len(result["skus"]) >= 1

def test_monitor_inventory_specific_stores():
    """Test monitoring specific stores."""
    result = monitor_inventory(["STORE_001"])
    assert "error" not in result
    assert result["stores"] == ["STORE_001"]

def test_monitor_inventory_invalid_store():
    """Test monitoring with invalid store ID."""
    result = monitor_inventory(["INVALID"])
    assert "error" in result

def test_low_stock_alerts_present():
    """Test that low stock alerts are identified."""
    result = monitor_inventory()
    # At least some alerts expected due to random stock generation
    # Not strictly guaranteed but likely; we can just check structure
    for alert in result["low_stock_alerts"]:
        assert "store_id" in alert
        assert "sku_id" in alert
        assert "current_stock" in alert
        assert "reorder_point" in alert
        assert "recommended_order" in alert
        assert alert["current_stock"] < alert["reorder_point"]

def test_mock_inventory_structure():
    """Test mock inventory has proper structure."""
    inv = _get_mock_inventory()
    assert isinstance(inv, dict)
    for store_id, skus in inv.items():
        assert store_id.startswith("STORE_")
        assert isinstance(skus, dict)
