"""
FastAPI Main Application

Serves the HTML dashboard and provides API endpoints for:
- Demand forecasting
- Inventory monitoring
- Purchase order generation
- Supplier communication
- Reporting and analytics
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from pathlib import Path
import uuid
import json
import logging

# Import agents
from src.agents.sales_data_ingestor import ingest_sales_data
from src.agents.demand_forecaster import forecast_demand
from src.agents.multi_store_inventory_monitor import monitor_inventory
from src.agents.replenishment_planner import generate_po
from src.agents.supplier_communicator import send_po
from src.agents.reporting_agent import (
    generate_inventory_report,
    generate_financial_report,
    generate_supplier_comparison_report
)

logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "src" / "data"
STATIC_DIR = PROJECT_ROOT / "src" / "app" / "static"
REPORTS_DIR = PROJECT_ROOT / "reports"
POS_DIR = REPORTS_DIR / "pos"
POS_DIR.mkdir(parents=True, exist_ok=True)

# Initialize FastAPI app
app = FastAPI(
    title="Retail Demand Forecaster & Auto-Replenishment API",
    description="AI-powered inventory management for Australian retailers",
    version="1.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Load sales data at startup (cached in memory)
SALES_DATA = None


def _get_sales_data():
    global SALES_DATA
    if SALES_DATA is None:
        sales_path = DATA_DIR / "sample_sales.csv"
        if sales_path.exists():
            SALES_DATA = ingest_sales_data(str(sales_path))
        else:
            logger.error("Sales data file not found at startup")
    return SALES_DATA


# Pydantic models
class ForecastRequest(BaseModel):
    sku_id: str = Field(..., description="SKU identifier (e.g., SKU_001)")
    store_id: str = Field(..., description="Store identifier (e.g., STORE_001)")
    horizon_days: int = Field(7, ge=1, le=30, description="Forecast horizon in days")


class PORequest(BaseModel):
    store_ids: List[str] = Field(..., min_length=1, description="List of store IDs")
    sku_ids: Optional[List[str]] = Field(None, description="Optional list of SKU IDs to include")


class SendPORequest(BaseModel):
    po_id: str = Field(..., description="Purchase order ID")
    method: str = Field("email", description="Sending method: email or api")


class FinancialMetricsRequest(BaseModel):
    store_id: str = Field(..., description="Store identifier")
    start_date: str = Field(..., description="Start date YYYY-MM-DD")
    end_date: str = Field(..., description="End date YYYY-MM-DD")


# API endpoints
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the HTML dashboard."""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    raise HTTPException(status_code=404, detail="Dashboard not found")


@app.post("/forecast/")
async def get_forecast(request: ForecastRequest):
    """
    Forecast demand for a specific SKU at a store.

    Returns daily demand predictions with confidence intervals,
    reorder point, current stock, and recommended order quantity.
    """
    try:
        forecast = forecast_demand(
            sku_id=request.sku_id,
            store_id=request.store_id,
            horizon_days=request.horizon_days
        )
    except Exception as e:
        logger.error(f"Forecast computation error: {e}")
        raise HTTPException(status_code=500, detail="Internal forecasting error.")
    if forecast is None:
        raise HTTPException(status_code=400, detail="Failed to generate forecast. Check SKU/store IDs.")
    return forecast


@app.get("/inventory/")
async def get_inventory(store_ids: List[str] = Query([])):
    """
    Get current inventory levels for specified stores.

    If no store_ids provided, returns data for all stores.
    """
    try:
        store_list = store_ids if store_ids else None
        inventory = monitor_inventory(store_list)
    except Exception as e:
        logger.error(f"Inventory endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Internal inventory error.")
    if "error" in inventory:
        raise HTTPException(status_code=400, detail=inventory["error"])
    return inventory


@app.get("/inventory/heatmap/")
async def get_inventory_heatmap(store_ids: List[str] = Query([])):
    """Get inventory heatmap data for all SKUs across specified stores."""
    try:
        store_list = store_ids if store_ids else None
        inventory = monitor_inventory(store_list)
    except Exception as e:
        logger.error(f"Heatmap endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Internal inventory error.")
    if "error" in inventory:
        raise HTTPException(status_code=400, detail=inventory["error"])

    sku_ids = [sku["sku_id"] for sku in inventory["skus"]]
    heatmap_data = []
    for sku in inventory["skus"]:
        row = {"sku": sku["sku_id"]}
        for store_id in store_list or inventory["stores"]:
            row[store_id] = sku["stock_levels"].get(store_id, {}).get("stock_level", 0)
        heatmap_data.append(row)

    return {
        "heatmap_data": heatmap_data,
        "sku_ids": sku_ids,
        "store_ids": inventory["stores"]
    }


@app.post("/generate-po/")
async def create_po(request: PORequest):
    """
    Generate a purchase order for the specified stores and SKUs.

    If sku_ids is omitted, automatically includes low-stock SKUs.
    Returns optimized PO with bulk discounts applied.
    """
    try:
        po = generate_po(request.store_ids, request.sku_ids)
    except Exception as e:
        logger.error(f"Generate PO endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Internal PO generation error.")
    if "error" in po:
        raise HTTPException(status_code=400, detail=po["error"])
    # Save PO to file for tracking
    po_id = po.get("po_id", str(uuid.uuid4()))
    po_file = POS_DIR / f"{po_id}.json"
    with open(po_file, "w") as f:
        json.dump(po, f, indent=2)
    return po


@app.post("/generate-multi-store-po/")
async def create_multi_store_po(request: PORequest):
    """Generate a consolidated PO for multiple stores."""
    return await create_po(request)  # same as single


@app.post("/send-po/")
async def send_purchase_order(po_id: str, method: str = "email"):
    """
    Send a generated PO to the supplier.

    Args:
        po_id: Purchase order ID (must exist in system)
        method: "email" or "api"
    """
    try:
        po_file = POS_DIR / f"{po_id}.json"
        if not po_file.exists():
            raise HTTPException(status_code=404, detail=f"PO {po_id} not found")

        with open(po_file, "r") as f:
            po = json.load(f)

        success = send_po(po, method=method)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to send PO")

        return {"status": "sent", "po_id": po_id, "method": method}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Send PO endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/financial-metrics/")
async def get_financial_metrics(
    store_id: str,
    start_date: str,
    end_date: str
):
    """
    Get financial metrics for a store over a date range.

    Includes gross margin, inventory turnover, stockout/overstock incidents.
    """
    try:
        report = generate_financial_report(store_id, start_date, end_date)
    except Exception as e:
        logger.error(f"Financial metrics endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Internal financial reporting error.")
    if "error" in report:
        raise HTTPException(status_code=400, detail=report["error"])
    return report["metrics"]


@app.get("/supplier-comparison/")
async def get_supplier_comparison():
    """Get supplier comparison data with lead times, costs, and reliability."""
    try:
        report = generate_supplier_comparison_report()
    except Exception as e:
        logger.error(f"Supplier comparison endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Internal supplier reporting error.")
    if "error" in report:
        raise HTTPException(status_code=400, detail=report["error"])
    return report


@app.get("/reports/inventory/")
async def get_inventory_report(
    store_ids: List[str] = Query(...),
    start_date: str = ...,
    end_date: str = ...
):
    """Generate an inventory report (PDF + Markdown + heatmap HTML)."""
    try:
        report = generate_inventory_report(store_ids, start_date, end_date)
    except Exception as e:
        logger.error(f"Inventory report endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Internal inventory reporting error.")
    if "error" in report:
        raise HTTPException(status_code=400, detail=report["error"])
    return report


@app.get("/reports/financial/")
async def get_financial_report(
    store_id: str,
    start_date: str,
    end_date: str
):
    """Generate a financial report (PDF + Markdown)."""
    try:
        report = generate_financial_report(store_id, start_date, end_date)
    except Exception as e:
        logger.error(f"Financial report endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Internal financial reporting error.")
    if "error" in report:
        raise HTTPException(status_code=400, detail=report["error"])
    return report


@app.get("/reports/supplier-comparison/")
async def get_supplier_report():
    """Generate a supplier comparison report (PDF + Markdown)."""
    try:
        report = generate_supplier_comparison_report()
        if "error" in report:
            raise HTTPException(status_code=400, detail=report["error"])
        return report
    except Exception as e:
        logger.error(f"Supplier report endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health/")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
