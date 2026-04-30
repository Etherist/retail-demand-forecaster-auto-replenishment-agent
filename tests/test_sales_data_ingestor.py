"""
Tests for Sales Data Ingestor Agent
"""

import pytest
import pandas as pd
from src.agents.sales_data_ingestor import ingest_sales_data

def test_ingest_valid_csv(tmp_path, sample_sales_df):
    """Test ingestion of a valid CSV file."""
    csv_path = tmp_path / "sales.csv"
    sample_sales_df.to_csv(csv_path, index=False)

    result = ingest_sales_data(str(csv_path))

    assert result is not None
    assert isinstance(result, pd.DataFrame)
    assert len(result) == len(sample_sales_df)
    assert set(result.columns) == {"date", "sku_id", "store_id", "quantity_sold", "price", "cost"}
    assert pd.api.types.is_datetime64_any_dtype(result["date"])

def test_ingest_missing_columns(tmp_path):
    """Test ingestion fails if required columns missing."""
    df = pd.DataFrame({"date": ["2025-05-01"], "sku_id": ["SKU_001"]})
    csv_path = tmp_path / "bad.csv"
    df.to_csv(csv_path, index=False)

    result = ingest_sales_data(str(csv_path))
    assert result is None  # Should fail

def test_ingest_file_not_found():
    """Test ingestion handles missing file."""
    result = ingest_sales_data("nonexistent.csv")
    assert result is None

def test_ingest_invalid_dates(tmp_path):
    """Test ingestion converts dates properly even with bad formats."""
    df = pd.DataFrame({
        "date": ["2025-05-01", "invalid"],
        "sku_id": ["SKU_001", "SKU_002"],
        "store_id": ["STORE_001", "STORE_002"],
        "quantity_sold": [10, 20],
        "price": [2.5, 1.8],
        "cost": [2.0, 1.5]
    })
    csv_path = tmp_path / "bad_dates.csv"
    df.to_csv(csv_path, index=False)

    result = ingest_sales_data(str(csv_path))
    # The second row should be dropped due to NaT, first row remains
    assert result is not None
    assert len(result) == 1

def test_ingest_non_negative_quantity(tmp_path):
    """Test that negative quantities are filtered out."""
    df = pd.DataFrame({
        "date": ["2025-05-01"] * 3,
        "sku_id": ["SKU_001", "SKU_002", "SKU_003"],
        "store_id": ["STORE_001"] * 3,
        "quantity_sold": [10, -5, 20],
        "price": [2.5, 1.8, 3.0],
        "cost": [2.0, 1.5, 2.5]
    })
    csv_path = tmp_path / "neg_qty.csv"
    df.to_csv(csv_path, index=False)

    result = ingest_sales_data(str(csv_path))
    assert result is not None
    assert len(result) == 2  # negative removed
