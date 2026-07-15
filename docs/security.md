# Security Controls

- GitHub OIDC instead of long-lived AWS keys
- Read-only default workflow token permissions
- Immutable Git SHA image tags
- Gitleaks secret scanning
- Bandit Python SAST
- pip-audit dependency scanning
- Hadolint Dockerfile linting
- Checkov Kubernetes scanning
- Trivy container scanning
- Non-root containers
- Dropped Linux capabilities
- RuntimeDefault seccomp
- Resource requests and limits
- Startup, readiness and liveness probes
- Kubernetes NetworkPolicy
- GitHub Environment approvals for production

For production, replace the in-cluster PostgreSQL and Redis workloads with RDS
and ElastiCache, and use External Secrets with AWS Secrets Manager.
