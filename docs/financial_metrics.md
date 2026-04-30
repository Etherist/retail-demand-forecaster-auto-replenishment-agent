# Financial Metrics

This document explains the financial metrics used to evaluate the effectiveness of the replenishment system.

## 1. Gross Margin

**Formula**:  
`Gross Margin (AUD) = Total Sales Revenue - Total Cost of Goods Sold (COGS)`  
`Gross Margin % = (Gross Margin / Total Sales Revenue) × 100`

**Interpretation**:  
Measures profitability of sold inventory. A higher margin indicates better pricing power or lower procurement costs.

**Calculation** (for a store over a period):
```python
total_sales = sum(quantity_sold * price)
total_cost = sum(quantity_sold * unit_cost)
gross_margin = total_sales - total_cost
gross_margin_pct = gross_margin / total_sales * 100
```

## 2. Inventory Turnover Ratio

**Formula**:  
`Inventory Turnover = COGS / Average Inventory Value`

**Interpretation**:  
How many times inventory is sold and replaced over a period. Higher turnover indicates efficient inventory management and less capital tied up.

- **High turnover**: Good sales, minimal overstock.
- **Low turnover**: Potential overstock, obsolescence risk.

In our demo, average inventory is approximated; production would use beginning + ending inventory / 2.

## 3. Stockout Incidents

Count of unique SKUs where stock level dropped below reorder point during the period, leading to potential lost sales.

**Impact**: Lost revenue, customer dissatisfaction.

## 4. Overstock Incidents

Count of SKUs where inventory significantly exceeds forecasted demand (e.g., stock > 2× reorder point), indicating excess capital tied up.

**Impact**: Increased holding costs, waste (especially for perishables).

## 5. Emergency Orders Cost

Additional costs incurred when stockouts force expedited orders from suppliers (e.g., air freight, premium pricing).

**Goal**: Reduce emergency orders through proactive forecasting.

## 6. Cost Savings from Bulk Discounts

When POs meet supplier bulk thresholds (e.g., ≥100 units), discounts are applied. The system aggregates demand across stores to maximize discount eligibility.

**Example**:
- Order 90 units: no discount → cost = 90 × $2.00 = $180
- Order 110 units: 10% discount → cost = 110 × $1.80 = $198 (more units for slightly higher cost, lower per-unit price)

## 7. Gross Margin by SKU

Identifies top-performing products by profitability. Helps category managers prioritize stocking and promotion strategies.

## Metrics in the Dashboard

The Financial Metrics tab displays:
- Total Sales (AUD)
- Total Cost (AUD)
- Gross Margin (AUD) and %
- Inventory Turnover
- Stockout / Overstock incident counts
- Emergency order costs
- Top 5 SKUs by gross margin

## How These Metrics Are Calculated in the Demo

For simplicity, financial metrics are derived from available sales data. In a production system:

- **COGS**: would come from purchase invoice data.
- **Average Inventory**: would be measured by periodic stock takes.
- **Stockout Detection**: would require POS data indicating lost sales when items unavailable.

Our mock calculations provide realistic values to demonstrate ROI to retail stakeholders.

## ROI Demonstration

The system aims to deliver:
- **50% reduction in stockouts** → fewer lost sales.
- **30% reduction in overstock** → less capital tied up.
- **20% reduction in emergency orders** → lower expediting costs.
- **Increased gross margin** via bulk discounts and better product mix.

By monitoring these metrics pre- and post-deployment, retailers can quantify value.
