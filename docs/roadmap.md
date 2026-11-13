# Roadmap ideas

Already shipped in 0.1.x:

- control plane core
- alerts / secrets / DLQ / metrics / logs
- CLI + SDK + recipes
- export/import, quotas, live WS
- multi-user RBAC (roles owner/admin/operator/viewer), invites, register

Next candidates:

1. Persistent Redis streams as optional queue backend
2. S3/MinIO artifact store for job outputs
3. OIDC login
4. Per-app autoscaling suggestions from metrics
5. Helm chart
6. Mobile-friendly compact dashboard mode
7. Signed worker attestation
8. Email delivery for invites + ownership transfer UI
