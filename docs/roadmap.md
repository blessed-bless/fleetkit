# Roadmap ideas

Already shipped in 0.1.x:

- control plane core
- alerts / secrets / DLQ / metrics / logs
- CLI + SDK + recipes
- export/import, quotas, live WS

Next candidates:

1. Multi-user RBAC enforcement on every route (models already exist)
2. Persistent Redis streams as optional queue backend
3. S3/MinIO artifact store for job outputs
4. OIDC login
5. Per-app autoscaling suggestions from metrics
6. Helm chart
7. Mobile-friendly compact dashboard mode
8. Signed worker attestation
