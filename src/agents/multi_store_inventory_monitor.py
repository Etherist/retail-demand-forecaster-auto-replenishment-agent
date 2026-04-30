"""
Multi-Store Inventory Monitor Agent

Tracks current stock levels and reorder points for each SKU across all stores.
Identifies low-stock alerts and provides inventory visibility.
"""

from typing import Dict, List, Optional
import pandas as pd
import numpy as np
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"


def monitor_inventory(store_ids: Optional[List[str]] = None) -> Dict:
    """
    Monitors inventory levels for specified stores and identifies low-stock SKUs.

    Args:
        store_ids: Optional list of store IDs to monitor. If None, monitors all stores.

    Returns:
        Dict containing:
        - stores: list of store IDs monitored
        - skus: list of SKU data with stock levels per store
        - low_stock_alerts: list of alerts for SKUs below reorder point
    """
    try:
        # Load metadata
        with open(DATA_DIR / "sku_metadata.json", "r") as f:
            sku_metadata = json.load(f)

        # Mock current inventory levels
        # In production, this would query inventory database/ERP
        inventory = _get_mock_inventory()

        # Determine which stores to include
        all_store_ids = list(inventory.keys())
        if store_ids:
            selected_stores = {sid: inventory[sid] for sid in store_ids if sid in inventory}
            if not selected_stores:
                raise ValueError("No valid store IDs found")
        else:
            selected_stores = inventory

        # Prepare output structure
        output = {
            "stores": list(selected_stores.keys()),
            "skus": [],
            "low_stock_alerts": []
        }

        # Aggregate SKU data across stores
        sku_data = {}
        for store_id, store_inventory in selected_stores.items():
            for sku_id, stock_level in store_inventory.items():
                if sku_id not in sku_data:
                    sku_data[sku_id] = {
                        "sku_id": sku_id,
                        "name": sku_metadata.get(sku_id, {}).get("name", sku_id),
                        "category": sku_metadata.get(sku_id, {}).get("category", "Unknown"),
                        "stores": {}
                    }
                sku_data[sku_id]["stores"][store_id] = {
                    "stock_level": stock_level,
                    "reorder_point": sku_metadata.get(sku_id, {}).get("reorder_point", 0)
                }

        # Format SKU list
        for sku_id, data in sku_data.items():
            sku_entry = {
                "sku_id": sku_id,
                "name": data["name"],
                "category": data["category"],
                "stock_levels": data["stores"]
            }
            output["skus"].append(sku_entry)

            # Check low stock for each store
            for store_id, store_data in data["stores"].items():
                if store_data["stock_level"] < store_data["reorder_point"]:
                    output["low_stock_alerts"].append({
                        "store_id": store_id,
                        "sku_id": sku_id,
                        "name": data["name"],
                        "current_stock": store_data["stock_level"],
                        "reorder_point": store_data["reorder_point"],
                        "recommended_order": max(
                            sku_metadata.get(sku_id, {}).get("min_order_quantity", 1),
                            store_data["reorder_point"] - store_data["stock_level"]
                        )
                    })

        # Sort low stock alerts by severity (gap)
        output["low_stock_alerts"].sort(key=lambda x: x["reorder_point"] - x["current_stock"], reverse=True)

        logger.info(f"Monitored inventory for {len(output['stores'])} stores, {len(output['skus'])} SKUs, {len(output['low_stock_alerts'])} low-stock alerts")
        return output

    except Exception as e:
        logger.error(f"Failed to monitor inventory: {e}", exc_info=True)
        return {"error": str(e)}


def _get_mock_inventory() -> Dict:
    """
    Generates mock current inventory levels for demo purposes.
    In production, this would read from inventory database.
    """
    # Load sales data to estimate current stock based on last 30 days of sales
    # For demo, we'll generate somewhat realistic levels
    sales_path = DATA_DIR / "sample_sales.csv"
    if not sales_path.exists():
        # Fallback to hardcoded mock
        return _get_hardcoded_inventory()

    sales_df = pd.read_csv(sales_path)
    sales_df["date"] = pd.to_datetime(sales_df["date"])

    # Get most recent date
    last_date = sales_df["date"].max()

    # Calculate stock as: initial 200 - sales in last 30 days + random receipts
    inventory = {}
    stores = sorted(sales_df["store_id"].unique())
    skus = sorted(sales_df["sku_id"].unique())

    for store in stores:
        inventory[store] = {}
        for sku in skus:
            # Estimate average daily demand
            sku_store_sales = sales_df[(sales_df["store_id"] == store) & (sales_df["sku_id"] == sku)]
            recent_sales = sku_store_sales[sku_store_sales["date"] >= last_date - pd.Timedelta(days=30)]
            total_recent = recent_sales["quantity_sold"].sum()

            # Start with some base stock, subtract recent sales, add random restock
            base = 200
            sold = int(total_recent)
            restock = np.random.randint(50, 150) if sold > 150 else 0
            stock = max(0, base - sold + restock)

            inventory[store][sku] = stock

    return inventory


def _get_hardcoded_inventory() -> Dict:
    """Fallback hardcoded inventory for quick demo."""
    return {
        "STORE_001": {
            "SKU_001": 25,
            "SKU_002": 15,
            "SKU_003": 10,
            # Add more SKUs with defaults
        },
        "STORE_002": {
            "SKU_001": 40,
            "SKU_002": 30,
            "SKU_003": 5,
        },
        "STORE_003": {
            "SKU_001": 10,
            "SKU_002": 5,
            "SKU_003": 20,
        }
    }
