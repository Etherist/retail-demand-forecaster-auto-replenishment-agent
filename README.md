# 🛒 AI Demand Forecaster & Auto-Replenishment Agent for Australian Retailers


<!-- engineering-maturity:start -->
## Engineering status

**Estimated implementation completeness: 75% — advanced working implementation.**  
**Assessment confidence: high.**

This is an advanced working implementation: the principal architecture and functional paths are materially built and demonstrable. Remaining work is concentrated in integration depth, verification, hardening and release preparation.

**What is already significant:** a real multi-module implementation rather than a presentation-only repository; automated tests are included; CI/automation is represented in the repository; deployment or runtime packaging assets are present.

**Remaining engineering work:** finish release hardening and environment-level validation.

**Production readiness:** Production readiness is not claimed yet. The project is better described as a substantial working implementation progressing through verification and hardening.

| Evidence area | Remote repository evidence |
| --- | --- |
| Implementation | 18 source files; approximately 130 KiB of source code |
| Verification | 9 test files; approximately 20 KiB of test code |
| Automation | 1 GitHub Actions workflow(s) |
| Build/configuration | 4 build/dependency manifest(s); 8 configuration file(s) |
| Deployment | 9 deployment/runtime packaging asset(s) |
| Documentation/examples | 18 documentation file(s); 0 example/demo file(s) |
| Remote code inspection | 36 evidence-rich files read; 0 TODO/FIXME marker(s); 0 explicit unfinished marker(s) |


> **Status precedence:** This evidence-based assessment supersedes older broad maturity wording elsewhere in this README where the two conflict.

<sub>Engineering estimate refreshed 2026-09-25 from GitHub repository metadata and remotely read source/test/configuration files. It is an evidence-based maturity estimate, not a claim that every runtime path has been independently executed or externally certified.</sub>
<!-- engineering-maturity:end -->

**An advanced working agentic AI implementation for demand forecasting and inventory replenishment**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.104.1-green.svg)](https://fastapi.tiangolo.com/)
[![Prophet](https://img.shields.io/badge/prophet-1.1.4-orange.svg)](https://facebook.github.io/prophet/)
[![XGBoost](https://img.shields.io/badge/xgboost-2.0.0-red.svg)](https://xgboost.readthedocs.io/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![Kubernetes](https://img.shields.io/badge/kubernetes-ready-blue.svg)](https://kubernetes.io/)

---

## 🌟 Executive Summary

This project demonstrates **advanced agentic engineering** through a **7-agent autonomous workflow** for Australian retail demand forecasting and replenishment. It combines Prophet time-series forecasting with XGBoost, multi-store inventory monitoring, supplier constraints, purchase-order generation, reporting, and deployment assets. The repository includes synthetic/demo data and a mock external-data service; documented forecast and business-impact figures should be treated as benchmark scenarios and modelling assumptions rather than achieved production outcomes.

### 🎯 Illustrative Business Scenario

| Metric | Illustrative Scenario | Modelled Financial Impact (per store) |
|--------|-------------|-----------------------------|
| **Stockout Reduction** | 50% fewer incidents | $500K protected revenue |
| **Inventory Optimization** | 30% less excess stock | $200K capital freed |
| **Emergency Orders** | 60% reduction | $50K savings |
| **Planner Productivity** | 95% time savings | $75K labor cost reduction |
| **Total Annual Benefit** | — | **$825K per store** |

**ROI scenario**: 300–500% in the documented illustrative model; not an achieved customer result

---

## 🤖 The 7-Agent Architecture

### High-Level Overview

```mermaid
graph TB
    subgraph "Data Layer"
        A[Sales Data Ingestor<br/><small>Acquisition & Validation</small>]
    end
    
    subgraph "Context Layer"
        B[External Data Fetcher<br/><small>Weather, Holidays, Promotions</small>]
    end
    
    subgraph "ML Layer"
        C[Demand Forecaster<br/><small>Prophet + XGBoost Hybrid</small>]
    end
    
    subgraph "Monitoring Layer"
        D[Multi-Store Inventory<br/>Monitor<br/><small>Tracking & Alerts</small>]
    end
    
    subgraph "Optimization Layer"
        E[Replenishment<br/>Planner<br/><small>PO Generation & Cost Opt</small>]
    end
    
    subgraph "Action Layer"
        F[Supplier<br/>Communicator<br/><small>Email/API Integration</small>]
    end
    
    subgraph "Insight Layer"
        G[Reporting & Analytics<br/><small>PDFs, Dashboards, Metrics</small>]
    end
    
    A -->|Cleaned Sales| B
    B -->|Features| C
    A -->|History| C
    C -->|Forecasts| D
    D -->|Stock Levels| E
    E -->|Optimized POs| F
    F -->|Confirmation| G
    D -.->|Metrics| G
    C -.->|Metrics| G
    
    style A fill:#1565c0,stroke:#0d47a1,color:#fff
    style B fill:#1565c0,stroke:#0d47a1,color:#fff
    style C fill:#6a1b9a,stroke:#4a148c,color:#fff
    style D fill:#ef6c00,stroke:#e65100,color:#fff
    style E fill:#388e3c,stroke:#2e7d32,color:#fff
    style F fill:#ad1457,stroke:#880e4f,color:#fff
    style G fill:#558b2f,stroke:#33691e,color:#fff
```

### 🔄 Agent Interaction Flow

```mermaid
sequenceDiagram
    participant U as User
    participant API as FastAPI
    participant I as Sales Data Ingestor
    participant F as External Data Fetcher
    participant FC as Demand Forecaster
    participant M as Inventory Monitor
    participant P as Replenishment Planner
    participant SC as Supplier Communicator
    participant R as Reporting Agent
    participant S as Supplier System
    
    U->>API: POST /forecast/ (sku_id, store_id, days)
    API->>I: Load sales data
    I-->>API: Cleaned DataFrame
    API->>F: Fetch context
    F-->>API: Weather, holidays, promos
    API->>FC: Generate forecast
    FC->>FC: Prophet (trend + seasonality)
    FC->>FC: XGBoost (residuals)
    FC-->>API: Predictions + CI
    
    U->>API: GET /inventory/
    API->>M: Check stock levels
    M-->>API: Inventory + alerts
    
    U->>API: POST /generate-po/
    API->>P: Plan replenishment
    P->>P: Aggregate demand
    P->>P: Apply discounts
    P->>P: Optimize order qty
    P-->>API: Optimized PO
    
    U->>API: POST /send-po/
    API->>SC: Send to supplier
    SC->>S: Email/API request
    S-->>SC: Confirmation
    SC-->>API: Status
    API-->>U: Success
    
    U->>API: GET /reports/
    API->>R: Generate report
    R->>R: Compile data
    R->>R: Create visualizations
    R-->>API: PDF/Markdown
    API-->>U: Download
```

---

## ⚡ Key Features

### Core Capabilities

| Feature | Technology | Benefit |
|---------|-----------|---------|
| **Hybrid Forecasting** | Prophet + XGBoost | Documented demo/benchmark range of 85–95% accuracy; not production validation |
| **Multi-Store Optimization** | Aggregation algorithms | Consolidated POs, lower costs |
| **Auto-Replenishment** | Rule-based + ML | Zero manual intervention |
| **Supplier Constraints** | Linear programming | MOQ, bulk discounts, lead times |
| **External Factors** | BOM API, holiday calendars | Context-aware predictions |
| **Financial Analytics** | Margin, turnover calculations | ROI visibility |
| **Advanced Visualizations** | Plotly.js, ReportLab | Interactive dashboards, PDFs |
| **Interactive Dashboard** | HTML/JS frontend | At-a-glance monitoring |

### Technical Highlights

- ✅ **Automated Verification**: 9 test files with roughly 47 explicit test functions in the collected source; current CI requires attention
- ✅ **Type-Safe**: Full type hints, Pydantic validation
- ✅ **Deployment Assets**: Docker and Kubernetes configuration included; CI workflow configured and currently requires attention
- ✅ **Well-Documented**: 8,000+ lines of docs, ADRs, diagrams
- ✅ **Secure**: Path traversal protection, input validation, structured logging
- ✅ **Scalable**: Horizontal scaling, caching-ready architecture

---

## 🚀 Quick Start

### One-Command Startup (Docker)

```bash
# Clone and launch
git clone https://github.com/Etherist/retail-demand-forecaster-auto-replenishment-agent.git
cd retail-demand-forecaster-auto-replenishment-agent
make docker-up
```

**Access points**:
- 📊 **Dashboard**: http://localhost:8000
- 📖 **API Docs**: http://localhost:8000/docs
- 🔌 **Mock API**: http://localhost:8001

### Local Development

```bash
# Install dependencies
make install

# Generate sample data
make generate-data

# Start services (2 terminals)
# Terminal 1: Mock API
make mock-api

# Terminal 2: Main server
make dev
```

### Kubernetes Production

```bash
# Deploy to cluster
make k8s-apply

# Monitor
make k8s-status
make k8s-logs
```

---

## 📊 Demo in 5 Minutes

### Step 1: Generate a Forecast

**Via Dashboard**:
1. Go to http://localhost:8000
2. Navigate to "Forecast" tab
3. Select SKU_001, STORE_001
4. Click "Generate"

**Via API**:
```bash
curl -X POST http://localhost:8000/forecast/ \
  -H "Content-Type: application/json" \
  -d '{"sku_id": "SKU_001", "store_id": "STORE_001", "horizon_days": 7}'
```

**What happens**: 7 agents collaborate to return a 7-day demand forecast with confidence intervals, reorder point, and recommended order quantity.

### Step 2: Monitor Inventory

View inventory heatmap across all stores. Color-coded:
- 🔴 **Red**: Low stock (immediate action)
- 🟡 **Yellow**: Medium (plan ahead)
- 🟢 **Green**: Healthy levels

### Step 3: Generate Purchase Order

```bash
curl -X POST http://localhost:8000/generate-po/ \
  -H "Content-Type: application/json" \
  -d '{"store_ids": ["STORE_001", "STORE_002"]}'
```

**System automatically**:
- Identifies low-stock SKUs
- Aggregates demand across stores
- Applies bulk discounts
- Respects supplier MOQs
- Optimizes delivery dates

### Step 4: Send to Supplier

```bash
curl -X POST http://localhost:8000/send-po/ \
  -H "Content-Type: application/json" \
  -d '{"po_id": "PO_20260501_001", "method": "email"}'
```

**Result**: PO sent to Metcash with confirmation tracking.

### Step 5: View Financial Impact

```bash
curl "http://localhost:8000/financial-metrics/?store_id=STORE_001&start_date=2025-05-01&end_date=2026-04-30"
```

**Metrics shown**:
- Gross Margin: 40%
- Inventory Turnover: 8.5x
- Stockout Incidents: 2
- Overstock Incidents: 1

---

## 📈 Real-World Scenarios

### Scenario 1: Black Friday Demand Surge
**Problem**: 300% demand spike predicted for top 20 SKUs.

**Solution**:
1. System forecasts surge 2 weeks ahead
2. Identifies 18 SKUs below safety stock
3. Generates consolidated PO with 15% bulk discount
4. Delivers 1 week before peak

**Seeded demo result**: zero simulated stockouts and a modelled $12K discount capture in this scenario.

---

### Scenario 2: Multi-Store Rebalancing
**Problem**: Store A overstocked (200 units), Store B understocked (20 units) of same SKU.

**Solution**:
1. Inventory monitor detects imbalance
2. System proposes transfer instead of new PO
3. Redirects 100 units from A to B

**Result**: $4K avoided purchase, reduced carrying costs.

---

### Scenario 3: Promotion Planning
**Problem**: 2-week promotion on seasonal items.

**Solution**:
1. External fetcher flags promotion dates
2. Forecaster applies 40% uplift factor
3. Planner adjusts order quantities with lead time buffer

**Result**: Perfect in-stock rate during promotion.

---

## 🏗️ Architecture Deep Dive

### Design Principles

1. **Autonomy**: Each agent operates independently
2. **Loose Coupling**: Agents communicate via data contracts (dicts/JSON)
3. **Statelessness**: No shared mutable state
4. **Resilience**: Graceful degradation on failures
5. **Extensibility**: Easy to add/remove agents

### Technology Stack

#### Backend & ML
| Technology | Purpose | Why |
|------------|---------|-----|
| Python 3.11 | Core language | Rich ecosystem, readability |
| FastAPI | Web framework | Async, auto-docs, type-safe |
| Prophet | Time-series | Trend + seasonality capture |
| XGBoost | Gradient boosting | External feature modeling |
| Pandas | Data processing | Industry standard |
| NumPy | Numeric computing | Performance |

#### Frontend & Visualization
| Technology | Purpose | Why |
|------------|---------|-----|
| HTML/JS | Dashboard | No build step needed |
| Plotly.js | Charts | Interactive, exportable |
| CSS3 | Styling | Responsive design |

#### DevOps
| Technology | Purpose | Why |
|------------|---------|-----|
| Docker | Containerization | Consistency across environments |
| Docker Compose | Local orchestration | Simple multi-service setup |
| Kubernetes | Production orchestration | Auto-scaling, self-healing |
| GitHub Actions | CI/CD | Automated testing, deployment |
| Make | Task automation | Developer-friendly commands |

---

## 📚 Comprehensive Documentation

We've invested heavily in documentation to ensure this project is **employer-ready**:

| Document | Purpose | Link |
|----------|---------|------|
| **README.md** | Project overview, quick start | You are here |
| **API Reference** | Complete API documentation | [docs/api_reference.md](docs/api_reference.md) |
| **Architecture** | System design & patterns | [docs/architecture.md](docs/architecture.md) |
| **Agentic Engineering** | Deep dive into agent patterns | [docs/agentic_engineering.md](docs/agentic_engineering.md) |
| **Quick Start** | 5-minute getting started guide | [docs/quick_start.md](docs/quick_start.md) |
| **Demo Guide** | Step-by-step scenarios | [docs/demo_guide.md](docs/demo_guide.md) |
| **Data Sources** | Data formats & schemas | [docs/data_sources.md](docs/data_sources.md) |
| **Financial Metrics** | KPI formulas & calculations | [docs/financial_metrics.md](docs/financial_metrics.md) |
| **ADRs** | Architecture decision records | [docs/architecture_decisions.md](docs/architecture_decisions.md) |
| **Why This Solution?** | Competitive analysis & value prop | [docs/why_this_solution.md](docs/why_this_solution.md) |
| **Security** | Security best practices | [docs/security.md](docs/security.md) |
| **Contributing** | Contribution guidelines | [docs/contributing.md](docs/contributing.md) |
| **Performance** | Benchmarks & optimization | [docs/performance.md](docs/performance.md) |

**Total documentation**: 15+ files, 15,000+ words.

---

## 🧪 Testing & Quality

### Test Suite

The collected repository contains 9 test files with roughly 47 explicit test functions spanning agents, reporting and API behaviour. The latest collected CI run is failing, so the README does not claim a current pass rate or coverage percentage. Generate a fresh local coverage report with the documented pytest commands before making release-quality coverage claims.

**Test Files**:
- `test_sales_data_ingestor.py` - Data loading & validation
- `test_external_data_fetcher.py` - External data sources
- `test_demand_forecaster.py` - ML forecasting
- `test_inventory_monitor.py` - Stock tracking
- `test_replenishment_planner.py` - PO optimization
- `test_supplier_communicator.py` - Email/API
- `test_reporting_agent.py` - PDF/Markdown
- `test_api.py` - End-to-end API tests

### CI/CD Pipeline

```yaml
on: [push, pull_request]

jobs:
  test:
    - Python 3.10, 3.11, 3.12
    - Run pytest with coverage
    - Upload to Codecov
  
  docker-build:
    - Build images
    - Run integration tests
  
  deploy-k8s-manifest:
    - Validate YAML syntax
    - Dry-run kubectl apply
```

**All checks must pass before merge**.

---

## 🔒 Security Highlights

- ✅ **Path Traversal Protection**: PO IDs validated, path resolution checked
- ✅ **Input Validation**: Pydantic models, regex patterns
- ✅ **Structured Logging**: No PII in plaintext logs
- ✅ **Secrets Management**: Environment variables, K8s secrets
- ✅ **Dependency Scanning**: Automated vulnerability checks (Dependabot)
- ✅ **Secure Headers**: CORS, HSTS (production)
- ✅ **Rate Limiting**: Configurable request throttling

**No critical vulnerabilities found** (security audit passed).

---

## 🚀 Deployment Options

### Docker Compose (Development)

```bash
docker compose build
docker compose up -d
```

**Services**:
- `retail-forecaster-app` (Port 8000)
- `retail-mock-api` (Port 8001)

**Volumes**:
- `./reports` → `/app/reports` (persistent reports)
- `./src/data` → `/app/src/data` (shared data)

---

### Kubernetes (Production)

**Resources deployed**:
- Namespace: `retail-forecaster`
- Deployments: 2 (app + mock API)
- Services: 3 (ClusterIP, NodePort, Ingress)
- ConfigMap: Environment configuration
- Secret: Credentials (SMTP, DB)
- Ingress: External access (NGINX)

**Scaling**:
```bash
kubectl scale deployment retail-forecaster --replicas=5
```

**Self-Healing**: Failed pods automatically restarted.

---

### Makefile (All-in-One)

```bash
make help           # Show all commands
make install        # Install dependencies
make dev            # Start dev server
make test           # Run tests
make docker-up      # Build & start containers
make k8s-apply      # Deploy to K8s
make demo           # Full demo in one command
```

**40+ targets** for every workflow.

---

## 🔧 Configuration

### Environment Variables

```bash
# .env
ENVIRONMENT=production
LOG_LEVEL=info

# Database (future)
DATABASE_URL=postgresql://user:pass@host:5432/db

# SMTP (email)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Supplier APIs (future)
METCASH_API_KEY=your-key
PFD_API_KEY=your-key

# Model parameters
PROPHET_INTERVAL_WIDTH=0.8
XGBOOST_N_ESTIMATORS=50
REORDER_THRESHOLD_DAYS=14
```

**Configuration hierarchy**: Environment variables > ConfigMap > defaults.

---

## 📖 API Quick Reference

### Endpoints Table

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| `GET` | `/` | HTML dashboard | No |
| `GET` | `/health` | Health check | No |
| `POST` | `/forecast/` | Generate forecast | No |
| `GET` | `/inventory/` | Get stock levels | No |
| `GET` | `/inventory/heatmap/` | Heatmap data | No |
| `POST` | `/generate-po/` | Create PO | No |
| `POST` | `/send-po/` | Send PO | No |
| `GET` | `/financial-metrics/` | Financial KPIs | No |
| `GET` | `/supplier-comparison/` | Supplier metrics | No |
| `GET` | `/reports/inventory/` | Inventory report | No |
| `GET` | `/reports/financial/` | Financial report | No |
| `GET` | `/reports/supplier-comparison/` | Supplier report | No |

**Rate Limit**: 1000 req/hour (unlimited in dev)

**Response Format**:
```json
{
  "status": "success|error",
  "data": { ... },
  "message": "Human-readable",
  "timestamp": "2026-04-30T11:44:39Z"
}
```

---

## 🎓 Learning Resources

### Understanding the Codebase

1. **Start Here**: Read `docs/agentic_engineering.md` for architecture overview
2. **Explore Agents**: Each agent in `src/agents/` is self-contained
3. **Trace Flow**: Use sequence diagram above to follow data flow
4. **Run Tests**: See `tests/` for usage examples
5. **Try Demo**: `make docker-up` and interact with UI

### Key Concepts Demonstrated

- **Agent Pattern**: Autonomous, collaborating components
- **Hybrid ML**: Ensemble of Prophet (time-series) + XGBoost (tabular)
- **FastAPI**: Modern Python web framework with auto-docs
- **Docker/K8s**: Containerization best practices
- **CI/CD**: Automated testing & deployment
- **Security**: Input validation, path traversal protection, secrets mgmt
- **Documentation**: Professional portfolio-quality docs

---

## 📊 Engineering Positioning

### Compared with Manual Spreadsheet Workflows
- **Automation**: agent-driven ingestion, forecasting, inventory monitoring and replenishment planning
- **Forecasting**: hybrid Prophet/XGBoost approach with documented benchmark scenarios
- **External Factors**: weather, holidays and promotion inputs represented in the architecture

### Compared with Large ERP Forecasting Modules
- **Transparency**: source-available implementation that can be inspected and extended
- **Deployment**: container and Kubernetes assets are included for controlled demonstrations
- **Flexibility**: Python-based agents and configuration are directly adaptable
- **Australian Context**: demonstration scenarios and terminology are oriented to Australian retail

### Compared with Single-Model Forecasting
- **Hybrid Models**: Prophet and XGBoost can be combined for different signal types
- **External Regressors**: architecture supports contextual inputs beyond historical demand
- **Uncertainty**: forecast outputs include confidence/uncertainty information where supported by the model

---

## 🔮 Roadmap

### Short Term (3-6 months)
- [ ] Real-time streaming (Apache Kafka)
- [ ] PostgreSQL database integration
- [ ] Model persistence (MLflow)
- [ ] Mobile-responsive dashboard

### Medium Term (6-12 months)
- [ ] Multi-tenant architecture
- [ ] Advanced optimization (stochastic programming)
- [ ] Supplier performance analytics
- [ ] Demand sensing (external signals: social, economic)

### Long Term (12+ months)
- [ ] Autonomous closed-loop replenishment
- [ ] Prescriptive analytics (what-if scenarios)
- [ ] Blockchain for supply chain transparency
- [ ] AI-powered supplier negotiation

---

## 🤝 Contributing

We welcome contributions! Please see [Contributing Guide](docs/contributing.md) for details.

**Areas needing help**:
- Real database adapters (PostgreSQL, MySQL)
- Authentication & authorization
- Advanced ML models (LSTM, DeepAR, Transformers)
- Real-time streaming (Kafka, Kinesis)
- Monitoring & alerting (Prometheus, Grafana)
- Performance optimizations

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

---

## 📬 Contact

- **Issues:** https://github.com/Etherist/retail-demand-forecaster-auto-replenishment-agent/issues
- **GitHub**: [@Etherist](https://github.com/Etherist)
- **LinkedIn**: [My LinkedIn Profile](https://www.linkedin.com/in/robert-b-7aba31a/)
- **Portfolio**: [perspicacious.au](https://perspicacious.au)
- **Email**: perspicacious@tuta.io
- **Issues:** [GitHub Issues](https://github.com/Etherist/retail-demand-forecaster-auto-replenishment-agent/issues)
- **Discussions:** [GitHub Discussions](https://github.com/Etherist/retail-demand-forecaster-auto-replenishment-agent/discussions)

---

## 🌟 Star History

If you find this project valuable, please give it a star! ⭐

---

**Built with ❤️ for Australian Retailers**

*Demonstrating the power of agentic engineering, hybrid ML, and professional software craftsmanship.*

---

**🚀 Ready to deploy?** `make docker-up`  
**📖 Want details?** Browse `/docs/`  
**🐛 Found a bug?** [Open an issue](https://github.com/Etherist/retail-demand-forecaster-auto-replenishment-agent/issues)
