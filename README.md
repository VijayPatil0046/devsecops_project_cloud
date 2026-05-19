# Green Cloud Cost Optimization — DevSecOps Project

A full-stack, ML-powered FinOps platform that analyses VM workloads and recommends
cost and carbon-reduction actions across cloud regions.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                     Client Browser                      │
│          React + TanStack Router (Vite / Nginx)         │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP / REST
┌────────────────────────▼────────────────────────────────┐
│                 FastAPI Backend (Python)                 │
│  • JWT authentication    • Isolation Forest ML model    │
│  • Electricity Maps API  • Prometheus /metrics          │
└──────────┬──────────────────────────┬───────────────────┘
           │                          │ scrape
  ┌────────▼────────┐       ┌─────────▼──────────┐
  │  HashiCorp Vault│       │     Prometheus      │
  │  (secrets KV)   │       │  + recording rules  │
  └─────────────────┘       └─────────┬───────────┘
                                      │
                            ┌─────────▼───────────┐
                            │       Grafana        │
                            │  dashboards + alerts │
                            └─────────────────────┘
```

**Deployment targets:** Docker Compose (local) · Kubernetes (production)

---

## Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.11+ |
| Node.js | 20+ |
| Docker + Docker Compose | v2+ |
| kubectl | 1.28+ (for K8s deploy) |

---

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/VijayPatil0046/devsecops_project_cloud.git
cd devsecops_project_cloud
```

### 2. Configure environment variables

```bash
cp .env.example .env
# Edit .env and fill in the required values (see .env.example for descriptions).
```

### 3. Train the ML model (first time only)

```bash
pip install -r requirements.txt
python main.py          # produces model.pkl and scaler.pkl
```

### 4. Start the full stack

```bash
docker compose up -d
```

| Service | URL |
|---------|-----|
| Backend API | http://localhost:8000 |
| Frontend | http://localhost:5173 |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 |
| Vault (optional) | http://localhost:8200 |

Start Vault alongside the stack:

```bash
docker compose --profile vault up -d
```

---

## Required Environment Variables

See [`.env.example`](.env.example) for the full list with descriptions.

| Variable | Required | Description |
|----------|----------|-------------|
| `JWT_SECRET` | ✅ | Secret used to sign JWT tokens |
| `ELECTRICITY_MAPS_API_KEY` | ✅ | API key for live carbon intensity data |
| `ADMIN_USERNAME` | optional | Admin username (default: `admin`) |
| `ADMIN_PASSWORD` | optional | Admin password (default: `admin123`) |
| `ALLOWED_ORIGINS` | optional | Comma-separated CORS origins (default: `*`) |
| `GRAFANA_ADMIN_PASSWORD` | optional | Grafana admin password (default: `admin123`) |
| `ENABLE_VAULT_BOOTSTRAP` | optional | Load secrets from Vault at startup (`true`/`false`) |

---

## Running Tests

### Backend

```bash
# Install test dependencies
pip install -r requirements.txt pytest pytest-cov

# Run tests
pytest -q tests/test_api.py --cov=. --cov-report=term-missing
```

### Frontend

```bash
cd frontend/green-cloud-guardian
npm install
npm test
```

---

## API Reference

### POST `/login`
Returns a short-lived JWT Bearer token.

```json
{ "username": "admin", "password": "admin123" }
```

### POST `/predict`
Accepts a CSV file with `vcpu_usage` and `ram_usage` columns and returns
ML anomaly scores, carbon recommendations, and cost-saving estimates.

Requires `Authorization: Bearer <token>` header.

```
server_id,vcpu_usage,ram_usage
vm-001,12,24
vm-002,88,58
```

### GET `/healthz`
Returns `{ "status": "ok" }` — used by K8s liveness/readiness probes.

### GET `/metrics`
Prometheus metrics endpoint (scraped automatically).

---

## Kubernetes Deployment

```bash
# Apply all manifests (replace placeholder secrets first — see k8s/secret.yaml)
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/prometheus-deployment.yaml
kubectl apply -f k8s/hpa.yaml
kubectl apply -f k8s/network-policy.yaml
```

> ⚠️ **Never apply `k8s/secret.yaml` as-is.** Replace the placeholder values
> with real base64-encoded secrets before running `kubectl apply`.
> See `k8s/secret.yaml` for instructions.

---

## CI/CD Pipeline

The pipeline (`.github/workflows/ci-cd.yml`) runs on every push to `main` or `feat`:

1. **Backend Lint** — flake8
2. **Backend Test** — pytest + coverage + pip-audit CVE scan
3. **Frontend Check** — ESLint + Vitest + npm audit + Vite build
4. **SonarCloud Scan** — static analysis (requires `SONAR_TOKEN` secret)
5. **Build** — Docker images built + Trivy vulnerability scan
6. **Push** — Images pushed to Docker Hub (push events only)
7. **Deploy + Newman** — Integration tests against live stack (push events only)

All GitHub Actions are pinned to commit SHAs to prevent supply-chain attacks.

---

## Project Structure

```
.
├── api.py                    # FastAPI application
├── model.py                  # IsolationForest pipeline
├── feature_engineering.py    # Carbon enrichment + decision engine
├── vault_bootstrap.py        # Vault secret loader
├── requirements.txt
├── Dockerfile.backend
├── docker-compose.yml
├── prometheus.yml            # Prometheus config (docker-compose)
├── recording_rules.yml       # Prometheus recording rules
├── postman_collection.json
├── sonar-project.properties
├── frontend/
│   └── green-cloud-guardian/ # React + TanStack Start SPA
├── grafana/
│   └── provisioning/         # Datasources, dashboards, alert rules
├── k8s/                      # Kubernetes manifests
└── tests/                    # pytest backend tests
```
