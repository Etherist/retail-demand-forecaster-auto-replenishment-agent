"""
Reporting & Analytics Agent

Generates inventory reports, financial reports, and supplier comparison reports.
Supports PDF and Markdown output formats.
Provides visualizations (heatmaps, charts) using Plotly.
"""

from typing import Dict, List
import re
import pandas as pd
import json
import logging
from datetime import datetime
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def _safe_str(s: str) -> str:
    """Sanitize string for safe filename usage."""
    return re.sub(r'[^A-Za-z0-9_-]', '_', s)

# PDF generation
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    Image as RLImage, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
REPORTS_DIR = Path(__file__).parent.parent.parent / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def generate_inventory_report(
    store_ids: List[str],
    start_date: str,
    end_date: str
) -> Dict:
    """
    Generates an inventory report with heatmap and low-stock alerts.

    Args:
        store_ids: List of store IDs
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)

    Returns:
        Dict with paths to PDF/Markdown reports and heatmap HTML
    """
    try:
        from .multi_store_inventory_monitor import monitor_inventory
        inventory = monitor_inventory(store_ids)
        if "error" in inventory:
            return {"error": inventory["error"]}

        # Build heatmap data
        sku_ids = [sku["sku_id"] for sku in inventory["skus"]]
        heatmap_df = pd.DataFrame(index=sku_ids)

        for store_id in store_ids:
            heatmap_df[store_id] = 0

        for sku in inventory["skus"]:
            for store_id in store_ids:
                stock = sku["stock_levels"].get(store_id, {}).get("stock_level", 0)
                heatmap_df.at[sku["sku_id"], store_id] = stock

        # Generate heatmap HTML
        heatmap_fig = px.imshow(
            heatmap_df.values,
            x=heatmap_df.columns.tolist(),
            y=heatmap_df.index.tolist(),
            labels=dict(x="Store", y="SKU", color="Stock Level"),
            color_continuous_scale=["red", "yellow", "green"],
            title="Inventory Heatmap",
            aspect="auto"
        )
        heatmap_html = heatmap_fig.to_html(full_html=False)

        # Generate PDF and Markdown
        safe_store_ids = [_safe_str(s) for s in store_ids]
        report_id = f"inventory_report_{'_'.join(safe_store_ids)}_{start_date}_{end_date}"
        pdf_path = REPORTS_DIR / f"{report_id}.pdf"
        md_path = REPORTS_DIR / f"{report_id}.md"

        _generate_inventory_pdf(heatmap_df, inventory["low_stock_alerts"], pdf_path, store_ids, start_date, end_date)
        _generate_inventory_markdown(heatmap_df, inventory["low_stock_alerts"], md_path, store_ids, start_date, end_date)

        return {
            "pdf_report": str(pdf_path),
            "markdown_report": str(md_path),
            "heatmap_html": heatmap_html
        }

    except Exception as e:
        logger.error(f"Failed to generate inventory report: {e}", exc_info=True)
        return {"error": str(e)}


def _generate_inventory_pdf(
    heatmap_df: pd.DataFrame,
    low_stock_alerts: List[Dict],
    output_path: Path,
    store_ids: List[str],
    start_date: str,
    end_date: str
):
    """Generates a PDF inventory report using ReportLab."""
    doc = SimpleDocTemplate(str(output_path), pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=72)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], alignment=TA_CENTER)
    story.append(Paragraph("Inventory Report", title_style))
    story.append(Spacer(1, 12))

    # Period
    sub_style = ParagraphStyle('Sub', parent=styles['Normal'], alignment=TA_CENTER)
    story.append(Paragraph(f"Period: {start_date} to {end_date}", sub_style))
    story.append(Spacer(1, 24))

    # Heatmap table
    story.append(Paragraph("Inventory Levels", styles['Heading2']))
    story.append(Spacer(1, 12))

    # Prepare table data
    table_data = [["SKU"] + heatmap_df.columns.tolist()]
    for sku_id, row in heatmap_df.iterrows():
        table_data.append([sku_id] + [str(int(val)) for val in row.values])

    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(table)
    story.append(Spacer(1, 24))

    # Low-stock alerts
    story.append(Paragraph("Low-Stock Alerts", styles['Heading2']))
    story.append(Spacer(1, 12))

    if low_stock_alerts:
        alert_data = [["Store", "SKU", "Name", "Current Stock", "Reorder Point", "Recommended Order"]]
        for alert in low_stock_alerts:
            alert_data.append([
                alert["store_id"],
                alert["sku_id"],
                alert["name"],
                str(alert["current_stock"]),
                str(alert["reorder_point"]),
                str(alert["recommended_order"])
            ])

        alert_table = Table(alert_data, repeatRows=1)
        alert_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightcoral if len(low_stock_alerts) > 0 else colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(alert_table)
    else:
        story.append(Paragraph("No low-stock alerts.", styles['Normal']))

    doc.build(story)
    logger.info(f"Generated inventory PDF report: {output_path}")


def _generate_inventory_markdown(
    heatmap_df: pd.DataFrame,
    low_stock_alerts: List[Dict],
    output_path: Path,
    store_ids: List[str],
    start_date: str,
    end_date: str
):
    """Generates a Markdown inventory report."""
    with open(output_path, "w") as f:
        f.write("# Inventory Report\n\n")
        f.write(f"**Period:** {start_date} to {end_date}\n\n")
        f.write(f"**Stores:** {', '.join(store_ids)}\n\n")

        f.write("## Inventory Heatmap\n\n")
        f.write("| SKU | " + " | ".join(heatmap_df.columns.tolist()) + " |\n")
        f.write("|-----|" + "|".join(["---"] * len(heatmap_df.columns)) + "|\n")
        for sku_id, row in heatmap_df.iterrows():
            f.write(f"| {sku_id} | " + " | ".join(str(int(v)) for v in row.values) + " |\n")

        f.write("\n## Low-Stock Alerts\n\n")
        if low_stock_alerts:
            f.write("| Store | SKU | Name | Current Stock | Reorder Point | Recommended Order |\n")
            f.write("|-------|-----|------|---------------|---------------|-------------------|\n")
            for alert in low_stock_alerts:
                f.write(f"| {alert['store_id']} | {alert['sku_id']} | {alert['name']} | {alert['current_stock']} | {alert['reorder_point']} | {alert['recommended_order']} |\n")
        else:
            f.write("No low-stock alerts.\n")

    logger.info(
        "Generated inventory Markdown report: %s",
        output_path,
    )


def generate_financial_report(
    store_id: str,
    start_date: str,
    end_date: str
) -> Dict:
    """
    Generates a financial report with gross margin, inventory turnover, etc.

    Args:
        store_id: Store identifier
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)

    Returns:
        Dict with paths to PDF/Markdown reports and metrics data
    """
    try:
        # In a real system, compute from sales data. Here we use mock metrics.
        # Load sales for calculations
        sales_path = DATA_DIR / "sample_sales.csv"
        if sales_path.exists():
            sales_df = pd.read_csv(sales_path)
            sales_df["date"] = pd.to_datetime(sales_df["date"])
            mask = (sales_df["date"] >= pd.to_datetime(start_date)) & \
                   (sales_df["date"] <= pd.to_datetime(end_date)) & \
                   (sales_df["store_id"] == store_id)
            store_sales = sales_df[mask]
            if not store_sales.empty:
                total_sales = float((store_sales["quantity_sold"] * store_sales["price"]).sum())
                total_cost = float((store_sales["quantity_sold"] * store_sales["cost"]).sum())
                gross_margin = total_sales - total_cost
                gross_margin_pct = (gross_margin / total_sales * 100) if total_sales > 0 else 0.0

                # Inventory turnover = COGS / Avg Inventory
                # Approximate avg inventory: use simple average of beginning and end inventory
                # Simplified: use total sales quantity / average stock
                avg_inventory = 1000  # placeholder
                inventory_turnover = round(total_cost / avg_inventory, 2) if avg_inventory > 0 else 0.0
            else:
                total_sales = 50000.0
                total_cost = 30000.0
                gross_margin = 20000.0
                gross_margin_pct = 40.0
                inventory_turnover = 8.5
        else:
            total_sales = 50000.0
            total_cost = 30000.0
            gross_margin = 20000.0
            gross_margin_pct = 40.0
            inventory_turnover = 8.5

        financial_metrics = {
            "store_id": store_id,
            "period": {"start_date": start_date, "end_date": end_date},
            "metrics": {
                "total_sales_AUD": round(total_sales, 2),
                "total_cost_AUD": round(total_cost, 2),
                "gross_margin_AUD": round(gross_margin, 2),
                "gross_margin_percent": round(gross_margin_pct, 1),
                "inventory_turnover": inventory_turnover,
                "stockout_incidents": 2,  # Placeholder - compute from inventory logs
                "overstock_incidents": 1,
                "emergency_orders_cost_AUD": 500.00
            },
            "top_skus_by_margin": []  # Could compute from sales data
        }

        # Determine top SKUs by margin (mock)
        # In real system, group by SKU and compute margin
        sales_df_top = sales_df[mask] if sales_path.exists() else pd.DataFrame()
        if not sales_df_top.empty:
            sku_margin = sales_df_top.groupby("sku_id").apply(
                lambda g: ((g["price"] - g["cost"]) * g["quantity_sold"]).sum()
            ).sort_values(ascending=False).head(2)
            top_skus = []
            for sku_id, margin in sku_margin.items():
                sku_sales = sales_df_top[sales_df_top["sku_id"] == sku_id]
                total_sales_revenue = (sku_sales["price"] * sku_sales["quantity_sold"]).sum()
                if total_sales_revenue > 0:
                    margin_pct = (margin / total_sales_revenue) * 100
                    if not pd.isna(margin_pct):
                        top_skus.append({
                            "sku_id": sku_id,
                            "gross_margin_AUD": round(margin, 2),
                            "margin_percent": round(margin_pct, 1),
                            "quantity_sold": int(sku_sales["quantity_sold"].sum())
                        })
            financial_metrics["top_skus_by_margin"] = top_skus
        else:
            financial_metrics["top_skus_by_margin"] = [
                {"sku_id": "SKU_001", "gross_margin_AUD": 1200.00, "margin_percent": 48.0, "quantity_sold": 500},
                {"sku_id": "SKU_003", "gross_margin_AUD": 900.00, "margin_percent": 45.0, "quantity_sold": 300}
            ]

        # Generate reports
        safe_store_id = _safe_str(store_id)
        report_id = f"financial_report_{safe_store_id}_{start_date}_{end_date}"
        pdf_path = REPORTS_DIR / f"{report_id}.pdf"
        md_path = REPORTS_DIR / f"{report_id}.md"

        _generate_financial_pdf(financial_metrics, pdf_path)
        _generate_financial_markdown(financial_metrics, md_path)

        return {
            "pdf_report": str(pdf_path),
            "markdown_report": str(md_path),
            "metrics": financial_metrics
        }

    except Exception as e:
        logger.error(f"Failed to generate financial report: {e}", exc_info=True)
        return {"error": str(e)}


def _generate_financial_pdf(metrics: Dict, output_path: Path):
    """Generates a PDF financial report."""
    doc = SimpleDocTemplate(str(output_path), pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=72)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle('Title', parent=styles['Heading1'], alignment=TA_CENTER)
    story.append(Paragraph(f"Financial Report for {metrics['store_id']}", title_style))
    story.append(Spacer(1, 12))

    sub_style = ParagraphStyle('Sub', parent=styles['Normal'], alignment=TA_CENTER)
    story.append(Paragraph(
        f"Period: {metrics['period']['start_date']} to {metrics['period']['end_date']}",
        sub_style
    ))
    story.append(Spacer(1, 24))

    story.append(Paragraph("Financial Metrics", styles['Heading2']))
    story.append(Spacer(1, 12))

    m = metrics['metrics']
    metrics_table_data = [
        ["Metric", "Value"],
        ["Total Sales (AUD)", f"${m['total_sales_AUD']:,.2f}"],
        ["Total Cost (AUD)", f"${m['total_cost_AUD']:,.2f}"],
        ["Gross Margin (AUD)", f"${m['gross_margin_AUD']:,.2f}"],
        ["Gross Margin (%)", f"{m['gross_margin_percent']:.1f}%"],
        ["Inventory Turnover", f"{m['inventory_turnover']:.2f}"],
        ["Stockout Incidents", str(m['stockout_incidents'])],
        ["Overstock Incidents", str(m['overstock_incidents'])],
        ["Emergency Orders Cost (AUD)", f"${m['emergency_orders_cost_AUD']:,.2f}"]
    ]

    t = Table(metrics_table_data, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(t)
    story.append(Spacer(1, 24))

    story.append(Paragraph("Top SKUs by Gross Margin", styles['Heading2']))
    story.append(Spacer(1, 12))

    top_data = [["SKU", "Gross Margin (AUD)", "Margin %", "Qty Sold"]]
    for sku in metrics["top_skus_by_margin"]:
        top_data.append([
            sku["sku_id"],
            f"${sku['gross_margin_AUD']:,.2f}",
            f"{sku['margin_percent']:.1f}%",
            str(sku["quantity_sold"])
        ])

    top_table = Table(top_data, repeatRows=1)
    top_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(top_table)

    doc.build(story)
    logger.info(f"Generated financial PDF report: {output_path}")


def _generate_financial_markdown(metrics: Dict, output_path: Path):
    """Generates a Markdown financial report."""
    with open(output_path, "w") as f:
        f.write(f"# Financial Report for {metrics['store_id']}\n\n")
        f.write(f"**Period:** {metrics['period']['start_date']} to {metrics['period']['end_date']}\n\n")
        f.write("## Financial Metrics\n\n")
        m = metrics['metrics']
        f.write(f"- **Total Sales (AUD):** ${m['total_sales_AUD']:,.2f}\n")
        f.write(f"- **Total Cost (AUD):** ${m['total_cost_AUD']:,.2f}\n")
        f.write(f"- **Gross Margin (AUD):** ${m['gross_margin_AUD']:,.2f}\n")
        f.write(f"- **Gross Margin (%):** {m['gross_margin_percent']:.1f}%\n")
        f.write(f"- **Inventory Turnover:** {m['inventory_turnover']:.2f}\n")
        f.write(f"- **Stockout Incidents:** {m['stockout_incidents']}\n")
        f.write(f"- **Overstock Incidents:** {m['overstock_incidents']}\n")
        f.write(f"- **Emergency Orders Cost (AUD):** ${m['emergency_orders_cost_AUD']:,.2f}\n\n")
        f.write("## Top SKUs by Gross Margin\n\n")
        f.write("| SKU | Gross Margin (AUD) | Margin % | Quantity Sold |\n")
        f.write("|-----|---------------------|----------|---------------|\n")
        for sku in metrics["top_skus_by_margin"]:
            f.write(f"| {sku['sku_id']} | ${sku['gross_margin_AUD']:,.2f} | {sku['margin_percent']:.1f}% | {sku['quantity_sold']} |\n")

    logger.info(f"Generated financial Markdown report: {output_path}")


def generate_supplier_comparison_report() -> Dict:
    """
    Generates a supplier comparison report with lead times and costs.

    Returns:
        Dict with PDF/Markdown paths and supplier data
    """
    try:
        # Load SKU metadata to compute supplier metrics
        with open(DATA_DIR / "sku_metadata.json", "r") as f:
            sku_metadata = json.load(f)

        # Aggregate by supplier
        supplier_stats = {}
        for sku_id, sku in sku_metadata.items():
            supplier = sku.get("supplier", "Unknown")
            if supplier not in supplier_stats:
                supplier_stats[supplier] = {
                    "sku_count": 0,
                    "total_unit_cost": 0.0,
                    "lead_times": [],
                    "bulk_discounts": {},
                    "skus": []
                }
            supplier_stats[supplier]["sku_count"] += 1
            supplier_stats[supplier]["total_unit_cost"] += sku.get("unit_cost", 0.0)
            supplier_stats[supplier]["lead_times"].append(sku.get("lead_time_days", 0))
            supplier_stats[supplier]["skus"].append(sku_id)
            # Merge bulk discounts (take max discount per threshold)
            for thr, disc in sku.get("bulk_discounts", {}).items():
                if thr not in supplier_stats[supplier]["bulk_discounts"] or disc > supplier_stats[supplier]["bulk_discounts"][thr]:
                    supplier_stats[supplier]["bulk_discounts"][thr] = disc

        # Compute averages
        suppliers_output = {}
        for supplier, stats in supplier_stats.items():
            avg_cost = stats["total_unit_cost"] / stats["sku_count"] if stats["sku_count"] > 0 else 0.0
            avg_lead = sum(stats["lead_times"]) / len(stats["lead_times"]) if stats["lead_times"] else 0.0
            suppliers_output[supplier] = {
                "avg_lead_time": round(avg_lead, 1),
                "avg_unit_cost": round(avg_cost, 2),
                "bulk_discounts": stats["bulk_discounts"],
                "reliability": 0.95 if "Metcash" in supplier else 0.90,  # Mock
                "skus": stats["skus"][:10]  # limit
            }

        # Generate reports
        report_id = "supplier_comparison_report"
        pdf_path = REPORTS_DIR / f"{report_id}.pdf"
        md_path = REPORTS_DIR / f"{report_id}.md"

        _generate_supplier_pdf(suppliers_output, pdf_path)
        _generate_supplier_markdown(suppliers_output, md_path)

        return {
            "pdf_report": str(pdf_path),
            "markdown_report": str(md_path),
            "suppliers": suppliers_output
        }

    except Exception as e:
        logger.error(f"Failed to generate supplier comparison report: {e}", exc_info=True)
        return {"error": str(e)}


def _generate_supplier_pdf(suppliers: Dict, output_path: Path):
    """Generates a PDF supplier comparison report."""
    doc = SimpleDocTemplate(str(output_path), pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=72)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle('Title', parent=styles['Heading1'], alignment=TA_CENTER)
    story.append(Paragraph("Supplier Comparison Report", title_style))
    story.append(Spacer(1, 24))

    story.append(Paragraph("Supplier Metrics", styles['Heading2']))
    story.append(Spacer(1, 12))

    header = ["Supplier", "Avg. Lead Time (days)", "Avg. Unit Cost (AUD)", "Bulk Discounts", "Reliability"]
    data = [header]
    for name, s in suppliers.items():
        discounts_str = ", ".join([f"{k} units: {v*100:.0f}%" for k, v in s["bulk_discounts"].items()])
        data.append([
            name,
            f"{s['avg_lead_time']}",
            f"${s['avg_unit_cost']:.2f}",
            discounts_str,
            f"{s['reliability']*100:.0f}%"
        ])

    t = Table(data, repeatRows=1, colWidths=[1.5*inch, 1.2*inch, 1.2*inch, 2*inch, 1*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 9)
    ]))
    story.append(t)
    story.append(Spacer(1, 24))

    story.append(Paragraph("SKUs per Supplier", styles['Heading2']))
    story.append(Spacer(1, 12))
    for name, s in suppliers.items():
        story.append(Paragraph(f"<b>{name}:</b> {', '.join(s['skus'])}", styles['Normal']))
        story.append(Spacer(1, 6))

    doc.build(story)
    logger.info(f"Generated supplier comparison PDF: {output_path}")


def _generate_supplier_markdown(suppliers: Dict, output_path: Path):
    """Generates a Markdown supplier comparison report."""
    with open(output_path, "w") as f:
        f.write("# Supplier Comparison Report\n\n")
        f.write("## Supplier Metrics\n\n")
        f.write("| Supplier | Avg. Lead Time (days) | Avg. Unit Cost (AUD) | Bulk Discounts | Reliability |\n")
        f.write("|----------|----------------------|----------------------|----------------|-------------|\n")
        for name, s in suppliers.items():
            discounts = ", ".join([f"{k} units: {v*100:.0f}%" for k, v in s["bulk_discounts"].items()])
            f.write(f"| {name} | {s['avg_lead_time']} | ${s['avg_unit_cost']:.2f} | {discounts} | {s['reliability']*100:.0f}% |\n")
        f.write("\n\n## SKUs by Supplier\n\n")
        for name, s in suppliers.items():
            f.write(f"**{name}:** {', '.join(s['skus'])}\n")

    logger.info(f"Generated supplier comparison Markdown: {output_path}")
