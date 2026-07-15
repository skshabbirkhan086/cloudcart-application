# Monitoring

Install kube-prometheus-stack:

```bash
./monitoring/install.sh
kubectl apply -f k8s/base/monitoring.yaml
```

Get Grafana credentials:

```bash
kubectl -n monitoring get secret kube-prometheus-stack-grafana \
  -o jsonpath='{.data.admin-password}' | base64 -d
```

Get Grafana service:

```bash
kubectl -n monitoring get svc kube-prometheus-stack-grafana
```

Useful PromQL:

```promql
sum(rate(cloudcart_http_requests_total[5m]))
```

```promql
histogram_quantile(
  0.95,
  sum by (le) (rate(cloudcart_http_request_duration_seconds_bucket[5m]))
)
```

```promql
cloudcart_worker_queue_depth
```
