"""
Demand Forecaster Agent

Predicts future demand for SKUs using Prophet (time-series) for baseline
and XGBoost to incorporate external factors (weather, holidays, promotions).
"""

from typing import Dict, Optional
import pandas as pd
import numpy as np
import json
import logging
from datetime import timedelta
from pathlib import Path

# Optional Prophet import
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    Prophet = None  # type: ignore

from xgboost import XGBRegressor

from .external_data_fetcher import (
    fetch_weather_data,
    fetch_holidays,
    fetch_promotions,
    get_store_coordinates
)
from .multi_store_inventory_monitor import monitor_inventory

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"

# Cache for loaded sales data to avoid re-reading
_SALES_CACHE = None


def _load_sales_data() -> Optional[pd.DataFrame]:
    """Loads and caches sales data."""
    global _SALES_CACHE
    if _SALES_CACHE is None:
        sales_path = DATA_DIR / "sample_sales.csv"
        if not sales_path.exists():
            logger.error("Sales data file not found")
            return None
        _SALES_CACHE = pd.read_csv(sales_path)
        _SALES_CACHE["date"] = pd.to_datetime(_SALES_CACHE["date"])
    return _SALES_CACHE.copy()


def _create_external_features(
    dates: pd.DatetimeIndex,
    sku_id: str,
    store_id: str
) -> pd.DataFrame:
    """
    Create external feature DataFrame for demand forecasting.
    
    Generates features from weather data, holidays, and promotions
    for the specified date range and location.
    
    Args:
        dates: DatetimeIndex of dates to generate features for
        sku_id: SKU identifier for promotion filtering
        store_id: Store identifier for location-based features
        
    Returns:
        DataFrame with columns: ds, temperature, rainfall, is_holiday,
        is_promotion, day_of_week, month
        
    Raises:
        ValueError: If date range is invalid or data fetch fails
    """
    start_date = dates.min().strftime("%Y-%m-%d")
    end_date = dates.max().strftime("%Y-%m-%d")

    # Get store coordinates
    lat, lng = get_store_coordinates(store_id)

    # Fetch external data
    weather_df = fetch_weather_data(lat, lng, start_date, end_date)
    holidays = fetch_holidays(start_date, end_date)
    promotions = fetch_promotions(sku_id, start_date, end_date)

    # Build feature DataFrame
    df = pd.DataFrame({"ds": dates})
    df["date"] = df["ds"].dt.date

    # Weather features (use nearest available)
    if weather_df is not None:
        weather_df["date"] = weather_df["date"].dt.date
        df = df.merge(weather_df[["date", "temperature", "rainfall"]], on="date", how="left")
        # Fill missing with median
        df["temperature"] = df["temperature"].fillna(df["temperature"].median())
        df["rainfall"] = df["rainfall"].fillna(0.0)
    else:
        df["temperature"] = 20.0  # default
        df["rainfall"] = 0.0

    # Holiday flag
    holiday_dates = {pd.to_datetime(h["date"]).date() for h in holidays}
    df["is_holiday"] = df["date"].isin(holiday_dates).astype(int)

    # Promotion flag
    promo_dates = set()
    for promo in promotions:
        s = pd.to_datetime(promo["start_date"]).date()
        e = pd.to_datetime(promo["end_date"]).date()
        date_range = pd.date_range(start=s, end=e)
        promo_dates.update([d.date() for d in date_range])
    df["is_promotion"] = df["date"].isin(promo_dates).astype(int)

    # Temporal features
    df["day_of_week"] = df["ds"].dt.dayofweek
    df["month"] = df["ds"].dt.month

    # Drop temporary date column
    df = df.drop(columns=["date"])
    return df


def forecast_demand(
    sku_id: str,
    store_id: str,
    horizon_days: int = 7
) -> Optional[Dict]:
    """
    Forecasts demand for a SKU at a store using Prophet + XGBoost hybrid.

    Workflow:
    1. Load historical sales data for the SKU+store.
    2. Fit Prophet on historical data to capture trend/seasonality.
    3. Train XGBoost on Prophet residuals using external features (weather, holidays, promotions).
    4. Predict future baseline with Prophet.
    5. Predict future residuals with XGBoost.
    6. Combine for final forecast.

    Args:
        sku_id: SKU identifier (e.g., "SKU_001")
        store_id: Store identifier (e.g., "STORE_001")
        horizon_days: Number of days to forecast

    Returns:
        Dict with forecast data including dates, demand, confidence intervals,
        reorder point, current stock, and recommended order quantity.
    """
    # Fallback if Prophet not available
    if not PROPHET_AVAILABLE:
        logger.warning("Prophet not installed. Using fallback forecasting model.")
        return _forecast_fallback(sku_id, store_id, horizon_days)

    try:
        # Load sales data
        sales_df = _load_sales_data()
        if sales_df is None:
            raise ValueError("Failed to load sales data")

        # Filter for specific SKU and store
        hist = sales_df[(sales_df["sku_id"] == sku_id) & (sales_df["store_id"] == store_id)].copy()
        if hist.empty:
            raise ValueError(f"No historical data for SKU {sku_id} in store {store_id}")

        hist = hist[["date", "quantity_sold"]].rename(columns={"date": "ds", "quantity_sold": "y"})
        hist = hist.sort_values("ds").reset_index(drop=True)

        # Get current stock (last known inventory - simplified: assume inventory track is separate)
        # For demo, we'll get from inventory monitor or use a placeholder.
        # Instead, we'll compute from sales: assume starting inventory unknown; we'll rely on a mock current stock later.
        # For forecast function, we can assume current_stock is fetched from inventory system.
        # We'll set current_stock to a placeholder here; actual integration will call inventory monitor.
        current_stock = 0  # Placeholder

        # Prepare external features for historical period
        hist_dates = pd.DatetimeIndex(hist["ds"])
        hist_ext = _create_external_features(hist_dates, sku_id, store_id)
        # Merge external features into hist
        hist_full = hist.merge(hist_ext, on="ds", how="left")

        # Fit Prophet
        model = Prophet(
            daily_seasonality=False,
            weekly_seasonality=True,
            yearly_seasonality=True,
            interval_width=0.8  # 80% confidence intervals
        )
        # Add external regressors to Prophet
        for col in ["temperature", "rainfall", "is_holiday", "is_promotion", "day_of_week", "month"]:
            model.add_regressor(col)

        model.fit(hist_full)

        # Create future dataframe
        last_date = hist["ds"].max()
        future_dates = pd.date_range(start=last_date + timedelta(days=1), periods=horizon_days, freq="D")
        future_df = pd.DataFrame({"ds": future_dates})
        # Get external features for future dates
        future_ext = _create_external_features(future_dates, sku_id, store_id)
        future_full = future_df.merge(future_ext, on="ds", how="left")

        # Predict baseline with Prophet
        prophet_forecast = model.predict(future_full)

        # Train XGBoost on residuals
        hist_pred = model.predict(hist_full)
        residuals = hist["y"] - hist_pred["yhat"]

        # Features for XGBoost: external features plus lagged demand
        X_hist = hist_full[[
            "temperature", "rainfall", "is_holiday", "is_promotion",
            "day_of_week", "month"
        ]].copy()
        X_hist["lag_1"] = hist["y"].shift(1).fillna(0)
        X_hist["lag_7"] = hist["y"].shift(7).fillna(0)

        # Encode categorical if needed (already numeric)
        xgb = XGBRegressor(
            n_estimators=50,
            max_depth=3,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42
        )
        xgb.fit(X_hist, residuals)

        # Prepare future features for XGBoost
        X_future = future_full[[
            "temperature", "rainfall", "is_holiday", "is_promotion",
            "day_of_week", "month"
        ]].copy()
        
        # For lag features, recursively forecast: use predicted values as lags for subsequent steps
        # Initialize with last known actual values
        lag_1_val = hist["y"].iloc[-1]
        lag_7_val = hist["y"].iloc[-7] if len(hist) >= 7 else lag_1_val
        
        # Store predictions for each step
        future_residuals = np.zeros(horizon_days)
        
        for i in range(horizon_days):
            # Create feature vector for this step
            X_step = X_future.iloc[i:i+1].copy()
            X_step["lag_1"] = lag_1_val
            X_step["lag_7"] = lag_7_val
            
            # Predict residual for this step
            residual_pred = xgb.predict(X_step)[0]
            future_residuals[i] = residual_pred
            
            # Update lags for next iteration
            # Get prophet prediction for this step
            prophet_pred_i = prophet_forecast.iloc[i]["yhat"]
            final_pred_i = max(0, prophet_pred_i + residual_pred)
            lag_7_val = lag_1_val
            lag_1_val = final_pred_i
        
        # Combine forecasts
        final_forecast = prophet_forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()
        final_forecast["yhat"] = final_forecast["yhat"] + future_residuals
        
        # Calculate combined confidence intervals
        # Prophet provides uncertainty, XGBoost residuals add additional uncertainty
        residual_std = np.std(residuals - xgb.predict(X_hist)) if len(residuals) > 1 else 0
        # Propagate uncertainty: sqrt(prophet_variance + residual_variance)
        prophet_ci_width = (
            final_forecast["yhat_upper"] - final_forecast["yhat_lower"]
        ) / (2 * 1.96)
        combined_ci_lower = final_forecast["yhat"] - 1.96 * np.sqrt(prophet_ci_width**2 + residual_std**2)
        combined_ci_upper = final_forecast["yhat"] + 1.96 * np.sqrt(prophet_ci_width**2 + residual_std**2)
        final_forecast["yhat_lower"] = combined_ci_lower.clip(lower=0).round().astype(int)
        final_forecast["yhat_upper"] = combined_ci_upper.clip(lower=0).round().astype(int)
        final_forecast["yhat"] = final_forecast["yhat"].clip(lower=0).round().astype(int)

        # Load SKU metadata for reorder point
        with open(DATA_DIR / "sku_metadata.json", "r") as f:
            sku_meta = json.load(f)
        sku_info = sku_meta.get(sku_id, {})
        reorder_point = sku_info.get("reorder_point", 0)

        # Load current stock from inventory monitor (simulate via reading inventory data)
        # In a real system, this would query inventory DB. Here we mock by reading from a static file or generating.
        # We'll read from inventory monitor to keep consistent.
        from .multi_store_inventory_monitor import monitor_inventory
        inv_data = monitor_inventory([store_id])
        if "error" not in inv_data:
            for sku in inv_data["skus"]:
                if sku["sku_id"] == sku_id:
                    current_stock = sku["stock_levels"].get(store_id, {}).get("stock_level", 0)
                    break

        # Recommended order quantity: max(0, total forecasted demand over lead time - current stock)
        # Use sum of forecast over horizon as demand estimate, or reorder point approach
        total_forecast_demand = final_forecast["yhat"].sum()
        recommended_order = max(0, int(total_forecast_demand - current_stock))
        # Ensure at least min order quantity
        min_order_qty = sku_info.get("min_order_quantity", 1)
        if recommended_order > 0 and recommended_order < min_order_qty:
            recommended_order = min_order_qty

        # Format output
        forecast_list = []
        for _, row in final_forecast.iterrows():
            forecast_list.append({
                "date": row["ds"].strftime("%Y-%m-%d"),
                "demand": int(row["yhat"]),
                "confidence_interval": [int(row["yhat_lower"]), int(row["yhat_upper"])]
            })

        output = {
            "sku_id": sku_id,
            "store_id": store_id,
            "forecast_horizon_days": horizon_days,
            "forecast": forecast_list,
            "reorder_point": reorder_point,
            "current_stock": current_stock,
            "recommended_order_quantity": recommended_order
        }

        logger.info(f"Generated demand forecast for {sku_id} at {store_id} (horizon: {horizon_days} days)")
        return output
    except Exception as e:
        logger.error(f"Failed to forecast demand for {sku_id} at {store_id}: {e}", exc_info=True)
        return None


def _forecast_fallback(sku_id: str, store_id: str, horizon_days: int) -> Optional[Dict]:
    """
    Simple fallback forecaster when Prophet is unavailable.
    Uses historical average with day-of-week and holiday/promo adjustments.
    """
    try:
        sales_df = _load_sales_data()
        if sales_df is None:
            raise ValueError("No sales data")
        hist = sales_df[(sales_df["sku_id"] == sku_id) & (sales_df["store_id"] == store_id)].copy()
        if hist.empty:
            raise ValueError(f"No history for {sku_id} at {store_id}")

        hist["date"] = pd.to_datetime(hist["date"])
        hist = hist.sort_values("date")

        # Compute day-of-week factors
        hist["dow"] = hist["date"].dt.dayofweek
        dow_means = hist.groupby("dow")["quantity_sold"].mean()
        overall_mean = hist["quantity_sold"].mean()
        dow_factors = (dow_means / overall_mean).to_dict()

        # Baseline: average of last 30 days
        recent = hist[hist["date"] >= (hist["date"].max() - pd.Timedelta(days=30))]
        base_demand = recent["quantity_sold"].mean()
        if pd.isna(base_demand) or base_demand <= 0:
            base_demand = overall_mean

        # Get promotions and holidays for future dates
        last_date = hist["date"].max()
        future_dates = pd.date_range(start=last_date + timedelta(days=1), periods=horizon_days, freq="D")
        start_str = future_dates.min().strftime("%Y-%m-%d")
        end_str = future_dates.max().strftime("%Y-%m-%d")
        holidays = fetch_holidays(start_str, end_str)
        promotions = fetch_promotions(sku_id, start_str, end_str)

        holiday_dates = {pd.to_datetime(h["date"]).date() for h in holidays}
        promo_dates = set()
        for promo in promotions:
            s = pd.to_datetime(promo["start_date"]).date()
            e = pd.to_datetime(promo["end_date"]).date()
            date_range = pd.date_range(start=s, end=e)
            promo_dates.update([d.date() for d in date_range])

        forecast = []
        for dt in future_dates:
            d = base_demand
            # Day of week factor
            dow_factor = dow_factors.get(dt.dayofweek, 1.0)
            d *= dow_factor
            # Holiday boost
            if dt.date() in holiday_dates:
                d *= 1.3
            # Promotion boost
            if dt.date() in promo_dates:
                d *= 1.2
            demand = max(0, int(round(d)))
            # Confidence interval: ±20%
            lower = max(0, int(round(demand * 0.8)))
            upper = int(round(demand * 1.2))
            forecast.append({
                "date": dt.strftime("%Y-%m-%d"),
                "demand": demand,
                "confidence_interval": [lower, upper]
            })

        # Get current stock & reorder point from metadata & inventory
        with open(DATA_DIR / "sku_metadata.json", "r") as f:
            sku_meta = json.load(f)
        reorder_point = sku_meta.get(sku_id, {}).get("reorder_point", 0)
        inv_data = monitor_inventory([store_id])
        current_stock = 0
        if "error" not in inv_data:
            for sku in inv_data["skus"]:
                if sku["sku_id"] == sku_id:
                    current_stock = sku["stock_levels"].get(store_id, {}).get("stock_level", 0)
                    break
        total_forecast_demand = sum(d["demand"] for d in forecast)
        recommended_order = max(0, int(total_forecast_demand - current_stock))
        min_order_qty = sku_meta.get(sku_id, {}).get("min_order_quantity", 1)
        if recommended_order > 0 and recommended_order < min_order_qty:
            recommended_order = min_order_qty

        return {
            "sku_id": sku_id,
            "store_id": store_id,
            "forecast_horizon_days": horizon_days,
            "forecast": forecast,
            "reorder_point": reorder_point,
            "current_stock": current_stock,
            "recommended_order_quantity": recommended_order
        }

    except Exception as e:
        logger.error(f"Fallback forecast failed: {e}")
        return None
