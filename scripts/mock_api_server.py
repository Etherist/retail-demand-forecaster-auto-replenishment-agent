"""
Mock Supplier API Server

Simulates Metcash and PFD Food Services APIs for the demo.
Run this server separately on port 8001.
"""

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import List, Optional
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

app = FastAPI(title="Mock Supplier APIs", version="1.0.0")

# Mock supplier data
SUPPLIERS = {
    "Metcash": {
        "api_key": "mock_metcash_key",
        "products": ["SKU_001", "SKU_003", "SKU_004", "SKU_007", "SKU_010"],
        "avg_lead_time": 2.5,
        "reliability": 0.95
    },
    "PFD Food Services": {
        "api_key": "mock_pfd_key",
        "products": ["SKU_002", "SKU_005", "SKU_008", "SKU_011"],
        "avg_lead_time": 1.2,
        "reliability": 0.90
    }
}

class OrderRequest(BaseModel):
    po_id: str
    store_ids: List[str]
    supplier: str
    items: List[dict]
    total_cost: float
    delivery_date: str

@app.get("/suppliers/")
async def get_suppliers():
    return {"suppliers": list(SUPPLIERS.keys())}

@app.get("/{supplier}/products/")
async def get_products(supplier: str, api_key: str = Header(...)):
    if supplier not in SUPPLIERS:
        raise HTTPException(status_code=404, detail="Supplier not found")
    if api_key != SUPPLIERS[supplier]["api_key"]:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return {"supplier": supplier, "products": SUPPLIERS[supplier]["products"]}

@app.post("/{supplier}/order/")
async def place_order(supplier: str, request: OrderRequest, api_key: str = Header(...)):
    if supplier not in SUPPLIERS:
        raise HTTPException(status_code=404, detail="Supplier not found")
    if api_key != SUPPLIERS[supplier]["api_key"]:
        raise HTTPException(status_code=401, detail="Invalid API key")
    if request.supplier != supplier:
        raise HTTPException(status_code=400, detail="Supplier mismatch")

    # Mock order processing
    logger.info(f"Received order {request.po_id} for {supplier}")
    return {
        "status": "received",
        "po_id": request.po_id,
        "supplier": supplier,
        "estimated_delivery": request.delivery_date,
        "tracking_number": f"TRK-{request.po_id[-6:]}"
    }

@app.get("/health/")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
