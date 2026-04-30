#!/usr/bin/env python3
"""
Retail Demand Forecaster & Auto-Replenishment CLI

Command-line interface for interacting with the forecasting and replenishment system.
"""

import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from agents.demand_forecaster import forecast_demand
from agents.multi_store_inventory_monitor import monitor_inventory
from agents.replenishment_planner import generate_po
from agents.supplier_communicator import send_po, track_po_status
from agents.reporting_agent import (
    generate_inventory_report,
    generate_financial_report,
    generate_supplier_comparison_report
)

def main():
    parser = argparse.ArgumentParser(
        description="Retail Demand Forecaster & Auto-Replenishment CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    # Forecast command
    forecast_parser = subparsers.add_parser("forecast", help="Forecast demand for a SKU at a store")
    forecast_parser.add_argument("--sku-id", type=str, required=True, help="SKU ID (e.g., SKU_001)")
    forecast_parser.add_argument("--store-id", type=str, required=True, help="Store ID (e.g., STORE_001)")
    forecast_parser.add_argument("--horizon", type=int, default=7, help="Forecast horizon in days (default: 7)")

    # Inventory command
    inventory_parser = subparsers.add_parser("inventory", help="Check inventory levels for stores")
    inventory_parser.add_argument("--store-ids", nargs="+", required=True, help="List of store IDs (e.g., STORE_001 STORE_002)")

    # Generate PO command
    po_parser = subparsers.add_parser("generate-po", help="Generate a purchase order for stores")
    po_parser.add_argument("--store-ids", nargs="+", required=True, help="List of store IDs")
    po_parser.add_argument("--sku-ids", nargs="+", help="Optional list of SKU IDs to include")

    # Send PO command
    send_parser = subparsers.add_parser("send-po", help="Send a purchase order to a supplier")
    send_parser.add_argument("--po-id", type=str, required=True, help="PO ID (e.g., PO_20260501_001)")
    send_parser.add_argument("--method", type=str, default="email", choices=["email", "api"], help="Sending method")

    # Financial metrics command
    fin_parser = subparsers.add_parser("financial-metrics", help="Get financial metrics for a store")
    fin_parser.add_argument("--store-id", type=str, required=True, help="Store ID")
    fin_parser.add_argument("--start-date", type=str, required=True, help="Start date (YYYY-MM-DD)")
    fin_parser.add_argument("--end-date", type=str, required=True, help="End date (YYYY-MM-DD)")

    # Reports command
    reports_parser = subparsers.add_parser("reports", help="Generate reports")
    reports_sub = reports_parser.add_subparsers(dest="report_type", required=True)

    # Inventory report
    inv_parser = reports_sub.add_parser("inventory", help="Generate inventory report")
    inv_parser.add_argument("--store-ids", nargs="+", required=True)
    inv_parser.add_argument("--start-date", type=str, required=True)
    inv_parser.add_argument("--end-date", type=str, required=True)

    # Financial report
    finrep_parser = reports_sub.add_parser("financial", help="Generate financial report")
    finrep_parser.add_argument("--store-id", type=str, required=True)
    finrep_parser.add_argument("--start-date", type=str, required=True)
    finrep_parser.add_argument("--end-date", type=str, required=True)

    # Supplier comparison report
    sup_parser = reports_sub.add_parser("supplier-comparison", help="Generate supplier comparison report")

    args = parser.parse_args()

    # Execute command
    try:
        if args.command == "forecast":
            result = forecast_demand(args.sku_id, args.store_id, args.horizon)
            if result:
                print(f"\nDemand Forecast for {args.sku_id} (Store: {args.store_id})")
                print(f"Horizon: {args.horizon} days")
                print(f"Current Stock: {result['current_stock']}")
                print(f"Reorder Point: {result['reorder_point']}")
                print(f"Recommended Order: {result['recommended_order_quantity']}\n")
                print("Date       | Demand | Confidence Interval")
                print("-" * 50)
                for day in result["forecast"]:
                    print(f"{day['date']} | {day['demand']:>6} | [{day['confidence_interval'][0]}, {day['confidence_interval'][1]}]")
            else:
                print("Failed to generate forecast.")
                sys.exit(1)

        elif args.command == "inventory":
            result = monitor_inventory(args.store_ids)
            if "error" not in result:
                print(f"\nInventory for Stores: {', '.join(result['stores'])}")
                print(f"Total SKUs: {len(result['skus'])}\n")
                for sku in result["skus"]:
                    print(f"SKU: {sku['sku_id']} ({sku['name']}) [{sku['category']}]")
                    for store_id, stock_data in sku["stock_levels"].items():
                        print(f"  {store_id}: {stock_data['stock_level']} units (Reorder: {stock_data['reorder_point']})")
                if result["low_stock_alerts"]:
                    print("\n⚠️  Low-Stock Alerts:")
                    for alert in result["low_stock_alerts"]:
                        print(f"  {alert['store_id']} - {alert['sku_id']} ({alert['name']}): {alert['current_stock']} (Need: {alert['recommended_order']})")
            else:
                print(f"Error: {result['error']}")
                sys.exit(1)

        elif args.command == "generate-po":
            result = generate_po(args.store_ids, args.sku_ids)
            if "error" not in result:
                print(f"\n✅ Purchase Order Generated")
                print(f"PO ID: {result.get('po_id', 'N/A')}")
                print(f"Stores: {', '.join(result['store_ids'])}")
                print(f"Supplier: {result['supplier']}")
                print(f"Delivery Date: {result['delivery_date']}")
                print(f"Total Cost: ${result['total_cost']:.2f}")
                if result.get("bulk_discount_applied", 0) > 0:
                    print(f"Bulk Discount: {result['bulk_discount_applied']*100:.0f}%")
                print("\nItems:")
                for item in result["items"]:
                    print(f"  - {item['name']} ({item['sku_id']}): {item['quantity']} x ${item['unit_cost']:.2f} = ${item['total']:.2f}")
            else:
                print(f"Error: {result['error']}")
                sys.exit(1)

        elif args.command == "send-po":
            success = send_po({"po_id": args.po_id}, method=args.method)
            if success:
                print(f"PO {args.po_id} sent successfully via {args.method}.")
            else:
                print(f"Failed to send PO {args.po_id}.")
                sys.exit(1)

        elif args.command == "financial-metrics":
            result = generate_financial_report(args.store_id, args.start_date, args.end_date)
            if "error" not in result:
                m = result["metrics"]["metrics"]
                print(f"\nFinancial Metrics for {args.store_id}")
                print(f"Period: {args.start_date} to {args.end_date}")
                print(f"Total Sales (AUD): ${m['total_sales_AUD']:,.2f}")
                print(f"Total Cost (AUD): ${m['total_cost_AUD']:,.2f}")
                print(f"Gross Margin (AUD): ${m['gross_margin_AUD']:,.2f} ({m['gross_margin_percent']:.1f}%)")
                print(f"Inventory Turnover: {m['inventory_turnover']:.2f}")
                print(f"Stockout Incidents: {m['stockout_incidents']}")
                print(f"Overstock Incidents: {m['overstock_incidents']}")
                print(f"Emergency Orders Cost: ${m['emergency_orders_cost_AUD']:,.2f}")
                print("\nTop SKUs by Gross Margin:")
                for sku in result["metrics"]["top_skus_by_margin"]:
                    print(f"  {sku['sku_id']}: ${sku['gross_margin_AUD']:,.2f} ({sku['margin_percent']:.1f}%) - {sku['quantity_sold']} sold")
            else:
                print(f"Error: {result['error']}")
                sys.exit(1)

        elif args.command == "reports":
            if args.report_type == "inventory":
                result = generate_inventory_report(args.store_ids, args.start_date, args.end_date)
                if "error" not in result:
                    print(f"Inventory report generated:")
                    print(f"  PDF: {result['pdf_report']}")
                    print(f"  Markdown: {result['markdown_report']}")
                else:
                    print(f"Error: {result['error']}")
                    sys.exit(1)
            elif args.report_type == "financial":
                result = generate_financial_report(args.store_id, args.start_date, args.end_date)
                if "error" not in result:
                    print(f"Financial report generated:")
                    print(f"  PDF: {result['pdf_report']}")
                    print(f"  Markdown: {result['markdown_report']}")
                else:
                    print(f"Error: {result['error']}")
                    sys.exit(1)
            elif args.report_type == "supplier-comparison":
                result = generate_supplier_comparison_report()
                if "error" not in result:
                    print(f"Supplier comparison report generated:")
                    print(f"  PDF: {result['pdf_report']}")
                    print(f"  Markdown: {result['markdown_report']}")
                else:
                    print(f"Error: {result['error']}")
                    sys.exit(1)

    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
