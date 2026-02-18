# Kubernetes Deployment Guide

Complete guide for deploying Skill Seekers to Kubernetes using Helm charts.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Installation Methods](#installation-methods)
- [Configuration](#configuration)
- [Accessing Services](#accessing-services)
- [Scaling](#scaling)
- [Persistence](#persistence)
- [Vector Databases](#vector-databases)
- [Security](#security)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [Production Best Practices](#production-best-practices)

## Prerequisites

### Required

- Kubernetes cluster (1.23+)
- Helm 3.8+
- kubectl configured for your cluster
- 20GB+ available storage (for persistence)

### Recommended

- Ingress controller (nginx, traefik)
- cert-manager (for TLS certificates)
- Prometheus operator (for monitoring)
- Persistent storage provisioner

### Cluster Resource Requirements

**Minimum (Development):**
- 2 CPU cores
- 8GB RAM
- 20GB storage

**Recommended (Production):**
- 8+ CPU cores
- 32GB+ RAM
- 200GB+ storage (persistent volumes)

## Quick Start

### 1. Add Helm Repository (if published)

```bash
# Add Helm repo
helm repo add skill-seekers https://yourusername.github.io/skill-seekers
helm repo update

# Install with default values
helm install my-skill-seekers skill-seekers/skill-seekers \
  --create-namespace \
  --namespace skill-seekers
```

### 2. Install from Local Chart

```bash
# Clone repository
git clone https://github.com/yourusername/skill-seekers.git
cd skill-seekers

# Install chart
helm install my-skill-seekers ./helm/skill-seekers \
  --create-namespace \
  --namespace skill-seekers
```

### 3. Quick Test

```bash
# Port-forward MCP server
kubectl port-forward -n skill-seekers svc/my-skill-seekers-mcp 8765:8765

# Test health endpoint
curl http://localhost:8765/health

# Expected response: {"status": "ok"}
```

## Installation Methods

### Method 1: Minimal Installation (Testing)

Smallest deployment for testing - no persistence, no vector databases.

```bash
helm install my-skill-seekers ./helm/skill-seekers \
  --namespace skill-seekers \
  --create-namespace \
  --set persistence.enabled=false \
  --set vectorDatabases.weaviate.enabled=false \
  --set vectorDatabases.qdrant.enabled=false \
  --set vectorDatabases.chroma.enabled=false \
  --set mcpServer.replicaCount=1 \
  --set mcpServer.autoscaling.enabled=false
```

### Method 2: Development Installation

Moderate resources with persistence for local development.

```bash
helm install my-skill-seekers ./helm/skill-seekers \
  --namespace skill-seekers \
  --create-namespace \
  --set persistence.data.size=5Gi \
  --set persistence.output.size=10Gi \
  --set vectorDatabases.weaviate.persistence.size=20Gi \
  --set mcpServer.replicaCount=1 \
  --set secrets.anthropicApiKey="sk-ant-..."
```

### Method 3: Production Installation

Full production deployment with autoscaling, persistence, and all vector databases.

```bash
helm install my-skill-seekers ./helm/skill-seekers \
  --namespace skill-seekers \
  --create-namespace \
  --values production-values.yaml
```

**production-values.yaml:**
```yaml
global:
  environment: production

mcpServer:
  enabled: true
  replicaCount: 3
  autoscaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 20
    targetCPUUtilizationPercentage: 70
  resources:
    limits:
      cpu: 2000m
      memory: 4Gi
    requests:
      cpu: 500m
      memory: 1Gi

persistence:
  data:
    size: 20Gi
    storageClass: "fast-ssd"
  output:
    size: 50Gi
    storageClass: "fast-ssd"

vectorDatabases:
  weaviate:
    enabled: true
    persistence:
      size: 100Gi
      storageClass: "fast-ssd"
  qdrant:
    enabled: true
    persistence:
      size: 100Gi
      storageClass: "fast-ssd"
  chroma:
    enabled: true
    persistence:
      size: 50Gi
      storageClass: "fast-ssd"

ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
  hosts:
    - host: skill-seekers.example.com
      paths:
        - path: /mcp
          pathType: Prefix
          backend:
            service:
              name: mcp
              port: 8765
  tls:
    - secretName: skill-seekers-tls
      hosts:
        - skill-seekers.example.com

secrets:
  anthropicApiKey: "sk-ant-..."
  googleApiKey: ""
  openaiApiKey: ""
  githubToken: ""
```

### Method 4: Custom Values Installation

```bash
# Create custom values
cat > my-values.yaml <<EOF
mcpServer:
  replicaCount: 2
  resources:
    requests:
      cpu: 1000m
      memory: 2Gi
secrets:
  anthropicApiKey: "sk-ant-..."
EOF

# Install with custom values
helm install my-skill-seekers ./helm/skill-seekers \
  --namespace skill-seekers \
  --create-namespace \
  --values my-values.yaml
```

## Configuration

### API Keys and Secrets

**Option 1: Via Helm values (NOT recommended for production)**
```bash
helm install my-skill-seekers ./helm/skill-seekers \
  --set secrets.anthropicApiKey="sk-ant-..." \
  --set secrets.githubToken="ghp_..."
```

**Option 2: Create Secret first (Recommended)**
```bash
# Create secret
kubectl create secret generic skill-seekers-secrets \
  --from-literal=ANTHROPIC_API_KEY="sk-ant-..." \
  --from-literal=GITHUB_TOKEN="ghp_..." \
  --namespace skill-seekers

# Reference in values
# (Chart already uses the secret name pattern)
helm install my-skill-seekers ./helm/skill-seekers \
  --namespace skill-seekers
```

**Option 3: External Secrets Operator**
```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: skill-seekers-secrets
  namespace: skill-seekers
spec:
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: skill-seekers-secrets
  data:
    - secretKey: ANTHROPIC_API_KEY
      remoteRef:
        key: skill-seekers/anthropic-api-key
```

### Environment Variables

Customize via ConfigMap values:

```yaml
env:
  MCP_TRANSPORT: "http"
  MCP_PORT: "8765"
  PYTHONUNBUFFERED: "1"
  CUSTOM_VAR: "value"
```

### Resource Limits

**Development:**
```yaml
mcpServer:
  resources:
    limits:
      cpu: 1000m
      memory: 2Gi
    requests:
      cpu: 250m
      memory: 512Mi
```

**Production:**
```yaml
mcpServer:
  resources:
    limits:
      cpu: 4000m
      memory: 8Gi
    requests:
      cpu: 1000m
      memory: 2Gi
```

## Accessing Services

### Port Forwarding (Development)

```bash
# MCP Server
kubectl port-forward -n skill-seekers svc/my-skill-seekers-mcp 8765:8765

# Weaviate
kubectl port-forward -n skill-seekers svc/my-skill-seekers-weaviate 8080:8080

# Qdrant
kubectl port-forward -n skill-seekers svc/my-skill-seekers-qdrant 6333:6333

# Chroma
kubectl port-forward -n skill-seekers svc/my-skill-seekers-chroma 8000:8000
```

### Via LoadBalancer

```yaml
mcpServer:
  service:
    type: LoadBalancer
```

Get external IP:
```bash
kubectl get svc -n skill-seekers my-skill-seekers-mcp
```

### Via Ingress (Production)

```yaml
ingress:
  enabled: true
  className: nginx
  hosts:
    - host: skill-seekers.example.com
      paths:
        - path: /mcp
          pathType: Prefix
          backend:
            service:
              name: mcp
              port: 8765
```

Access at: `https://skill-seekers.example.com/mcp`

## Scaling

### Manual Scaling

```bash
# Scale MCP server
kubectl scale deployment -n skill-seekers my-skill-seekers-mcp --replicas=5

# Scale Weaviate
kubectl scale deployment -n skill-seekers my-skill-seekers-weaviate --replicas=3
```

### Horizontal Pod Autoscaler

Enabled by default for MCP server:

```yaml
mcpServer:
  autoscaling:
    enabled: true
    minReplicas: 2
    maxReplicas: 10
    targetCPUUtilizationPercentage: 70
    targetMemoryUtilizationPercentage: 80
```

Monitor HPA:
```bash
kubectl get hpa -n skill-seekers
kubectl describe hpa -n skill-seekers my-skill-seekers-mcp
```

### Vertical Scaling

Update resource requests/limits:
```bash
helm upgrade my-skill-seekers ./helm/skill-seekers \
  --namespace skill-seekers \
  --set mcpServer.resources.requests.cpu=2000m \
  --set mcpServer.resources.requests.memory=4Gi \
  --reuse-values
```

## Persistence

### Storage Classes

Specify storage class for different workloads:

```yaml
persistence:
  data:
    storageClass: "fast-ssd"  # Frequently accessed
  output:
    storageClass: "standard"  # Archive storage
  configs:
    storageClass: "fast-ssd"  # Configuration files
```

### PVC Management

```bash
# List PVCs
kubectl get pvc -n skill-seekers

# Expand PVC (if storage class supports it)
kubectl patch pvc my-skill-seekers-data \
  -n skill-seekers \
  -p '{"spec":{"resources":{"requests":{"storage":"50Gi"}}}}'

# View PVC details
kubectl describe pvc -n skill-seekers my-skill-seekers-data
```

### Backup and Restore

**Backup:**
```bash
# Using Velero
velero backup create skill-seekers-backup \
  --include-namespaces skill-seekers

# Manual backup (example with data PVC)
kubectl exec -n skill-seekers deployment/my-skill-seekers-mcp -- \
  tar czf - /data | \
  cat > skill-seekers-data-backup.tar.gz
```

**Restore:**
```bash
# Using Velero
velero restore create --from-backup skill-seekers-backup

# Manual restore
kubectl exec -i -n skill-seekers deployment/my-skill-seekers-mcp -- \
  tar xzf - -C /data < skill-seekers-data-backup.tar.gz
```

## Vector Databases

### Weaviate

**Access:**
```bash
kubectl port-forward -n skill-seekers svc/my-skill-seekers-weaviate 8080:8080
```

**Query:**
```bash
curl http://localhost:8080/v1/schema
```

### Qdrant

**Access:**
```bash
# HTTP API
kubectl port-forward -n skill-seekers svc/my-skill-seekers-qdrant 6333:6333

# gRPC
kubectl port-forward -n skill-seekers svc/my-skill-seekers-qdrant 6334:6334
```

**Query:**
```bash
curl http://localhost:6333/collections
```

### Chroma

**Access:**
```bash
kubectl port-forward -n skill-seekers svc/my-skill-seekers-chroma 8000:8000
```

**Query:**
```bash
curl http://localhost:8000/api/v1/collections
```

### Disable Vector Databases

To disable individual vector databases:

```yaml
vectorDatabases:
  weaviate:
    enabled: false
  qdrant:
    enabled: false
  chroma:
    enabled: false
```

## Security

### Pod Security Context

Runs as non-root user (UID 1000):

```yaml
podSecurityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 1000

securityContext:
  capabilities:
    drop:
      - ALL
  readOnlyRootFilesystem: false
  allowPrivilegeEscalation: false
```

### Network Policies

Create network policies for isolation:

```yaml
networkPolicy:
  enabled: true
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
      - namespaceSelector:
          matchLabels:
            name: ingress-nginx
  egress:
    - to:
      - namespaceSelector: {}
```

### RBAC

Enable RBAC with minimal permissions:

```yaml
rbac:
  create: true
  rules:
    - apiGroups: [""]
      resources: ["configmaps", "secrets"]
      verbs: ["get", "list"]
```

### Secrets Management

**Best Practices:**
1. Never commit secrets to git
2. Use external secret managers (AWS Secrets Manager, HashiCorp Vault)
3. Enable encryption at rest in Kubernetes
4. Rotate secrets regularly

**Example with Sealed Secrets:**
```bash
# Create sealed secret
kubectl create secret generic skill-seekers-secrets \
  --from-literal=ANTHROPIC_API_KEY="sk-ant-..." \
  --dry-run=client -o yaml | \
  kubeseal -o yaml > sealed-secret.yaml

# Apply sealed secret
kubectl apply -f sealed-secret.yaml -n skill-seekers
```

## Monitoring

### Pod Metrics

```bash
# View pod status
kubectl get pods -n skill-seekers

# View pod metrics (requires metrics-server)
kubectl top pods -n skill-seekers

# View pod logs
kubectl logs -n skill-seekers -l app.kubernetes.io/component=mcp-server --tail=100 -f
```

### Prometheus Integration

Enable ServiceMonitor (requires Prometheus Operator):

```yaml
serviceMonitor:
  enabled: true
  interval: 30s
  scrapeTimeout: 10s
  labels:
    prometheus: kube-prometheus
```

### Grafana Dashboards

Import dashboard JSON from `helm/skill-seekers/dashboards/`.

### Health Checks

MCP server has built-in health checks:

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8765
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health
    port: 8765
  initialDelaySeconds: 10
  periodSeconds: 5
```

Test manually:
```bash
kubectl exec -n skill-seekers deployment/my-skill-seekers-mcp -- \
  curl http://localhost:8765/health
```

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl get pods -n skill-seekers

# View events
kubectl get events -n skill-seekers --sort-by='.lastTimestamp'

# Describe pod
kubectl describe pod -n skill-seekers <pod-name>

# Check logs
kubectl logs -n skill-seekers <pod-name>
```

### Common Issues

**Issue: ImagePullBackOff**
```bash
# Check image pull secrets
kubectl get secrets -n skill-seekers

# Verify image exists
docker pull <image-name>
```

**Issue: CrashLoopBackOff**
```bash
# View recent logs
kubectl logs -n skill-seekers <pod-name> --previous

# Check environment variables
kubectl exec -n skill-seekers <pod-name> -- env
```

**Issue: PVC Pending**
```bash
# Check storage class
kubectl get storageclass

# View PVC events
kubectl describe pvc -n skill-seekers <pvc-name>

# Check if provisioner is running
kubectl get pods -n kube-system | grep provisioner
```

**Issue: API Key Not Working**
```bash
# Verify secret exists
kubectl get secret -n skill-seekers my-skill-seekers

# Check secret contents (base64 encoded)
kubectl get secret -n skill-seekers my-skill-seekers -o yaml

# Test API key manually
kubectl exec -n skill-seekers deployment/my-skill-seekers-mcp -- \
  env | grep ANTHROPIC
```

### Debug Container

Run debug container in same namespace:

```bash
kubectl run debug -n skill-seekers --rm -it \
  --image=nicolaka/netshoot \
  --restart=Never -- bash

# Inside debug container:
# Test MCP server connectivity
curl http://my-skill-seekers-mcp:8765/health

# Test vector database connectivity
curl http://my-skill-seekers-weaviate:8080/v1/.well-known/ready
```

## Production Best Practices

### 1. Resource Planning

**Capacity Planning:**
- MCP Server: 500m CPU + 1Gi RAM per 10 concurrent requests
- Vector DBs: 2GB RAM + 10GB storage per 100K documents
- Reserve 30% overhead for spikes

**Example Production Setup:**
```yaml
mcpServer:
  replicaCount: 5  # Handle 50 concurrent requests
  resources:
    requests:
      cpu: 2500m
      memory: 5Gi
  autoscaling:
    minReplicas: 5
    maxReplicas: 20
```

### 2. High Availability

**Anti-Affinity Rules:**
```yaml
mcpServer:
  affinity:
    podAntiAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchExpressions:
          - key: app.kubernetes.io/component
            operator: In
            values:
            - mcp-server
        topologyKey: kubernetes.io/hostname
```

**Multiple Replicas:**
- MCP Server: 3+ replicas across different nodes
- Vector DBs: 2+ replicas with replication

### 3. Monitoring and Alerting

**Key Metrics to Monitor:**
- Pod restart count (> 5 per hour = critical)
- Memory usage (> 90% = warning)
- CPU throttling (> 50% = investigate)
- Request latency (p95 > 1s = warning)
- Error rate (> 1% = critical)

**Prometheus Alerts:**
```yaml
- alert: HighPodRestarts
  expr: rate(kube_pod_container_status_restarts_total{namespace="skill-seekers"}[15m]) > 0.1
  for: 5m
  labels:
    severity: warning
```

### 4. Backup Strategy

**Automated Backups:**
```yaml
# CronJob for daily backups
apiVersion: batch/v1
kind: CronJob
metadata:
  name: skill-seekers-backup
spec:
  schedule: "0 2 * * *"  # 2 AM daily
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: skill-seekers:latest
            command:
            - /bin/sh
            - -c
            - tar czf /backup/data-$(date +%Y%m%d).tar.gz /data
```

### 5. Security Hardening

**Security Checklist:**
- [ ] Enable Pod Security Standards
- [ ] Use Network Policies
- [ ] Enable RBAC with least privilege
- [ ] Rotate secrets every 90 days
- [ ] Scan images for vulnerabilities
- [ ] Enable audit logging
- [ ] Use private container registry
- [ ] Enable encryption at rest

### 6. Cost Optimization

**Strategies:**
- Use spot/preemptible instances for non-critical workloads
- Enable cluster autoscaler
- Right-size resource requests
- Use storage tiering (hot/warm/cold)
- Schedule downscaling during off-hours

**Example Cost Optimization:**
```yaml
# Development environment: downscale at night
# Create CronJob to scale down replicas
apiVersion: batch/v1
kind: CronJob
metadata:
  name: downscale-dev
spec:
  schedule: "0 20 * * *"  # 8 PM
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: scaler
          containers:
          - name: kubectl
            image: bitnami/kubectl
            command:
            - kubectl
            - scale
            - deployment
            - my-skill-seekers-mcp
            - --replicas=1
```

### 7. Update Strategy

**Rolling Updates:**
```yaml
mcpServer:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
```

**Update Process:**
```bash
# 1. Test in staging
helm upgrade my-skill-seekers ./helm/skill-seekers \
  --namespace skill-seekers-staging \
  --values staging-values.yaml

# 2. Run smoke tests
./scripts/smoke-test.sh

# 3. Deploy to production
helm upgrade my-skill-seekers ./helm/skill-seekers \
  --namespace skill-seekers \
  --values production-values.yaml

# 4. Monitor for 15 minutes
kubectl rollout status deployment -n skill-seekers my-skill-seekers-mcp

# 5. Rollback if issues
helm rollback my-skill-seekers -n skill-seekers
```

## Upgrade Guide

### Minor Version Upgrade

```bash
# Fetch latest chart
helm repo update

# Upgrade with existing values
helm upgrade my-skill-seekers skill-seekers/skill-seekers \
  --namespace skill-seekers \
  --reuse-values
```

### Major Version Upgrade

```bash
# Backup current values
helm get values my-skill-seekers -n skill-seekers > backup-values.yaml

# Review CHANGELOG for breaking changes
curl https://raw.githubusercontent.com/yourusername/skill-seekers/main/CHANGELOG.md

# Upgrade with migration steps
helm upgrade my-skill-seekers skill-seekers/skill-seekers \
  --namespace skill-seekers \
  --values backup-values.yaml \
  --force  # Only if schema changed
```

## Uninstallation

### Full Cleanup

```bash
# Delete Helm release
helm uninstall my-skill-seekers -n skill-seekers

# Delete PVCs (if you want to remove data)
kubectl delete pvc -n skill-seekers --all

# Delete namespace
kubectl delete namespace skill-seekers
```

### Keep Data

```bash
# Delete release but keep PVCs
helm uninstall my-skill-seekers -n skill-seekers

# PVCs remain for later use
kubectl get pvc -n skill-seekers
```

## Additional Resources

- [Helm Documentation](https://helm.sh/docs/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Skill Seekers GitHub](https://github.com/yourusername/skill-seekers)
- [Issue Tracker](https://github.com/yourusername/skill-seekers/issues)

---

**Need Help?**
- GitHub Issues: https://github.com/yourusername/skill-seekers/issues
- Documentation: https://skillseekersweb.com
- Community: [Link to Discord/Slack]
