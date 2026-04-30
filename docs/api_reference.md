# API Reference

## Overview

The Retail Demand Forecaster provides a RESTful API for demand forecasting, inventory management, and automated replenishment. All endpoints return JSON responses.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://api.retail-forecaster.com`

## Authentication

Currently, the API does not require authentication for demo purposes. In production, API keys or OAuth2 will be required.

## Rate Limiting

- **Development**: Unlimited
- **Production**: 1000 requests/hour per API key

## Response Format

All responses follow this structure:

```json
{
  "status": "success|error",
  "data": { ... },
  "message": "Human-readable message",
  "timestamp": "2026-04-30T11:44:39Z"
}
```

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid parameters |
| 404 | Not Found - Resource doesn't exist |
| 422 | Unprocessable Entity - Validation failed |
| 500 | Internal Server Error - Server-side issue |

---

## Endpoints

### Health Check

#### `GET /health/`

Check if the service is healthy.

**Response** (200 OK):
```json
{
  "status": "healthy",
  "timestamp": "2026-04-30T11:44:39Z",
  "version": "1.0.0"
}
```

---

### Demand Forecasting

#### `POST /forecast/`

Generate demand forecast for a specific SKU and store.

**Request Body**:
```json
{
  "sku_id": "SKU_001",
  "store_id": "STORE_001",
  "horizon_days": 7
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| sku_id | string | Yes | SKU identifier (e.g., "SKU_001") |
| store_id | string | Yes | Store identifier (e.g., "STORE_001") |
| horizon_days | integer | No | Forecast horizon in days (default: 7, max: 90) |

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "sku_id": "SKU_001",
    "store_id": "STORE_001",
    "forecast_horizon_days": 7,
    "forecast": [
      {
        "date": "2026-05-01",
        "demand": 45,
        "confidence_interval": [40, 50]
      },
      {
        "date": "2026-05-02",
        "demand": 50,
        "confidence_interval": [45, 55]
      }
    ],
    "reorder_point": 30,
    "current_stock": 25,
    "recommended_order_quantity": 100
  },
  "message": "Forecast generated successfully",
  "timestamp": "2026-04-30T11:44:39Z"
}
```

**Error Response** (400 Bad Request):
```json
{
  "status": "error",
  "data": null,
  "message": "Invalid SKU ID format",
  "timestamp": "2026-04-30T11:44:39Z"
}
```

---

### Inventory Management

#### `GET /inventory/`

Get current inventory levels.

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| store_ids | array | No | Comma-separated store IDs (e.g., "STORE_001,STORE_002") |

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "stores": [
      {
        "store_id": "STORE_001",
        "skus": [
          {
            "sku_id": "SKU_001",
            "name": "Product A",
            "stock_level": 150,
            "reorder_point": 100,
            "unit_cost": 2.50
          }
        ]
      }
    ]
  },
  "message": "Inventory retrieved successfully",
  "timestamp": "2026-04-30T11:44:39Z"
}
```

---

#### `GET /inventory/heatmap/`

Get inventory heatmap data for visualization.

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| store_ids | array | No | Comma-separated store IDs |

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "heatmap": [
      {
        "sku_id": "SKU_001",
        "STORE_001": 150,
        "STORE_002": 200
      }
    ],
    "stores": ["STORE_001", "STORE_002"],
    "skus": ["SKU_001", "SKU_002"]
  },
  "message": "Heatmap data retrieved",
  "timestamp": "2026-04-30T11:44:39Z"
}
```

---

### Purchase Order Management

#### `POST /generate-po/`

Generate a purchase order for a single store.

**Request Body**:
```json
{
  "store_ids": ["STORE_001"],
  "sku_ids": ["SKU_001", "SKU_002"]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| store_ids | array | Yes | List of store IDs |
| sku_ids | array | No | List of SKU IDs (optional, all if omitted) |

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "po_id": "PO_20260501_001",
    "stores": ["STORE_001"],
    "supplier": "Metcash",
    "items": [
      {
        "sku_id": "SKU_001",
        "name": "Product A",
        "quantity": 100,
        "unit_cost": 2.50,
        "total": 250.00
      }
    ],
    "total_quantity": 100,
    "total_cost": 250.00,
    "bulk_discount_applied": 0.1,
    "delivery_date": "2026-05-03",
    "status": "generated"
  },
  "message": "Purchase order generated",
  "timestamp": "2026-04-30T11:44:39Z"
}
```

---

#### `POST /generate-multi-store-po/`

Generate consolidated purchase order for multiple stores.

**Request Body**:
```json
{
  "store_ids": ["STORE_001", "STORE_002"],
  "sku_ids": ["SKU_001", "SKU_002"]
}
```

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "po_id": "PO_20260501_002",
    "stores": ["STORE_001", "STORE_002"],
    "supplier": "Metcash",
    "items": [
      {
        "sku_id": "SKU_001",
        "quantity": 180,
        "unit_cost": 2.50,
        "total": 450.00
      }
    ],
    "total_quantity": 180,
    "total_cost": 450.00,
    "bulk_discount_applied": 0.15,
    "delivery_date": "2026-05-03",
    "status": "generated"
  },
  "message": "Multi-store purchase order generated",
  "timestamp": "2026-04-30T11:44:39Z"
}
```

---

#### `POST /send-po/`

Send a purchase order to supplier.

**Request Body**:
```json
{
  "po_id": "PO_20260501_001",
  "method": "email"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| po_id | string | Yes | Purchase order ID |
| method | string | No | "email" or "api" (default: "email") |

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "po_id": "PO_20260501_001",
    "method": "email",
    "status": "sent",
    "timestamp": "2026-04-30T11:44:39Z"
  },
  "message": "Purchase order sent successfully",
  "timestamp": "2026-04-30T11:44:39Z"
}
```

---

### Financial Analytics

#### `GET /financial-metrics/`

Get financial metrics for a store.

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| store_id | string | Yes | Store identifier |
| start_date | string | Yes | Start date (YYYY-MM-DD) |
| end_date | string | Yes | End date (YYYY-MM-DD) |

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "store_id": "STORE_001",
    "period": {
      "start_date": "2025-05-01",
      "end_date": "2026-04-30"
    },
    "metrics": {
      "total_sales_AUD": 50000.00,
      "total_cost_AUD": 30000.00,
      "gross_margin_AUD": 20000.00,
      "gross_margin_percent": 40.0,
      "inventory_turnover": 8.5,
      "stockout_incidents": 2,
      "overstock_incidents": 1,
      "emergency_orders_cost_AUD": 500.00
    },
    "top_skus_by_margin": [
      {
        "sku_id": "SKU_001",
        "gross_margin_AUD": 1200.00,
        "margin_percent": 48.0,
        "quantity_sold": 500
      }
    ]
  },
  "message": "Financial metrics calculated",
  "timestamp": "2026-04-30T11:44:39Z"
}
```

---

#### `GET /supplier-comparison/`

Compare supplier performance metrics.

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "suppliers": [
      {
        "name": "Metcash",
        "avg_lead_time": 3.5,
        "avg_unit_cost": 2.50,
        "bulk_discounts": {
          "100": 0.1,
          "500": 0.15
        },
        "reliability": 0.95
      }
    ]
  },
  "message": "Supplier comparison generated",
  "timestamp": "2026-04-30T11:44:39Z"
}
```

---

### Reporting

#### `GET /reports/inventory/`

Generate inventory report.

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| store_ids | array | Yes | Comma-separated store IDs |
| start_date | string | Yes | Start date (YYYY-MM-DD) |
| end_date | string | Yes | End date (YYYY-MM-DD) |
| format | string | No | "pdf" or "md" (default: "pdf") |

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "report_id": "inventory_20260501_001",
    "format": "pdf",
    "file_path": "/reports/inventory_20260501_001.pdf",
    "file_size": 245760,
    "generated_at": "2026-04-30T11:44:39Z"
  },
  "message": "Inventory report generated",
  "timestamp": "2026-04-30T11:44:39Z"
}
```

---

#### `GET /reports/financial/`

Generate financial report.

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| store_id | string | Yes | Store identifier |
| start_date | string | Yes | Start date (YYYY-MM-DD) |
| end_date | string | Yes | End date (YYYY-MM-DD) |
| format | string | No | "pdf" or "md" (default: "pdf") |

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "report_id": "financial_20260501_001",
    "format": "pdf",
    "file_path": "/reports/financial_20260501_001.pdf",
    "file_size": 184320,
    "generated_at": "2026-04-30T11:44:39Z"
  },
  "message": "Financial report generated",
  "timestamp": "2026-04-30T11:44:39Z"
}
```

---

#### `GET /reports/supplier-comparison/`

Generate supplier comparison report.

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "report_id": "supplier_20260501_001",
    "format": "pdf",
    "file_path": "/reports/supplier_20260501_001.pdf",
    "file_size": 153600,
    "generated_at": "2026-04-30T11:44:39Z"
  },
  "message": "Supplier comparison report generated",
  "timestamp": "2026-04-30T11:44:39Z"
}
```

---

## SDK Examples

### Python

```python
import requests

BASE_URL = "http://localhost:8000"

# Generate forecast
response = requests.post(f"{BASE_URL}/forecast/", json={
    "sku_id": "SKU_001",
    "store_id": "STORE_001",
    "horizon_days": 7
})
forecast = response.json()

# Generate PO
response = requests.post(f"{BASE_URL}/generate-po/", json={
    "store_ids": ["STORE_001"],
    "sku_ids": ["SKU_001", "SKU_002"]
})
po = response.json()

# Send PO
response = requests.post(f"{BASE_URL}/send-po/", json={
    "po_id": po["data"]["po_id"],
    "method": "email"
})
```

### JavaScript

```javascript
const BASE_URL = 'http://localhost:8000';

// Generate forecast
const forecast = await fetch(`${BASE_URL}/forecast/`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    sku_id: 'SKU_001',
    store_id: 'STORE_001',
    horizon_days: 7
  })
}).then(r => r.json());

// Generate PO
const po = await fetch(`${BASE_URL}/generate-po/`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    store_ids: ['STORE_001'],
    sku_ids: ['SKU_001', 'SKU_002']
  })
}).then(r => r.json());
```

### cURL

```bash
# Generate forecast
curl -X POST http://localhost:8000/forecast/ \
  -H "Content-Type: application/json" \
  -d '{
    "sku_id": "SKU_001",
    "store_id": "STORE_001",
    "horizon_days": 7
  }'

# Generate PO
curl -X POST http://localhost:8000/generate-po/ \
  -H "Content-Type: application/json" \
  -d '{
    "store_ids": ["STORE_001"],
    "sku_ids": ["SKU_001", "SKU_002"]
  }'

# Send PO
curl -X POST http://localhost:8000/send-po/ \
  -H "Content-Type: application/json" \
  -d '{
    "po_id": "PO_20260501_001",
    "method": "email"
  }'
```

---

## Webhooks

### Event Types

| Event | Description | Payload |
|-------|-------------|---------|
| `po.generated` | PO created | PO details |
| `po.sent` | PO sent to supplier | PO ID, method |
| `low_stock` | Stock below threshold | SKU, store, level |

### Configuration

Configure webhooks via environment variables:
```bash
WEBHOOK_URL=https://your-app.com/webhooks
WEBHOOK_SECRET=your-secret-key
```

---

## Best Practices

1. **Error Handling**: Always check response status codes
2. **Rate Limiting**: Implement exponential backoff for retries
3. **Caching**: Cache forecast results for 1 hour
4. **Timeouts**: Set request timeout to 30 seconds
5. **Validation**: Validate all inputs before sending

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-04-30 | Initial release |

---

*For support, contact: api-support@retail-forecaster.com*