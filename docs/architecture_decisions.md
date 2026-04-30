# Architecture Decision Records

## ADR-001: Multi-Agent Architecture

### Status
✅ Accepted

### Context

We need to build a demand forecasting and inventory optimization system for Australian retailers. The system must handle sales data ingestion, demand forecasting, inventory monitoring, replenishment planning, supplier communication, and reporting.

### Decision

Adopt a **multi-agent architecture** with 7 specialized autonomous agents:

1. **Sales Data Ingestor** - Data acquisition & validation
2. **External Data Fetcher** - Context enrichment (weather, holidays, promotions)
3. **Demand Forecaster** - ML predictions (Prophet + XGBoost)
4. **Multi-Store Inventory Monitor** - Stock tracking & alerts
5. **Replenishment Planner** - PO generation & optimization
6. **Supplier Communicator** - Action execution (email/API)
7. **Reporting & Analytics** - Insight generation (PDFs, dashboards)

### Consequences

**Positive:**
- ✅ **Modularity**: Each agent can be developed, tested, and deployed independently
- ✅ **Maintainability**: Clear separation of concerns; easy to understand and debug
- ✅ **Scalability**: Agents can be scaled horizontally based on load
- ✅ **Resilience**: Failure in one agent doesn't cascade to others
- ✅ **Extensibility**: New agents can be added without modifying existing ones

**Negative:**
- ⚠️ **Complexity**: More moving parts than monolithic architecture
- ⚠️ **Overhead**: Inter-agent communication adds latency
- ⚠️ **Testing**: Integration testing more complex

---

## ADR-002: Hybrid Forecasting Model (Prophet + XGBoost)

### Status
✅ Accepted

### Context

Demand forecasting requires capturing both:
- **Trend & Seasonality**: Weekly, yearly patterns
- **External Factors**: Weather, holidays, promotions

单一模型难以同时满足这些需求。

### Decision

Use **hybrid ensemble** approach:
1. **Prophet** for baseline (trend + seasonality + holidays)
2. **XGBoost** for residuals (weather, promotions, lag features)
3. **Combine**: Final = Prophet + XGBoost residuals

### Consequences

**Positive:**
- ✅ **Accuracy**: Combines strengths of both models
- ✅ **Interpretability**: Prophet component explains trend/seasonality
- ✅ **Flexibility**: XGBoost handles arbitrary external features
- ✅ **Robustness**: Fallback to statistical model if Prophet unavailable

**Negative:**
- ⚠️ **Complexity**: Two models to train and maintain
- ⚠️ **Latency**: Longer training time than single model
- ⚠️ **Caching**: Requires careful feature alignment

---

## ADR-003: Fallback Forecasting Strategy

### Status
✅ Accepted

### Context

Prophet has known installation issues on Python 3.12+ (pystan compilation). We need a strategy to ensure the system works even without Prophet.

### Decision

Implement **graceful degradation**:
1. Try to import Prophet at module load
2. Set `PROPHET_AVAILABLE = False` if import fails
3. Use statistical fallback: historical averages with DoW/holiday/promo adjustments
4. Log warning when fallback is used

### Consequences

**Positive:**
- ✅ **Reliability**: System works regardless of Prophet availability
- ✅ **Portability**: No compilation dependencies
- ✅ **User Experience**: No hard crashes; degraded but functional forecasts

**Negative:**
- ⚠️ **Accuracy**: Fallback less accurate than Prophet
- ⚠️ **Maintenance**: Two code paths to test and maintain

---

## ADR-004: In-Memory Data Processing

### Status
✅ Accepted (Demo)

### Context

For the demo, we need simplicity and fast iteration. A full database setup adds complexity.

### Decision

Use **in-memory Pandas DataFrames** with CSV files as data source:
- Sales data loaded from `sample_sales.csv`
- Metadata from JSON files
- Cached in module-level variables

### Consequences

**Positive:**
- ✅ **Simplicity**: No database setup required
- ✅ **Speed**: Fast data access (no I/O latency)
- ✅ **Portability**: Single file deployment

**Negative:**
- ⚠️ **Scalability**: Limited by available memory
- ⚠️ **Persistence**: Data lost on restart
- ⚠️ **Concurrency**: Not thread-safe without locks

**Future Migration:**
Replace with PostgreSQL + connection pooling when moving to production.

---

## ADR-005: FastAPI for API Layer

### Status
✅ Accepted

### Context

Need to expose forecasting and replenishment functionality via HTTP API. Must support:
- Automatic documentation
- Type validation
- Async operations
- Easy testing

### Decision

Use **FastAPI** over alternatives (Flask, Django REST Framework).

### Consequences

**Positive:**
- ✅ **Auto-docs**: Interactive Swagger UI at `/docs`
- ✅ **Type Safety**: Pydantic models enforce validation
- ✅ **Performance**: Async support, high throughput
- ✅ **Modern**: Active development, large community

**Negative:**
- ⚠️ **Learning Curve**: Team must learn FastAPI conventions
- ⚠️ **Dependencies**: Additional package requirements

---

## ADR-006: Docker-First Deployment

### Status
✅ Accepted

### Context

Need consistent environments across development, testing, and production.

### Decision

**Docker-first** approach:
1. Multi-stage Dockerfile for production images
2. Docker Compose for local orchestration
3. Kubernetes manifests for production deployment
4. Makefile as developer-friendly wrapper

### Consequences

**Positive:**
- ✅ **Consistency**: Same environment everywhere
- ✅ **Isolation**: Dependencies contained
- ✅ **Scalability**: Easy to scale with K8s
- ✅ **Dev Experience**: `make docker-up` gets running instantly

**Negative:**
- ⚠️ **Resource Overhead**: Docker uses more memory
- ⚠️ **Complexity**: Requires Docker knowledge
- ⚠️ **Build Times**: Image builds add time to CI/CD

---

## ADR-007: Mock Supplier APIs

### Status
✅ Accepted

### Context

Real supplier APIs (Metcash, PFD) require credentials, have rate limits, and are complex to integrate during development.

### Decision

Implement **mock supplier API server**:
- Simulates Metcash and PFD endpoints
- Returns realistic responses
- Configurable delay and failure modes
- Runs on port 8001 alongside main app

### Consequences

**Positive:**
- ✅ **Development Speed**: No external dependencies
- ✅ **Testing**: Deterministic, no rate limits
- ✅ **Demo Ready**: Works out of the box
- ✅ **Safety**: No accidental real orders

**Negative:**
- ⚠️ **Production Gap**: Requires replacement with real integrations
- ⚠️ **Accuracy**: Mock data may not match real API behavior

**Future Work:**
Implement adapters for real supplier APIs with feature flags.

---

## ADR-008: Financial Metrics Calculation

### Status
✅ Accepted

### Context

Business stakeholders need to understand the financial impact of the system:
- How much money is saved?
- What's the ROI?
- How does performance change over time?

### Decision

Track and report **5 key financial metrics**:

1. **Gross Margin** = (Revenue - COGS) / Revenue
2. **Inventory Turnover** = COGS / Average Inventory
3. **Stockout Incidents** = Count of days with zero stock
4. **Overstock Incidents** = Count of excess inventory days
5. **Emergency Order Cost** = Premium shipping fees

### Consequences

**Positive:**
- ✅ **Business Value**: Quantifies system benefits
- ✅ **Decision Support**: Informs inventory policies
- ✅ **ROI Justification**: Demonstrates cost savings

**Negative:**
- ⚠️ **Data Requirements**: Needs accurate cost data
- ⚠️ **Complexity**: Requires careful accounting

---

## ADR-009: Security by Default

### Status
✅ Accepted

### Context

Even as a demo, the code should demonstrate security best practices.

### Decision

Implement **defense-in-depth**:
- Path traversal protection on file operations
- Input validation via Pydantic models
- Secrets via environment variables (never hardcoded)
- Structured logging without PII exposure
- SQL injection prevention (parameterized queries when using DB)

### Consequences

**Positive:**
- ✅ **Production-Ready**: Can be deployed securely
- ✅ **Compliance**: GDPR-ready architecture
- ✅ **Best Practices**: Teaches secure coding

**Negative:**
- ⚠️ **Code Complexity**: More validation code
- ⚠️ **Performance**: Minor overhead from checks

---

## ADR-010: Documentation-First Approach

### Status
✅ Accepted

### Context

Employers need to understand the system quickly. Poor documentation reduces perceived value.

### Decision

Comprehensive documentation from day one:
- README with wow-factor overview
- `/docs/` folder with detailed guides
- Inline code docstrings (Google style)
- Architecture diagrams (Mermaid)
- API reference with examples
- Demo guide with real scenarios

### Consequences

**Positive:**
- ✅ **Professionalism**: Shows attention to detail
- ✅ **Onboarding**: New developers ramp up faster
- ✅ **Portfolio Quality**: Impressive GitHub repo
- ✅ **Maintenance**: Easier to update code

**Negative:**
- ⚠️ **Time Investment**: Significant effort to write docs
- ⚠️ **Maintenance Burden**: Docs must be kept in sync with code

---

## Future ADRs (Planned)

- ADR-011: Database Migration (CSV → PostgreSQL)
- ADR-012: Authentication & Authorization (OAuth2/JWT)
- ADR-013: Real-Time Streaming (Kafka/Kinesis)
- ADR-014: Model Versioning (MLflow)
- ADR-015: Multi-Tenant Architecture
- ADR-016: Advanced Optimization (Stochastic Programming)

---

*These ADRs document the key architectural decisions that shape the system. They provide context, rationale, and trade-offs for future reference and team alignment.*