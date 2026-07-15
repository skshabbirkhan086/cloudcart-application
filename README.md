# CloudCart Order Management Platform

A production-style DevOps portfolio application containing:

- FastAPI backend
- PostgreSQL database
- Redis-backed background worker
- Nginx frontend
- Docker Compose local environment
- Kubernetes manifests
- AWS ALB Ingress
- GitHub Actions CI/CD with OIDC
- Gitleaks, Bandit, pip-audit, Hadolint, Checkov and Trivy
- Prometheus ServiceMonitor and alert rules
- Grafana dashboard

## Local run

```bash
cp .env.example .env
docker compose up --build
```

Open:

- Application: http://localhost:8080
- API documentation: http://localhost:8000/docs
- Backend metrics: http://localhost:8000/metrics
- Worker metrics: http://localhost:9101/metrics

## Kubernetes deployment

Replace image placeholders in `k8s/base/*.yaml`, or use the GitHub Actions
deployment workflow.

```bash
kubectl apply -k k8s/overlays/dev
kubectl -n cloudcart-dev get pods,svc,ingress
```

The ALB address appears under:

```bash
kubectl -n cloudcart-dev get ingress cloudcart
```

## GitHub repository configuration

Repository variables:

- `AWS_REGION`
- `AWS_ROLE_ARN`
- `ECR_REGISTRY`
- `EKS_CLUSTER_NAME`

Repository secrets:

- `POSTGRES_PASSWORD`

Create GitHub Environments:

- `dev`
- `production`

Apply required reviewers to `production`.
