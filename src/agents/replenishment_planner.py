"""
Replenishment Planner Agent

Generates optimized purchase orders (POs) for low-stock or high-demand SKUs.
Accounts for supplier constraints (minimum order quantities, bulk discounts, lead times).
Aggregates demand across multiple stores to optimize ordering.
"""

from typing import Dict, List, Optional
import pandas as pd
import numpy as np
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"


def generate_po(
    store_ids: List[str],
    sku_ids: Optional[List[str]] = None
) -> Dict:
    """
    Generates a consolidated purchase order for multiple stores and SKUs.

    Args:
        store_ids: List of store IDs to include in PO
        sku_ids: Optional list of specific SKU IDs to order. If None, includes all low-stock SKUs.

    Returns:
        Dict containing PO details: po_id, supplier, items, total_cost, delivery_date, etc.
        If multiple suppliers are involved, returns a dict with 'pos' key containing list of POs.
    """
    try:
        # Load SKU metadata and inventory
        with open(DATA_DIR / "sku_metadata.json", "r") as f:
            sku_metadata = json.load(f)

        # Get current inventory
        from .multi_store_inventory_monitor import monitor_inventory
        inventory = monitor_inventory(store_ids)

        if "error" in inventory:
            return {"error": inventory["error"]}

        # Determine which SKUs to include
        if sku_ids:
            target_skus = [s for s in sku_ids if s in sku_metadata]
            if not target_skus:
                return {"error": "No valid SKU IDs provided"}
        else:
            # Include all low-stock SKUs
            target_skus = list({alert["sku_id"] for alert in inventory["low_stock_alerts"]})

        if not target_skus:
            return {"error": "No SKUs require replenishment."}

        # Group SKUs by supplier
        supplier_skus = {}
        for sku_id in target_skus:
            sku_data = sku_metadata.get(sku_id, {})
            supplier = sku_data.get("supplier", "Unknown")
            if supplier not in supplier_skus:
                supplier_skus[supplier] = []
            supplier_skus[supplier].append(sku_id)

        # Generate POs per supplier
        pos = []
        for supplier, skus in supplier_skus.items():
            po_items = []
            total_cost = 0.0
            max_lead_time = 0
            total_quantity = 0
            bulk_discount_applied = 0.0

            for sku_id in skus:
                sku_data = sku_metadata[sku_id]

                # Aggregate demand across all stores for this SKU
                total_demand = 0
                for store_id in store_ids:
                    for sku in inventory["skus"]:
                        if sku["sku_id"] == sku_id:
                            store_data = sku["stock_levels"].get(store_id, {})
                            stock_level = store_data.get("stock_level", 0)
                            reorder_point = store_data.get("reorder_point", sku_data.get("reorder_point", 0))
                            if stock_level < reorder_point:
                                total_demand += reorder_point - stock_level
                            break

                if total_demand <= 0:
                    continue

                # Apply bulk discounts and minimum order quantity
                unit_cost = float(sku_data["unit_cost"])
                min_order_qty = int(sku_data.get("min_order_quantity", 1))
                bulk_discounts = sku_data.get("bulk_discounts", {})

                # Determine order quantity (round up to nearest min_order_qty)
                order_qty = max(min_order_qty, ((total_demand + min_order_qty - 1) // min_order_qty) * min_order_qty)

                # Apply bulk discount
                discount = 0.0
                for threshold_str, discount_rate in bulk_discounts.items():
                    threshold = int(threshold_str)
                    if order_qty >= threshold:
                        discount = float(discount_rate)
                # Keep track of max discount applied for this PO
                if discount > bulk_discount_applied:
                    bulk_discount_applied = discount

                discounted_cost = unit_cost * (1 - discount)
                item_total = order_qty * discounted_cost
                total_cost += item_total
                total_quantity += order_qty
                max_lead_time = max(max_lead_time, int(sku_data.get("lead_time_days", 0)))

                po_items.append({
                    "sku_id": sku_id,
                    "name": sku_data.get("name", sku_id),
                    "quantity": order_qty,
                    "unit_cost": unit_cost,
                    "discount": discount,
                    "total": round(item_total, 2)
                })

            if not po_items:
                continue

            # Delivery date: today + lead time
            delivery_date = (datetime.now() + timedelta(days=max_lead_time)).strftime("%Y-%m-%d")

            # Generate PO ID
            po_id = f"PO_{datetime.now().strftime('%Y%m%d')}_{len(pos) + 1:03d}"

            pos.append({
                "po_id": po_id,
                "store_ids": store_ids,
                "supplier": supplier,
                "items": po_items,
                "total_cost": round(total_cost, 2),
                "total_quantity": total_quantity,
                "bulk_discount_applied": round(bulk_discount_applied, 2),
                "delivery_date": delivery_date,
                "status": "generated"
            })

        # Return single PO if only one supplier, else list
        if len(pos) == 1:
            result = pos[0]
            # Add aggregated recommended order across stores for the SKU
            return result
        else:
            return {"pos": pos, "note": "Multiple suppliers require separate POs"}

    except Exception as e:
        logger.error(f"Failed to generate PO: {e}", exc_info=True)
        return {"error": str(e)}
