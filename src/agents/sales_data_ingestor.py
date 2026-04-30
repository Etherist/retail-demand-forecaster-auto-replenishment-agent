"""
Sales Data Ingestor Agent

Ingests historical sales data for SKUs from retail ERP systems (CSV files).
Validates data structure and returns a clean Pandas DataFrame.
"""

import pandas as pd
from typing import Optional
import logging

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = {"date", "sku_id", "store_id", "quantity_sold", "price", "cost"}


def ingest_sales_data(file_path: str) -> Optional[pd.DataFrame]:
    """
    Ingests sales data from a CSV file.

    Args:
        file_path: Path to the CSV file containing sales data

    Returns:
        Pandas DataFrame with validated sales data, or None if ingestion fails

    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If required columns are missing or data is invalid
    """
    try:
        df = pd.read_csv(file_path)

        # Validate required columns
        missing_cols = REQUIRED_COLUMNS - set(df.columns)
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        # Convert date to datetime (coerce invalid dates to NaT)
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

        # Validate data types
        df["quantity_sold"] = pd.to_numeric(df["quantity_sold"], errors="coerce").fillna(0).astype(int)
        df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0).astype(float)
        df["cost"] = pd.to_numeric(df["cost"], errors="coerce").fillna(0).astype(float)

        # Drop rows with invalid values
        initial_rows = len(df)
        df = df.dropna(subset=["sku_id", "store_id", "date"])
        if len(df) < initial_rows:
            logger.warning(f"Dropped {initial_rows - len(df)} rows with invalid data")

        # Ensure positive quantities
        df = df[df["quantity_sold"] >= 0]

        # Sort by date for time-series consistency
        df = df.sort_values("date").reset_index(drop=True)

        logger.info(f"Successfully ingested {len(df)} sales records from {file_path}")
        return df

    except FileNotFoundError:
        logger.error(f"Sales data file not found: {file_path}")
        return None
    except pd.errors.EmptyDataError:
        logger.error(f"Sales data file is empty: {file_path}")
        return None
    except Exception as e:
        logger.error(f"Failed to ingest sales data from {file_path}: {e}")
        return None
