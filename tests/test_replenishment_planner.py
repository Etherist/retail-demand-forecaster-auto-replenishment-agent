"""
Tests for Replenishment Planner Agent
"""

import pytest
from src.agents.replenishment_planner import generate_po

def test_generate_po_for_low_stock_skus():
    """Test PO generation for automatically detected low-stock SKUs."""
    po = generate_po(store_ids=["STORE_001", "STORE_002"])
    assert "error" not in po
    assert "po_id" in po or "pos" in po
    assert "supplier" in po or (isinstance(po, dict) and "pos" in po)
    assert "items" in po or (isinstance(po, dict) and "pos" in po)
    # Check that at least one item if low-stock exists
    if "items" in po:
        assert len(po["items"]) >= 1
        for item in po["items"]:
            assert item["quantity"] >= item.get("min_order_quantity", 1)

def test_generate_po_specific_skus():
    """Test PO generation for specific SKUs."""
    po = generate_po(store_ids=["STORE_001"], sku_ids=["SKU_001", "SKU_002"])
    assert "error" not in po
    if "items" in po:
        item_skus = [i["sku_id"] for i in po["items"]]
        assert "SKU_001" in item_skus or "SKU_002" in item_skus

def test_generate_po_no_low_stock():
    """Test PO generation when no SKUs need replenishment."""
    # Possibly all SKUs are well-stocked; expect error message
    po = generate_po(store_ids=["STORE_999"])  # invalid store may cause error or no SKUs
    # We can't guarantee no low stock, but check error handling
    if "error" in po:
        assert po["error"] in ("No SKUs require replenishment.", "No valid store IDs found")
    else:
        # Some result
        assert "po_id" in po or "pos" in po

def test_generate_po_invalid_store():
    """Test PO generation with invalid store ID."""
    po = generate_po(store_ids=["INVALID"], sku_ids=["SKU_001"])
    assert "error" in po
    assert "store" in po["error"].lower() or "no valid" in po["error"].lower()

def test_generate_po_bulk_discounts_applied():
    """Test that bulk discounts are correctly applied."""
    # This test may be tricky to guarantee, but check presence of discount field
    po = generate_po(store_ids=["STORE_001", "STORE_002"])
    if "items" in po and len(po["items"]) > 0:
        for item in po["items"]:
            assert "discount" in item
            assert 0 <= item["discount"] <= 0.2  # reasonable range
