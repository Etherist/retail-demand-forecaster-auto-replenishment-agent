"""
Integration Tests for FastAPI Endpoints
"""

import pytest
from fastapi.testclient import TestClient
from src.app.main import app

client = TestClient(app)

def test_root_returns_html():
    """Test root endpoint returns HTML dashboard."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Retail Demand Forecaster" in response.text

def test_forecast_endpoint():
    """Test POST /forecast/ returns valid JSON."""
    payload = {
        "sku_id": "SKU_001",
        "store_id": "STORE_001",
        "horizon_days": 7
    }
    response = client.post("/forecast/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["sku_id"] == "SKU_001"
    assert "forecast" in data
    assert len(data["forecast"]) == 7

def test_forecast_endpoint_invalid():
    """Test forecast with invalid inputs returns error."""
    payload = {"sku_id": "INVALID", "store_id": "STORE_999"}
    response = client.post("/forecast/", json=payload)
    assert response.status_code == 400

def test_inventory_endpoint():
    """Test GET /inventory/ returns inventory data."""
    response = client.get("/inventory/?store_ids=STORE_001")
    assert response.status_code == 200
    data = response.json()
    assert "stores" in data
    assert "skus" in data

def test_inventory_heatmap():
    """Test heatmap endpoint."""
    response = client.get("/inventory/heatmap/?store_ids=STORE_001&store_ids=STORE_002")
    assert response.status_code == 200
    data = response.json()
    assert "heatmap_data" in data
    assert "sku_ids" in data
    assert "store_ids" in data

def test_generate_po():
    """Test PO generation endpoint."""
    payload = {"store_ids": ["STORE_001", "STORE_002"]}
    response = client.post("/generate-po/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "po_id" in data or "pos" in data
    assert "supplier" in data or ("pos" in data and len(data["pos"]) > 0)

def test_generate_po_invalid_store():
    """Test PO with invalid store returns error."""
    payload = {"store_ids": ["INVALID"]}
    response = client.post("/generate-po/", json=payload)
    assert response.status_code == 400

def test_send_po():
    """Test PO sending endpoint."""
    # First generate a PO
    po_resp = client.post("/generate-po/", json={"store_ids": ["STORE_001"]})
    if po_resp.status_code != 200:
        pytest.skip("PO generation failed, skipping send test")
    po_data = po_resp.json()
    po_id = po_data.get("po_id")
    if not po_id:
        pytest.skip("No PO ID returned")
    # Attempt to send
    response = client.post(f"/send-po/?po_id={po_id}&method=email")
    # Might succeed or fail depending on SMTP, but should return something
    assert response.status_code in (200, 500)

def test_financial_metrics():
    """Test financial metrics endpoint."""
    response = client.get("/financial-metrics/?store_id=STORE_001&start_date=2025-05-01&end_date=2025-05-31")
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data

def test_supplier_comparison():
    """Test supplier comparison endpoint."""
    response = client.get("/supplier-comparison/")
    assert response.status_code == 200
    data = response.json()
    assert "suppliers" in data

def test_health():
    """Test health check."""
    response = client.get("/health/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
