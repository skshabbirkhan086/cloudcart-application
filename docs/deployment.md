# Deployment Checklist

1. Install AWS Load Balancer Controller.
2. Install metrics-server for HPA.
3. Install kube-prometheus-stack before applying ServiceMonitor resources.
4. Create ECR repositories:
   - cloudcart-backend
   - cloudcart-worker
   - cloudcart-frontend
5. Configure the GitHub OIDC deployment role.
6. Configure repository variables and the database password secret.
7. Run the CD workflow.
8. Open the URL printed in the GitHub job summary.
