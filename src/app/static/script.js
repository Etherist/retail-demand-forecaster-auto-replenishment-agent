// Global state
let currentStores = ["STORE_001", "STORE_002"];

// Store filter
function applyStoreFilter() {
    const select = document.getElementById('store-select');
    currentStores = Array.from(select.selectedOptions).map(opt => opt.value);
    updateForecastChart();
    updateInventoryHeatmap();
    updateSupplierComparison();
    updateFinancialMetrics();
    updatePOTable();
}

// Order SKU quick action
function quickOrder(storeId, skuId) {
    const confirmed = confirm(`Generate PO for ${skuId} at ${storeId}?`);
    if (confirmed) {
        document.getElementById('po-store').value = [storeId];
        openTab('po');
    }
}

// PO generation
async function generateMultiStorePO() {
    const stores = Array.from(document.getElementById('po-store').selectedOptions).map(opt => opt.value);
    if (stores.length === 0) {
        alert('Please select at least one store.');
        return;
    }
    const params = stores.map(s => `store_ids=${s}`).join('&');
    const response = await fetch(`/generate-multi-store-po/?${params}`, { method: 'POST' });
    const po = await response.json();
    if (po.error) {
        alert(`Error: ${po.error}`);
        return;
    }
    addPOToTable(po);
    alert(`PO ${po.po_id} generated successfully!`);
}

function addPOToTable(po) {
    const tbody = document.getElementById('po-body');
    if (tbody.rows.length === 1 && tbody.rows[0].cells[0].colSpan === 9) {
        tbody.innerHTML = '';
    }
    const row = tbody.insertRow();
    row.insertCell(0).textContent = po.po_id;
    row.insertCell(1).textContent = po.store_ids.join(', ');
    row.insertCell(2).textContent = po.supplier;
    row.insertCell(3).textContent = po.items.map(i => `${i.sku_id}: ${i.quantity}`).join(', ');
    row.insertCell(4).textContent = `$${po.total_cost.toFixed(2)}`;
    row.insertCell(5).textContent = `${(po.bulk_discount_applied * 100).toFixed(0)}%`;
    row.insertCell(6).textContent = po.delivery_date;
    row.insertCell(7).textContent = po.status;
    const actionCell = row.insertCell(8);
    const sendBtn = document.createElement('button');
    sendBtn.textContent = 'Send';
    sendBtn.onclick = () => sendPO(po.po_id);
    actionCell.appendChild(sendBtn);
}

async function sendPO(poId) {
    const method = confirm('Send via email? (OK=email, Cancel=API)') ? 'email' : 'api';
    const response = await fetch(`/send-po/?po_id=${poId}&method=${method}`, { method: 'POST' });
    const result = await response.json();
    if (result.status === 'sent') {
        alert(`PO ${poId} sent via ${method}.`);
    } else {
        alert('Failed to send PO.');
    }
}

// Reports
async function generateReport(type) {
    const storeId = document.getElementById('report-store').value;
    const startDate = document.getElementById('report-start').value;
    const endDate = document.getElementById('report-end').value;

    let endpoint;
    if (type === 'inventory') {
        endpoint = `/reports/inventory/?store_ids=${storeId}&start_date=${startDate}&end_date=${endDate}`;
    } else if (type === 'financial') {
        endpoint = `/reports/financial/?store_id=${storeId}&start_date=${startDate}&end_date=${endDate}`;
    } else {
        endpoint = '/reports/supplier-comparison/';
    }

    const response = await fetch(endpoint);
    const report = await response.json();
    if (report.error) {
        alert(`Error: ${report.error}`);
        return;
    }

    const linksDiv = document.getElementById('report-links');
    linksDiv.innerHTML = `
        <a href="${report.pdf_report}" target="_blank">📄 Download PDF Report</a>
        <a href="${report.markdown_report}" target="_blank">📝 Download Markdown Report</a>
        ${report.heatmap_html ? '<h4>Heatmap Preview:</h4>' + report.heatmap_html : ''}
    `;
}

// Load SKU dropdown
async function loadSKUs() {
    const response = await fetch('/inventory/?store_ids=STORE_001');
    const data = await response.json();
    const skuSelect = document.getElementById('sku-filter');
    skuSelect.innerHTML = '<option value="all">All SKUs</option>';
    data.skus.forEach(sku => {
        const opt = document.createElement('option');
        opt.value = sku.sku_id;
        opt.textContent = `${sku.sku_id} - ${sku.name}`;
        skuSelect.appendChild(opt);
    });
}

// Tab switching
function openTab(tabName) {
    const tabs = document.querySelectorAll('.tab-content');
    tabs.forEach(tab => tab.style.display = 'none');
    const buttons = document.querySelectorAll('.tab-button');
    buttons.forEach(btn => btn.classList.remove('active'));
    document.getElementById(tabName).style.display = 'block';
    event.currentTarget.classList.add('active');
}

// Initialize on load
window.onload = async function() {
    await loadSKUs();
    updateForecastChart();
    updateInventoryHeatmap();
    updateSupplierComparison();
    updateFinancialMetrics();
    updatePOTable();
};
