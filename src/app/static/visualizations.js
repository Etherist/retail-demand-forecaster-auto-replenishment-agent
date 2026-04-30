// Demand Forecast Chart
async function updateForecastChart() {
    const sku = document.getElementById('sku-filter').value;
    const horizon = parseInt(document.getElementById('horizon-filter').value);
    const storeSelect = document.getElementById('store-select');
    const stores = Array.from(storeSelect.selectedOptions).map(opt => opt.value);
    if (stores.length === 0) return;

    const traces = [];
    const colors = ['#3498db', '#e74c3c', '#2ecc71', '#f1c40f', '#9b59b6'];

    for (let i = 0; i < stores.length; i++) {
        const store = stores[i];
        const skuId = sku === 'all' ? 'SKU_001' : sku; // if all, pick first SKU for demo
        const params = new URLSearchParams({
            sku_id: skuId,
            store_id: store,
            horizon_days: horizon
        });

        try {
            const response = await fetch(`/forecast/?${params.toString()}`);
            if (!response.ok) continue;
            const data = await response.json();
            const forecast = data.forecast;
            traces.push({
                x: forecast.map(d => d.date),
                y: forecast.map(d => d.demand),
                type: 'scatter',
                mode: 'lines+markers',
                name: `${skuId} (${store})`,
                line: { color: colors[i % colors.length], width: 3 }
            });
        } catch (err) {
            console.error('Forecast fetch error:', err);
        }
    }

    const layout = {
        title: `Demand Forecast (Horizon: ${horizon} days)`,
        xaxis: { title: 'Date' },
        yaxis: { title: 'Demand (Units)' },
        hovermode: 'x unified',
        margin: { l: 50, r: 20, t: 50, b: 50 }
    };
    Plotly.newPlot('forecast-chart', traces, layout, {responsive: true});
}

// Inventory Heatmap
async function updateInventoryHeatmap() {
    const stores = currentStores;
    if (stores.length === 0) return;

    const query = stores.map(s => `store_ids=${s}`).join('&');
    const response = await fetch(`/inventory/heatmap/?${query}`);
    const data = await response.json();

    const skuIds = data.sku_ids;
    const z = [];
    stores.forEach(store => {
        const row = [];
        skuIds.forEach(sku => {
            const found = data.heatmap_data.find(d => d.sku === sku);
            row.push(found ? found[store] : 0);
        });
        z.push(row);
    });

    const heatmapData = {
        z: z,
        x: skuIds,
        y: stores,
        type: 'heatmap',
        colorscale: [
            [0, 'rgb(255, 0, 0)'],
            [0.5, 'rgb(255, 255, 0)'],
            [1, 'rgb(0, 255, 0)']
        ]
    };

    const layout = {
        title: 'Inventory Heatmap (Units in Stock)',
        xaxis: { title: 'SKU' },
        yaxis: { title: 'Store' },
        margin: { l: 100, r: 20, t: 50, b: 100 }
    };
    Plotly.newPlot('inventory-heatmap', [heatmapData], layout, {responsive: true});

    updateLowStockTable();
}

async function updateLowStockTable() {
    const query = currentStores.map(s => `store_ids=${s}`).join('&');
    const response = await fetch(`/inventory/?${query}`);
    const data = await response.json();

    const tbody = document.getElementById('low-stock-body');
    tbody.innerHTML = '';

    if (data.low_stock_alerts && data.low_stock_alerts.length > 0) {
        data.low_stock_alerts.forEach(alert => {
            const row = tbody.insertRow();
            row.insertCell(0).textContent = alert.store_id;
            row.insertCell(1).textContent = alert.sku_id;
            row.insertCell(2).textContent = alert.name;
            row.insertCell(3).textContent = alert.current_stock;
            row.insertCell(4).textContent = alert.reorder_point;
            row.insertCell(5).textContent = alert.recommended_order;
            const actionCell = row.insertCell(6);
            const btn = document.createElement('button');
            btn.textContent = 'Order';
            btn.onclick = () => quickOrder(alert.store_id, alert.sku_id);
            actionCell.appendChild(btn);
        });
    } else {
        const row = tbody.insertRow();
        const cell = row.insertCell(0);
        cell.colSpan = 7;
        cell.textContent = 'No low-stock alerts. Inventory healthy!';
        cell.style.textAlign = 'center';
        cell.style.color = '#27ae60';
        cell.style.fontWeight = 'bold';
    }
}

// Supplier Comparison
async function updateSupplierComparison() {
    const response = await fetch('/supplier-comparison/');
    const data = await response.json();
    const suppliers = Object.values(data.suppliers);

    // Lead time bar chart
    const leadTrace = {
        x: suppliers.map(s => s.name),
        y: suppliers.map(s => s.avg_lead_time),
        type: 'bar',
        name: 'Avg. Lead Time (days)',
        marker: { color: '#3498db' }
    };
    const leadLayout = {
        title: 'Supplier Lead Time Comparison',
        xaxis: { title: 'Supplier' },
        yaxis: { title: 'Lead Time (days)' },
        margin: { l: 50, r: 20, t: 50, b: 50 }
    };
    Plotly.newPlot('supplier-chart', [leadTrace], leadLayout, {responsive: true});

    // Supplier table
    const tbody = document.getElementById('supplier-body');
    tbody.innerHTML = '';
    Object.entries(data.suppliers).forEach(([name, s]) => {
        const row = tbody.insertRow();
        row.insertCell(0).textContent = name;
        row.insertCell(1).textContent = s.avg_lead_time;
        row.insertCell(2).textContent = `$${s.avg_unit_cost.toFixed(2)}`;
        row.insertCell(3).textContent = Object.entries(s.bulk_discounts)
            .map(([k, v]) => `${k}+ units: ${(v*100).toFixed(0)}%`).join(', ');
        row.insertCell(4).textContent = `${(s.reliability * 100).toFixed(0)}%`;
    });
}

// Financial Metrics
async function updateFinancialMetrics() {
    const storeId = document.getElementById('financial-store').value;
    const startDate = document.getElementById('start-date').value;
    const endDate = document.getElementById('end-date').value;

    const params = new URLSearchParams({ store_id: storeId, start_date: startDate, end_date: endDate });
    const response = await fetch(`/financial-metrics/?${params.toString()}`);
    const data = await response.json();

    const metrics = data.metrics;
    const trace = {
        x: ['Total Sales', 'Total Cost', 'Gross Margin'],
        y: [metrics.total_sales_AUD, metrics.total_cost_AUD, metrics.gross_margin_AUD],
        type: 'bar',
        marker: { color: ['#2ecc71', '#e74c3c', '#3498db'] }
    };
    const layout = {
        title: `Financial Metrics for ${storeId}`,
        xaxis: { title: 'Metric' },
        yaxis: { title: 'Amount (AUD)' },
        margin: { l: 50, r: 20, t: 50, b: 50 }
    };
    Plotly.newPlot('financial-metrics-chart', [trace], layout, {responsive: true});

    // Top SKUs
    const tbody = document.getElementById('top-skus-body');
    tbody.innerHTML = '';
    data.top_skus_by_margin.forEach(sku => {
        const row = tbody.insertRow();
        row.insertCell(0).textContent = sku.sku_id;
        row.insertCell(1).textContent = `$${sku.gross_margin_AUD.toFixed(2)}`;
        row.insertCell(2).textContent = `${sku.margin_percent.toFixed(1)}%`;
        row.insertCell(3).textContent = sku.quantity_sold;
    });
}

// PO Table (empty until generation)
async function updatePOTable() {
    const tbody = document.getElementById('po-body');
    tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;">No POs generated yet.</td></tr>';
}
