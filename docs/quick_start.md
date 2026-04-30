# Quick Start Guide

## Get Up and Running in 5 Minutes

### Prerequisites
- Docker and Docker Compose (recommended)
- OR Python 3.10+ and UV
- OR Kubernetes cluster (for production)

### Option 1: One-Command Startup (Docker)

```bash
# Clone and start
git clone <your-repo-url>
cd retail-demand-forecaster-auto-replenishment-agent
make docker-up
```

That's it! Access:
- **Dashboard**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Mock API**: http://localhost:8001

### Option 2: Local Development

```bash
# 1. Install dependencies
make install

# 2. Generate sample data
make generate-data

# 3. Start mock supplier API (in one terminal)
make mock-api

# 4. Start main server (in another terminal)
make dev
```

### Option 3: Kubernetes Production

```bash
# Build and push images
make docker-build

# Deploy to cluster
make k8s-apply

# Monitor deployment
make k8s-status
```

---

## Try These Commands

### Generate a Forecast
```bash
curl -X POST http://localhost:8000/forecast/ \
  -H "Content-Type: application/json" \
  -d '{"sku_id": "SKU_001", "store_id": "STORE_001", "horizon_days": 7}'
```

### Check Inventory
```bash
curl "http://localhost:8000/inventory/?store_ids=STORE_001"
```

### Generate a Purchase Order
```bash
curl -X POST http://localhost:8000/generate-po/ \
  -H "Content-Type: application/json" \
  -d '{"store_ids": ["STORE_001"], "sku_ids": ["SKU_001", "SKU_002"]}'
```

### View Financial Metrics
```bash
curl "http://localhost:8000/financial-metrics/?store_id=STORE_001&start_date=2025-05-01&end_date=2026-04-30"
```

---

## What's Next?

1. **Customize for Your Business**
   - Replace sample data with your own
   - Configure SKU metadata
   - Set up real supplier integrations

2. **Integrate with Your Systems**
   - Connect to ERP for live sales data
   - Link to WMS for inventory sync
   - Export POs to accounting

3. **Scale Up**
   - Deploy to production K8s cluster
   - Add more stores and SKUs
   - Enable real-time streaming

4. **Enhance**
   - Add custom ML models
   - Implement authentication
   - Set up monitoring/alerting

---

## Troubleshooting

**Port already in use?**
```bash
# Change ports in docker-compose.yml or use different ports
# For local: uvicorn src.app.main:app --port 8001
```

**Tests failing?**
```bash
# Ensure you're using the project virtual environment
source /home/aetherist/projects/llm_engineering/.venv/bin/activate
make test
```

**Docker build fails?**
```bash
# Clear Docker cache and rebuild
docker compose build --no-cache
```

**Need help?**
- Check logs: `make docker-logs` or `make k8s-logs`
- Read full docs: `/docs/` folder
- Open an issue on GitHub

---

## Ready for Production?

This demo uses mock data and hardcoded values. For production:

1. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your SMTP, API keys, database URLs
   ```

2. **Set Up Database**
   ```sql
   # Replace in-memory DataFrames with PostgreSQL
   # See docs/architecture.md for schema
   ```

3. **Enable Authentication**
   ```python
   # Add OAuth2/JWT middleware
   # See FastAPI security docs
   ```

4. **Configure Monitoring**
   ```yaml
   # Add Prometheus metrics endpoint
   # Set up Grafana dashboards
   ```

5. **Deploy to Production K8s**
   ```bash
   # Update k8s/ manifests with your values
   make k8s-apply
   ```

---

**Want a guided walkthrough?** See [Demo Guide](demo_guide.md) for detailed scenarios.
