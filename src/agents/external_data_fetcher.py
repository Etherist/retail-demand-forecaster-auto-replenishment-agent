"""
External Data Fetcher Agent

Retrieves weather data (from BOM API mock), public holidays, and promotions.
Provides functions to fetch and format external factors for demand forecasting.
"""

from typing import List, Dict, Optional
import pandas as pd
import numpy as np
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"


def fetch_weather_data(
    lat: float,
    lng: float,
    start_date: str,
    end_date: str
) -> Optional[pd.DataFrame]:
    """
    Fetches mock weather data for the given location and date range.

    Args:
        lat: Latitude of the store location
        lng: Longitude of the store location
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        DataFrame with columns: date, temperature, rainfall, location
    """
    try:
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        dates = pd.date_range(start=start, end=end)

        # Generate synthetic weather data with realistic patterns
        # Base temperature with seasonal variation (Australian seasons)
        base_temps = {
            1: 26,   # Jan (summer)
            2: 26,   # Feb
            3: 24,   # Mar (autumn)
            4: 21,
            5: 18,
            6: 15,   # Jun (winter)
            7: 14,
            8: 15,
            9: 18,   # Sep (spring)
            10: 20,
            11: 22,
            12: 24   # Dec
        }

        temperatures = []
        rainfall = []

        for date in dates:
            # Seasonal temperature with daily variation
            month_avg = base_temps[date.month]
            day_temp = month_avg + (date.day % 7 - 3) * 0.5  # ±1.5°C variation
            temperatures.append(round(day_temp, 1))

            # Rainfall: 20% chance of rain, between 1-30mm
            if np.random.random() < 0.2:
                rain = round(np.random.uniform(1, 30), 1)
            else:
                rain = 0.0
            rainfall.append(rain)

        data = {
            "date": dates,
            "temperature": temperatures,
            "rainfall": rainfall,
            "location": f"{lat},{lng}"
        }
        df = pd.DataFrame(data)
        logger.info(f"Generated weather data for {lat},{lng} from {start_date} to {end_date} ({len(df)} days)")
        return df

    except Exception as e:
        logger.error(f"Failed to fetch weather data: {e}")
        return None


def fetch_holidays(start_date: str, end_date: str) -> List[Dict]:
    """
    Fetches Australian public holidays and retail events from pre-loaded JSON.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        List of holiday dictionaries with name, date, type, impact
    """
    try:
        holidays_file = DATA_DIR / "australian_holidays.json"
        if not holidays_file.exists():
            logger.warning("Holidays file not found, returning empty list")
            return []

        with open(holidays_file, "r") as f:
            all_holidays = json.load(f)

        result = []
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)

        for year, events in all_holidays.items():
            for event in events:
                event_date = pd.to_datetime(event["date"])
                if start_dt <= event_date <= end_dt:
                    result.append(event)

        logger.info(f"Found {len(result)} holidays/events between {start_date} and {end_date}")
        return result

    except Exception as e:
        logger.error(f"Failed to fetch holidays: {e}")
        return []


def fetch_promotions(
    sku_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[Dict]:
    """
    Fetches promotions from pre-loaded JSON, optionally filtered by SKU and date range.

    Args:
        sku_id: Optional SKU ID to filter promotions
        start_date: Optional start date filter (YYYY-MM-DD)
        end_date: Optional end date filter (YYYY-MM-DD)

    Returns:
        List of promotion dictionaries
    """
    try:
        promotions_file = DATA_DIR / "promotions.json"
        if not promotions_file.exists():
            logger.warning("Promotions file not found, returning empty list")
            return []

        with open(promotions_file, "r") as f:
            all_promotions = json.load(f)

        result = []
        start_dt = pd.to_datetime(start_date) if start_date else None
        end_dt = pd.to_datetime(end_date) if end_date else None

        for year, year_promotions in all_promotions.items():
            for promo in year_promotions:
                # SKU filter
                if sku_id and promo.get("sku_id") != sku_id:
                    continue

                # Date range filters
                promo_start = pd.to_datetime(promo["start_date"])
                promo_end = pd.to_datetime(promo["end_date"])

                if start_dt and promo_end < start_dt:
                    continue
                if end_dt and promo_start > end_dt:
                    continue

                result.append(promo)

        logger.info(f"Found {len(result)} promotions for SKU {sku_id or 'all'}")
        return result

    except Exception as e:
        logger.error(f"Failed to fetch promotions: {e}")
        return []


def get_store_coordinates(store_id: str) -> tuple:
    """
    Returns mock latitude/longitude for a given store ID.
    In production, this would query a store database.

    Args:
        store_id: Store identifier (e.g., "STORE_001")

    Returns:
        Tuple of (latitude, longitude)
    """
    store_coords = {
        "STORE_001": (-33.8688, 151.2093),   # Sydney CBD
        "STORE_002": (-37.8136, 144.9631),   # Melbourne North
        "STORE_003": (-27.4698, 153.0251),   # Brisbane Central
    }
    return store_coords.get(store_id, (0.0, 0.0))
