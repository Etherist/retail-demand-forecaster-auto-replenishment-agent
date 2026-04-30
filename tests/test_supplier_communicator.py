"""
Tests for Supplier Communicator Agent
"""

import pytest
import os
from src.agents.supplier_communicator import send_po_email, send_po_api, send_po, track_po_status

def test_send_po_email_mock(monkeypatch):
    """Test email sending with missing SMTP config returns mock success."""
    po = {
        "po_id": "PO_20260501_001",
        "supplier": "Metcash",
        "store_ids": ["STORE_001"],
        "items": [{"name": "Milk", "quantity": 100, "unit_cost": 2.5}],
        "total_cost": 250.0,
        "delivery_date": "2026-05-03"
    }
    # Ensure SMTP env vars not set
    monkeypatch.delenv("SMTP_SERVER", raising=False)
    monkeypatch.delenv("SMTP_USERNAME", raising=False)
    monkeypatch.delenv("SMTP_PASSWORD", raising=False)
    result = send_po_email(po)
    assert result is True  # Mock success

def test_send_po_api_mock(monkeypatch):
    """Test API sending without requests library."""
    po = {
        "po_id": "PO_20260501_002",
        "supplier": "PFD Food Services",
        "store_ids": ["STORE_002"],
        "items": [],
        "total_cost": 100.0,
        "delivery_date": "2026-05-02"
    }
    # Mock requests.post to avoid actual call
    class MockResp:
        status_code = 200
        def raise_for_status(self): pass
    def mock_post(url, json, headers, timeout):
        return MockResp()
    monkeypatch.setattr("requests.post", mock_post)
    result = send_po_api(po)
    assert result is True

def test_send_po_invalid_method():
    """Test sending with unsupported method."""
    po = {"po_id": "PO_001", "supplier": "Test"}
    result = send_po(po, method="carrier_pigeon")
    assert result is False

def test_track_po_status():
    """Test PO status tracking (mock)."""
    status = track_po_status("PO_123")
    assert status["po_id"] == "PO_123"
    assert "status" in status
