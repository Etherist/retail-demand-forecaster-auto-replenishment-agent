#!/usr/bin/env python3
"""
Data Generation Script for Retail Demand Forecaster

This script generates comprehensive mock data for the demo:
- 12 months of historical sales data for 50-100 SKUs across 2-3 stores
- SKU metadata with categories, suppliers, lead times, reorder points, bulk discounts
- Store metadata with locations and details
- Australian public holidays and events
- Promotions data
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

# Set random seed for reproducibility
np.random.seed(42)

# Configuration
NUM_SKUS = 75
NUM_STORES = 3
START_DATE = datetime(2025, 5, 1)
END_DATE = datetime(2026, 4, 30)
DATA_DIR = Path("src/data")

# Ensure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

# -------------------- Generate Store Metadata --------------------
STORE_IDS = [f"STORE_{i:03d}" for i in range(1, NUM_STORES + 1)]
CITIES = ["Sydney", "Melbourne", "Brisbane"]
REGIONS = ["NSW", "VIC", "QLD"]

store_metadata = {}
for i, (store_id, city, region) in enumerate(zip(STORE_IDS, CITIES, REGIONS)):
    store_metadata[store_id] = {
        "name": f"{city} {['CBD', 'North', 'South'][i % 3]}",
        "address": f"{100 + i*100} Main St, {city}, {region}",
        "size_sqm": int(np.random.choice([1500, 2000, 2500, 3000])),
        "manager": f"Manager {chr(65 + i)}",
        "region": region,
        "city": city,
        "latitude": {
            "Sydney": -33.8688,
            "Melbourne": -37.8136,
            "Brisbane": -27.4698
        }[city],
        "longitude": {
            "Sydney": 151.2093,
            "Melbourne": 144.9631,
            "Brisbane": 153.0251
        }[city]
    }

# Save store metadata
with open(DATA_DIR / "store_metadata.json", "w") as f:
    json.dump(store_metadata, f, indent=2)

print(f"✓ Generated store metadata for {NUM_STORES} stores")

# -------------------- Generate SKU Metadata --------------------
CATEGORIES = {
    "Dairy": ["Milk", "Cheese", "Yogurt", "Butter"],
    "Bakery": ["Bread", "Rolls", "Cakes", "Pastries"],
    "Produce": ["Apples", "Bananas", "Tomatoes", "Lettuce"],
    "Meat": ["Chicken", "Beef", "Pork", "Sausages"],
    "Beverages": ["Soft Drink", "Juice", "Water", "Coffee"],
    "Pantry": ["Rice", "Pasta", "Canned Beans", "Sauces"],
    "Frozen": ["Ice Cream", "Frozen Veggies", "Frozen Pizza"],
    "Personal Care": ["Shampoo", "Toothpaste", "Soap"],
    "Cleaning": ["Detergent", "Disinfectant", "Bleach"],
    "Snacks": ["Chips", "Chocolate", "Biscuits", "Nuts"]
}

SUPPLIERS = ["Metcash", "PFD Food Services", "Toll Group", "CEVA Logistics"]

SKU_IDS = [f"SKU_{i:03d}" for i in range(1, NUM_SKUS + 1)]

sku_metadata = {}
for sku_id in SKU_IDS:
    # Randomly assign category and product
    category = np.random.choice(list(CATEGORIES.keys()))
    product = np.random.choice(CATEGORIES[category])

    # Assign supplier based on category heuristics
    if category in ["Dairy", "Bakery", "Pantry"]:
        supplier = "Metcash"
    elif category in ["Frozen", "Meat"]:
        supplier = "PFD Food Services"
    else:
        supplier = np.random.choice(SUPPLIERS[:2])

    # Generate realistic parameters
    unit_cost = round(np.random.uniform(0.8, 15.0), 2)
    selling_price = round(unit_cost * np.random.uniform(1.2, 1.5), 2)
    shelf_life_days = np.random.choice([3, 7, 14, 30, 90, 365])

    # Reorder point: ~5-10 days of average demand
    avg_daily_demand = np.random.randint(10, 100)
    reorder_point = avg_daily_demand * np.random.choice([5, 7, 10])

    # Lead time (1-5 days)
    lead_time_days = np.random.randint(1, 6)

    # Minimum order quantity
    min_order_qty = np.random.choice([10, 20, 50, 100])

    # Bulk discounts
    bulk_discounts = {}
    if min_order_qty >= 50:
        bulk_discounts["50"] = round(np.random.uniform(0.03, 0.08), 2)
    if min_order_qty >= 100:
        bulk_discounts["100"] = round(np.random.uniform(0.08, 0.15), 2)
    if min_order_qty >= 200:
        bulk_discounts["200"] = round(np.random.uniform(0.15, 0.20), 2)

    sku_metadata[sku_id] = {
        "name": f"{product} {np.random.choice(['2L', '1kg', '500g', '1L', 'Dozen'])}" if category != "Beverages" else f"{product} {np.random.choice(['330ml', '1.5L', '500ml'])}",
        "category": category,
        "supplier": supplier,
        "lead_time_days": int(lead_time_days),
        "reorder_point": int(reorder_point),
        "unit_cost": float(unit_cost),
        "selling_price": float(selling_price),
        "min_order_quantity": int(min_order_qty),
        "shelf_life_days": int(shelf_life_days),
        "bulk_discounts": {str(k): float(v) for k, v in bulk_discounts.items()},
        "is_seasonal": bool(category in ["Frozen", "Beverages"] and np.random.random() > 0.5),
        "perishable": bool(shelf_life_days <= 7)
    }

# Save SKU metadata
with open(DATA_DIR / "sku_metadata.json", "w") as f:
    json.dump(sku_metadata, f, indent=2)

print(f"✓ Generated SKU metadata for {NUM_SKUS} SKUs")

# -------------------- Generate Sales Data --------------------
sales_records = []
current_date = START_DATE

# Seasonality patterns by category
seasonal_factors = {
    "Frozen": {"summer": 1.3, "winter": 0.8},  # Ice cream
    "Beverages": {"summer": 1.4, "winter": 0.7},  # Cold drinks
    "Meat": {"summer": 1.1, "winter": 1.2},  # BBQ seasons
    "Dairy": {"summer": 1.0, "winter": 1.0},
    "Bakery": {"summer": 1.0, "winter": 1.0}
}

# Weekend effects (higher sales on weekends)
weekend_multiplier = 1.3

# Base demand for each SKU per day (per store)
base_demands = {}
for sku_id in SKU_IDS:
    base_demands[sku_id] = int(np.random.randint(20, 80))

# Generate daily sales for each store and SKU
while current_date <= END_DATE:
    month = current_date.month
    day_of_week = current_date.weekday()
    is_weekend = day_of_week >= 5
    is_summer = month in [12, 1, 2]  # Australian summer (Dec-Feb)
    is_winter = month in [6, 7, 8]   # Australian winter (Jun-Aug)

    for store_id in STORE_IDS:
        for sku_id in SKU_IDS:
            sku_info = sku_metadata[sku_id]
            base = base_demands[sku_id]

            # Apply seasonal multipliers
            seasonal_factor = 1.0
            if sku_info["is_seasonal"]:
                if is_summer:
                    seasonal_factor = 1.3 if np.random.random() > 0.3 else 1.0
                elif is_winter:
                    seasonal_factor = 1.3 if np.random.random() > 0.7 else 1.0

            # Apply weekend effect (higher for some categories)
            weekend_factor = weekend_multiplier if is_weekend and sku_info["category"] in ["Beverages", "Snacks"] else 1.0

            # Random daily variation
            daily_variation = np.random.uniform(0.8, 1.2)

            # Store-specific factor (some stores sell more)
            store_factor = 0.9 if store_id == "STORE_002" else 1.1 if store_id == "STORE_001" else 1.0

            # Calculate final quantity
            quantity = int(base * seasonal_factor * weekend_factor * daily_variation * store_factor)

            # Add some randomness (Poisson distribution for count data)
            quantity = max(0, np.random.poisson(quantity) if quantity > 0 else 0)

            if quantity > 0:  # Only record days with sales
                sales_records.append({
                    "date": current_date.strftime("%Y-%m-%d"),
                    "sku_id": sku_id,
                    "store_id": store_id,
                    "quantity_sold": quantity,
                    "price": sku_info["selling_price"],
                    "cost": sku_info["unit_cost"]
                })

    current_date += timedelta(days=1)

# Create DataFrame and save
sales_df = pd.DataFrame(sales_records)
sales_df.to_csv(DATA_DIR / "sample_sales.csv", index=False)
print(f"✓ Generated {len(sales_records):,} sales records covering {(END_DATE - START_DATE).days} days")

# -------------------- Generate Holidays --------------------
AUSTRALIAN_HOLIDAYS = {
    2025: [
        {"name": "New Year's Day", "date": "2025-01-01", "type": "public", "impact": "high"},
        {"name": "Australia Day", "date": "2025-01-26", "type": "public", "impact": "medium"},
        {"name": "Labour Day (NSW/VIC)", "date": "2025-03-10", "type": "public", "impact": "medium"},
        {"name": "Good Friday", "date": "2025-04-18", "type": "public", "impact": "high"},
        {"name": "Easter Monday", "date": "2025-04-21", "type": "public", "impact": "high"},
        {"name": "Anzac Day", "date": "2025-04-25", "type": "public", "impact": "medium"},
        {"name": "King's Birthday", "date": "2025-06-09", "type": "public", "impact": "low"},
        {"name": "Darwin Show Day", "date": "2025-07-28", "type": "regional", "impact": "low"},
        {"name": "Labour Day (QLD)", "date": "2025-10-06", "type": "public", "impact": "medium"},
        {"name": "Christmas Day", "date": "2025-12-25", "type": "public", "impact": "very_high"},
        {"name": "Boxing Day", "date": "2025-12-26", "type": "public", "impact": "high"},
        {"name": "New Year's Eve", "date": "2025-12-31", "type": "public", "impact": "medium"}
    ],
    2026: [
        {"name": "New Year's Day", "date": "2026-01-01", "type": "public", "impact": "high"},
        {"name": "Australia Day", "date": "2026-01-26", "type": "public", "impact": "medium"},
        {"name": "Labour Day (NSW/VIC)", "date": "2026-03-09", "type": "public", "impact": "medium"},
        {"name": "Good Friday", "date": "2026-04-03", "type": "public", "impact": "high"},
        {"name": "Easter Monday", "date": "2026-04-06", "type": "public", "impact": "high"},
        {"name": "Anzac Day", "date": "2026-04-25", "type": "public", "impact": "medium"},
        {"name": "King's Birthday", "date": "2026-06-08", "type": "public", "impact": "low"},
        {"name": "Darwin Show Day", "date": "2026-07-27", "type": "regional", "impact": "low"},
        {"name": "Labour Day (QLD)", "date": "2026-10-05", "type": "public", "impact": "medium"},
        {"name": "Christmas Day", "date": "2026-12-25", "type": "public", "impact": "very_high"},
        {"name": "Boxing Day", "date": "2026-12-26", "type": "public", "impact": "high"},
        {"name": "New Year's Eve", "date": "2026-12-31", "type": "public", "impact": "medium"}
    ]
}

# Add special retail events
RETAIL_EVENTS = {
    2025: [
        {"name": "AFL Grand Final", "date": "2025-09-27", "type": "sporting", "impact": "high", "categories": ["Beverages", "Snacks"]},
        {"name": "NRL Grand Final", "date": "2025-10-05", "type": "sporting", "impact": "high", "categories": ["Beverages", "Snacks"]},
        {"name": "Black Friday", "date": "2025-11-28", "type": "shopping", "impact": "very_high", "categories": ["All"]},
        {"name": "Cyber Monday", "date": "2025-12-01", "type": "shopping", "impact": "high", "categories": ["All"]},
        {"name": "Easter Long Weekend", "date": "2025-04-18", "type": "holiday", "impact": "high", "categories": ["All"],
         "end_date": "2025-04-21"},
        {"name": "School Holidays ( NSW )", "date": "2025-04-07", "type": "school", "impact": "medium", "categories": ["Beverages", "Snacks", "Frozen"],
         "end_date": "2025-04-25"},
        {"name": "School Holidays (VIC)", "date": "2025-04-07", "type": "school", "impact": "medium", "categories": ["Beverages", "Snacks", "Frozen"],
         "end_date": "2025-04-25"}
    ],
    2026: [
        {"name": "AFL Grand Final", "date": "2026-09-26", "type": "sporting", "impact": "high", "categories": ["Beverages", "Snacks"]},
        {"name": "NRL Grand Final", "date": "2026-10-04", "type": "sporting", "impact": "high", "categories": ["Beverages", "Snacks"]},
        {"name": "Black Friday", "date": "2026-11-27", "type": "shopping", "impact": "very_high", "categories": ["All"]},
        {"name": "Cyber Monday", "date": "2026-11-30", "type": "shopping", "impact": "high", "categories": ["All"]},
        {"name": "Easter Long Weekend", "date": "2026-04-03", "type": "holiday", "impact": "high", "categories": ["All"],
         "end_date": "2026-04-06"},
        {"name": "School Holidays (NSW)", "date": "2026-04-06", "type": "school", "impact": "medium", "categories": ["Beverages", "Snacks", "Frozen"],
         "end_date": "2026-04-24"},
        {"name": "School Holidays (VIC)", "date": "2026-04-06", "type": "school", "impact": "medium", "categories": ["Beverages", "Snacks", "Frozen"],
         "end_date": "2026-04-24"}
    ]
}

# Combine all holidays and events
all_holidays = {}
for year in [2025, 2026]:
    all_holidays[str(year)] = AUSTRALIAN_HOLIDAYS[year] + RETAIL_EVENTS[year]

with open(DATA_DIR / "australian_holidays.json", "w") as f:
    json.dump(all_holidays, f, indent=2)

print(f"✓ Generated holiday/event data for 2 years")

# -------------------- Generate Promotions --------------------
promotions = {
    "2025": [],
    "2026": []
}

# Major retail promotions/promotional periods
PROMO_PERIODS = [
    {"name": "Anzac Day Sale", "start": "2025-04-20", "end": "2025-04-26", "discount": 0.15, "skus": "all"},
    {"name": "Winter Warm-Up", "start": "2025-06-01", "end": "2025-08-31", "discount": 0.10, "skus": ["Pantry", "Meat", "Beverages"]},
    {"name": "Back to School", "start": "2025-01-15", "end": "2025-02-15", "discount": 0.20, "skus": ["Pantry", "Snacks", "Beverages"]},
    {"name": "Easter Promo", "start": "2025-04-01", "end": "2025-04-20", "discount": 0.25, "skus": ["Dairy", "Bakery", "Beverages"]},
    {"name": "Christmas Season", "start": "2025-12-01", "end": "2025-12-24", "discount": 0.15, "skus": "all"},
    {"name": "Australia Day", "start": "2025-01-20", "end": "2025-01-28", "discount": 0.10, "skus": ["Beverages", "Snacks", "Meat"]},
    {"name": "Black Friday", "start": "2025-11-24", "end": "2025-11-30", "discount": 0.30, "skus": "all"},
    {"name": "Summer Refresh", "start": "2025-12-20", "end": "2026-02-28", "discount": 0.15, "skus": ["Beverages", "Frozen"]},
]

# Generate promo entries for each year
for year_offset, year in enumerate([2025, 2026]):
    for promo in PROMO_PERIODS:
        start_dt = datetime.strptime(promo["start"].replace("2025", str(year)), "%Y-%m-%d")
        end_dt = datetime.strptime(promo["end"].replace("2025", str(year)), "%Y-%m-%d")

        # Only include if within our data range
        if start_dt <= END_DATE and end_dt >= START_DATE:
            affected_skus = SKU_IDS if promo["skus"] == "all" else [
                sku_id for sku_id in SKU_IDS
                if sku_metadata[sku_id]["category"] in promo["skus"]
            ][:int(np.random.randint(10, 30))]  # Random subset

            if affected_skus:
                for sku_id in affected_skus:
                    promotions[str(year)].append({
                        "sku_id": sku_id,
                        "name": promo["name"],
                        "start_date": start_dt.strftime("%Y-%m-%d"),
                        "end_date": end_dt.strftime("%Y-%m-%d"),
                        "discount_rate": promo["discount"],
                        "type": "percentage"
                    })

with open(DATA_DIR / "promotions.json", "w") as f:
    json.dump(promotions, f, indent=2)

print(f"✓ Generated promotion data for 2 years")

# -------------------- Summary --------------------
print(f"\n✅ Data generation complete!")
print(f"   - Stores: {NUM_STORES}")
print(f"   - SKUs: {NUM_SKUS}")
print(f"   - Sales records: {len(sales_records):,}")
print(f"   - Date range: {START_DATE.strftime('%Y-%m-%d')} to {END_DATE.strftime('%Y-%m-%d')}")
print(f"\nFiles created:")
for f in DATA_DIR.iterdir():
    if f.is_file():
        size = f.stat().st_size / 1024
        print(f"   - {f.name} ({size:.1f} KB)")
