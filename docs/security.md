# Security Best Practices

## Overview

This document outlines security measures implemented in the Retail Demand Forecaster & Auto-Replenishment Agent system. While the demo uses mock data and simplified configurations, the code follows security best practices suitable for production deployment.

---

## Threat Model

### Assets to Protect
- **Sales Data**: Business-sensitive information
- **Supplier Credentials**: SMTP passwords, API keys
- **Purchase Orders**: Financial transactions
- **Customer Data** (future): PII (when integrated with real systems)

### Potential Threats
- **Unauthorized Access**: API abuse, credential theft
- **Data Breach**: Exposure of sensitive files
- **Injection Attacks**: Path traversal, command injection
- **Denial of Service**: Resource exhaustion
- **Man-in-the-Middle**: Network interception

---

## Security Controls

### 1. Authentication & Authorization

#### Current State (Demo)
- No authentication required for API access
- All endpoints publicly accessible

#### Production Recommendations
```python
# Add OAuth2 with JWT tokens
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Verify credentials
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}
```

**Implementation Priority**: HIGH

---

### 2. Input Validation

#### Implemented
- **Pydantic Models**: All API requests validated
- **Type Checks**: Python type hints enforced
- **Range Checks**: Numeric parameters validated
- **Regex Patterns**: SKU/store ID formats validated

**Example**:
```python
from pydantic import BaseModel, Field, validator
import re

class ForecastRequest(BaseModel):
    sku_id: str = Field(..., pattern=r'^[A-Z0-9_-]+$', max_length=50)
    store_id: str = Field(..., pattern=r'^[A-Z0-9_-]+$', max_length=50)
    horizon_days: int = Field(7, ge=1, le=90)
```

---

### 3. Path Traversal Protection

#### Implemented
- **Filename Validation**: Regex patterns for PO IDs
- **Path Resolution**: Ensures file operations stay within designated directories

**Example**:
```python
def _safe_po_path(po_id: str) -> Path:
    if not _validate_po_id(po_id):
        raise ValueError(f"Invalid PO ID format: {po_id}")
    
    po_file = (POS_DIR / po_id).with_suffix('.json')
    
    # Ensure within POS_DIR
    try:
        po_file.resolve().relative_to(POS_DIR.resolve())
    except ValueError:
        raise ValueError(f"Path traversal attempt: {po_id}")
    
    return po_file
```

---

### 4. Secrets Management

#### Current State
- SMTP credentials via environment variables
- Kubernetes secrets for deployment

**Example**:
```bash
# .env file (never committed)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=forecaster@retail.com
SMTP_PASSWORD=super-secret-password
```

#### Production Recommendations
Use **secrets manager**:
- **AWS**: Secrets Manager or Parameter Store
- **GCP**: Secret Manager
- **Azure**: Key Vault
- **Kubernetes**: Sealed Secrets or external-secrets

```python
import boto3
from botocore.exceptions import ClientError

def get_secret(secret_name: str) -> str:
    client = boto3.client('secretsmanager')
    try:
        response = client.get_secret_value(SecretId=secret_name)
        return response['SecretString']
    except ClientError as e:
        logger.error(f"Failed to retrieve secret: {e}")
        raise
```

---

### 5. Logging & Monitoring

#### Implemented
- **Structured Logging**: JSON-formatted logs with context
- **No PII**: Sensitive data filtered from logs
- **Log Levels**: DEBUG, INFO, WARNING, ERROR

**Example**:
```python
logger.info(
    "PO sent via email",
    extra={
        "po_id": po["po_id"],
        "supplier": po["supplier"],
        "sensitive": False,  # Flag for log filtering
    },
)
```

#### Production Recommendations
- Centralized logging (ELK stack, Splunk, Datadog)
- Alerting on suspicious patterns (failed auth, unusual volumes)
- Audit trails for all PO generation/sending
- Correlation IDs for request tracing

---

### 6. Network Security

#### Recommended Configuration

**Docker Network**:
```yaml
# docker-compose.yml
networks:
  retail_network:
    driver: bridge
    internal: true  # No external internet access
    attachable: false
```

**Kubernetes Network Policies**:
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-api
spec:
  podSelector:
    matchLabels:
      app: retail-forecaster
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: nginx-ingress
    ports:
    - protocol: TCP
      port: 8000
```

**API Gateway** (Recommended):
- **API Gateway**: Kong, Apigee, or AWS API Gateway
- **Rate Limiting**: 1000 req/hour per key
- **IP Whitelisting**: Allow only known IP ranges
- **WAF**: Web Application Firewall for SQLi/XSS protection

---

### 7. Data Protection

#### Data at Rest
- **Encryption**: Full-disk encryption on servers
- **Database**: Encrypted storage (TDE for PostgreSQL)
- **Backups**: Encrypted backups with rotation

#### Data in Transit
- **TLS 1.3**: All API communications over HTTPS
- **Certificate Management**: Automated renewal (Let's Encrypt)
- **HSTS**: Strict Transport Security headers

```python
# FastAPI HTTPS configuration
app = FastAPI(
    title="Retail Forecaster",
    # Enforce HTTPS in production
    root_path="/api/v1",
    # Add security headers middleware
)
```

---

### 8. SQL Injection Prevention

#### Current State
- No SQL database (Pandas only)
- No SQL injection risk

#### Future (PostgreSQL)
```python
# ✅ Use parameterized queries
cursor.execute(
    "SELECT * FROM sales WHERE sku_id = %s AND date >= %s",
    (sku_id, start_date)
)

# ❌ Never do this
cursor.execute(f"SELECT * FROM sales WHERE sku_id = '{sku_id}'")
```

---

### 9. Cross-Site Scripting (XSS) Prevention

#### Frontend
```javascript
// Escape user input before rendering
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Use innerText instead of innerHTML where possible
element.innerText = userInput;  // Safe
element.innerHTML = userInput;  // Dangerous!
```

#### API
- Content-Type: application/json (not HTML)
- CORS restrictions:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

---

### 10. Rate Limiting

#### Implementation
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/forecast/")
@limiter.limit("10/minute")
async def forecast(request: ForecastRequest):
    # ...
```

**Recommended Limits**:
- Anonymous: 10 req/min
- Authenticated: 100 req/min
- Bulk operations: 5 req/min

---

### 11. Dependency Security

#### Current Dependencies
Check for vulnerabilities:
```bash
# Audit dependencies
pip install safety
safety check --json

# Or use GitHub Dependabot
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
```

#### Recommendations
- **Pin versions**: `requirements.txt` with exact versions
- **Regular updates**: Weekly dependency reviews
- **Vulnerability scanning**: Integrate into CI/CD
- **Minimize dependencies**: Remove unused packages

---

### 12. Input Sanitization

#### File Uploads (Future)
If adding file uploads:
```python
from pathlib import Path
import magic  # File type detection

ALLOWED_EXTENSIONS = {'.csv', '.json'}
ALLOWED_MIME_TYPES = {'text/csv', 'application/json'}

def validate_upload(file_content: bytes, filename: str) -> bool:
    # Check extension
    if Path(filename).suffix not in ALLOWED_EXTENSIONS:
        return False
    
    # Check MIME type
    mime = magic.from_buffer(file_content, mime=True)
    if mime not in ALLOWED_MIME_TYPES:
        return False
    
    # Check for malicious content (e.g., script tags in CSV)
    if b'<script>' in file_content:
        return False
    
    return True
```

---

### 13. Session Management

#### Current State
- Stateless API (no sessions)

#### If Adding Web UI Sessions
```python
from fastapi import Request
from starlette.middleware.sessions import SessionMiddleware

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET"),
    session_cookie="secure",
    max_age=3600,  # 1 hour
    same_site="lax",
    https_only=True,
)
```

**Best Practices**:
- Use secure, random session IDs
- Set `HttpOnly`, `Secure`, `SameSite` flags
- Implement session expiration
- Rotate secrets regularly

---

### 14. CSRF Protection

#### Current State
- API only (no vulnerable browser sessions)

#### If Adding Browser Forms
```python
from fastapi import Form
from starlette_wtf import CSRFProtectMiddleware

# CSRF token in forms
@app.post("/submit")
async def submit(form: MyForm = Depends()):
    # CSRF validated automatically
    pass
```

---

### 15. Error Handling & Information Disclosure

#### Implemented
- Generic error messages for users
- Detailed errors logged server-side
- No stack traces in API responses

**Example**:
```python
@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    logger.error(f"Internal error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
```

#### Recommendations
- Never expose system details in errors
- Log full tracebacks with request IDs
- Monitor error patterns for attacks

---

## Security Checklist for Production

### Pre-Deployment

- [ ] Enable HTTPS with valid TLS certificate
- [ ] Configure authentication (OAuth2/JWT)
- [ ] Set up secrets manager (not env vars)
- [ ] Implement rate limiting
- [ ] Configure firewall rules (allow only 80/443)
- [ ] Enable audit logging
- [ ] Set up intrusion detection
- [ ] Run security scan (`safety check`, `bandit`)
- [ ] Perform penetration testing
- [ ] Document incident response plan

### Runtime Monitoring

- [ ] Monitor failed authentication attempts
- [ ] Alert on unusual traffic patterns
- [ ] Review logs weekly for anomalies
- [ ] Rotate credentials every 90 days
- [ ] Keep dependencies updated
- [ ] Backup data encrypted, tested restores
- [ ] Document security incidents

### Compliance (If Handling PII)

- [ ] GDPR: Data minimization, consent records, right to deletion
- [ ] Privacy Policy: Clear data usage description
- [ ] Data Retention: Automated purging
- [ ] Data Breach Notification: Process in place
- [ ] Vendor Assessments: Third-party security reviews

---

## Incident Response

### Security Incident Types

1. **Unauthorized Access**: Compromised credentials detected
2. **Data Exfiltration**: Unusual data download volumes
3. **Service Disruption**: DoS/DDoS attack
4. **Malware**: Suspicious file uploads or code execution

### Response Playbook

**Step 1: Contain**
- Isolate affected systems
- Disable compromised accounts
- Preserve evidence (logs, memory dumps)

**Step 2: Assess**
- Determine scope and impact
- Identify attack vector
- Classify severity (Critical/High/Medium/Low)

**Step 3: Eradicate**
- Remove malware/backdoors
- Patch vulnerabilities
- Rotate all credentials

**Step 4: Recover**
- Restore from clean backups
- Monitor for recurrence
- Resume normal operations

**Step 5: Lessons Learned**
- Document incident
- Update security controls
- Team training

---

## Security Contacts

- **Security Issues**: security@retail-forecaster.com (private)
- **Vulnerability Disclosure**: Responsible disclosure policy
- **Security Team**: [Contact info]

---

*This document is living. Update as security practices evolve.*

**Last Updated**: 2026-04-30  
**Next Review**: 2026-07-30