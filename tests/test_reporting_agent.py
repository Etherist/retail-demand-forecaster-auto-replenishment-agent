"""
Tests for Reporting & Analytics Agent
"""

import pytest
import json
from pathlib import Path
from src.agents.reporting_agent import (
    generate_inventory_report,
    generate_financial_report,
    generate_supplier_comparison_report
)

def test_generate_inventory_report(tmp_path, monkeypatch):
    """Test inventory report generation."""
    # Override REPORTS_DIR to temp
    from src.agents import reporting_agent
    monkeypatch.setattr(reporting_agent, "REPORTS_DIR", tmp_path)

    report = generate_inventory_report(
        store_ids=["STORE_001", "STORE_002"],
        start_date="2025-05-01",
        end_date="2025-05-31"
    )
    assert "error" not in report
    assert "pdf_report" in report
    assert "markdown_report" in report
    assert "heatmap_html" in report
    # Check files exist
    assert Path(report["pdf_report"]).exists()
    assert Path(report["markdown_report"]).exists()

def test_generate_financial_report(tmp_path, monkeypatch):
    """Test financial report generation."""
    from src.agents import reporting_agent
    monkeypatch.setattr(reporting_agent, "REPORTS_DIR", tmp_path)

    report = generate_financial_report(
        store_id="STORE_001",
        start_date="2025-05-01",
        end_date="2025-05-31"
    )
    assert "error" not in report
    assert "pdf_report" in report
    assert "markdown_report" in report
    assert "metrics" in report
    metrics = report["metrics"]["metrics"]
    assert "total_sales_AUD" in metrics
    assert "gross_margin_AUD" in metrics
    assert Path(report["pdf_report"]).exists()

def test_generate_supplier_comparison_report(tmp_path, monkeypatch):
    """Test supplier comparison report."""
    from src.agents import reporting_agent
    monkeypatch.setattr(reporting_agent, "REPORTS_DIR", tmp_path)

    report = generate_supplier_comparison_report()
    assert "error" not in report
    assert "pdf_report" in report
    assert "markdown_report" in report
    assert "suppliers" in report
    suppliers = report["suppliers"]
    assert "Metcash" in suppliers or "PFD Food Services" in suppliers
    assert Path(report["pdf_report"]).exists()
    assert Path(report["markdown_report"]).exists()
