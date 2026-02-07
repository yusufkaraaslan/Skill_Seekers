# Kubernetes Deployment Guide

Complete guide for deploying Skill Seekers on Kubernetes.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start with Helm](#quick-start-with-helm)
- [Manual Deployment](#manual-deployment)
- [Configuration](#configuration)
- [Scaling](#scaling)
- [High Availability](#high-availability)
- [Monitoring](#monitoring)
- [Ingress & Load Balancing](#ingress--load-balancing)
- [Storage](#storage)
- [Security](#security)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### 1. Kubernetes Cluster

**Minimum requirements:**
- Kubernetes v1.21+
- kubectl configured
- 2 nodes (minimum)
- 4 CPU cores total
- 8 GB RAM total

**Cloud providers:**
- **AWS:** EKS (Elastic Kubernetes Service)
- **GCP:** GKE (Google Kubernetes Engine)
- **Azure:** AKS (Azure Kubernetes Service)
- **Local:** Minikube, kind, k3s

### 2. Required Tools

```bash
# kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Helm 3
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Verify installations
kubectl version --client
helm version
```

### 3. Cluster Access

```bash
# Verify cluster connection
kubectl cluster-info
kubectl get nodes

# Create namespace
kubectl create namespace skillseekers
kubectl config set-context --current --namespace=skillseekers
```

## Quick Start with Helm

### 1. Install with Default Values

```bash
# Add Helm repository (when available)
helm repo add skillseekers https://charts.skillseekers.io
helm repo update

# Install release
helm install skillseekers skillseekers/skillseekers \
  --namespace skillseekers \
  --create-namespace

# Or install from local chart
helm install skillseekers ./helm/skillseekers \
  --namespace skillseekers \
  --create-namespace
```

### 2. Install with Custom Values

```bash
# Create values file
cat > values-prod.yaml <<EOF
replicaCount: 3

secrets:
  anthropicApiKey: "sk-ant-..."
  githubToken: "ghp_..."
  openaiApiKey: "sk-..."

resources:
  limits:
    cpu: 2000m
    memory: 4Gi
  requests:
    cpu: 1000m
    memory: 2Gi

ingress:
  enabled: true
  className: nginx
  hosts:
    - host: api.skillseekers.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: skillseekers-tls
      hosts:
        - api.skillseekers.example.com

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
EOF

# Install with custom values
helm install skillseekers ./helm/skillseekers \
  --namespace skillseekers \
  --create-namespace \
  --values values-prod.yaml
```

### 3. Helm Commands

```bash
# List releases
helm list -n skillseekers

# Get status
helm status skillseekers -n skillseekers

# Upgrade release
helm upgrade skillseekers ./helm/skillseekers \
  --namespace skillseekers \
  --values values-prod.yaml

# Rollback
helm rollback skillseekers 1 -n skillseekers

# Uninstall
helm uninstall skillseekers -n skillseekers
```

## Manual Deployment

### 1. Secrets

Create secrets for API keys:

```yaml
# secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: skillseekers-secrets
  namespace: skillseekers
type: Opaque
stringData:
  ANTHROPIC_API_KEY: "sk-ant-..."
  GITHUB_TOKEN: "ghp_..."
  OPENAI_API_KEY: "sk-..."
  VOYAGE_API_KEY: "..."
```

```bash
kubectl apply -f secrets.yaml
```

### 2. ConfigMap

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: skillseekers-config
  namespace: skillseekers
data:
  MCP_TRANSPORT: "http"
  MCP_PORT: "8765"
  LOG_LEVEL: "INFO"
  CACHE_TTL: "86400"
```

```bash
kubectl apply -f configmap.yaml
```

### 3. Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: skillseekers-mcp
  namespace: skillseekers
  labels:
    app: skillseekers
    component: mcp-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: skillseekers
      component: mcp-server
  template:
    metadata:
      labels:
        app: skillseekers
        component: mcp-server
    spec:
      containers:
      - name: mcp-server
        image: skillseekers:2.9.0
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8765
          name: http
          protocol: TCP
        env:
        - name: MCP_TRANSPORT
          valueFrom:
            configMapKeyRef:
              name: skillseekers-config
              key: MCP_TRANSPORT
        - name: MCP_PORT
          valueFrom:
            configMapKeyRef:
              name: skillseekers-config
              key: MCP_PORT
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: skillseekers-secrets
              key: ANTHROPIC_API_KEY
        - name: GITHUB_TOKEN
          valueFrom:
            secretKeyRef:
              name: skillseekers-secrets
              key: GITHUB_TOKEN
        resources:
          requests:
            cpu: 1000m
            memory: 2Gi
          limits:
            cpu: 2000m
            memory: 4Gi
        livenessProbe:
          httpGet:
            path: /health
            port: 8765
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health
            port: 8765
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2
        volumeMounts:
        - name: data
          mountPath: /app/data
        - name: cache
          mountPath: /app/cache
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: skillseekers-data
      - name: cache
        emptyDir: {}
```

```bash
kubectl apply -f deployment.yaml
```

### 4. Service

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: skillseekers-mcp
  namespace: skillseekers
  labels:
    app: skillseekers
    component: mcp-server
spec:
  type: ClusterIP
  ports:
  - port: 8765
    targetPort: 8765
    protocol: TCP
    name: http
  selector:
    app: skillseekers
    component: mcp-server
```

```bash
kubectl apply -f service.yaml
```

### 5. Verify Deployment

```bash
# Check pods
kubectl get pods -n skillseekers

# Check services
kubectl get svc -n skillseekers

# Check logs
kubectl logs -n skillseekers -l app=skillseekers --tail=100 -f

# Port forward for testing
kubectl port-forward -n skillseekers svc/skillseekers-mcp 8765:8765

# Test endpoint
curl http://localhost:8765/health
```

## Configuration

### 1. Resource Requests & Limits

```yaml
resources:
  requests:
    cpu: 500m      # Guaranteed CPU
    memory: 1Gi    # Guaranteed memory
  limits:
    cpu: 2000m     # Maximum CPU
    memory: 4Gi    # Maximum memory
```

### 2. Environment Variables

```yaml
env:
# From ConfigMap
- name: LOG_LEVEL
  valueFrom:
    configMapKeyRef:
      name: skillseekers-config
      key: LOG_LEVEL

# From Secret
- name: ANTHROPIC_API_KEY
  valueFrom:
    secretKeyRef:
      name: skillseekers-secrets
      key: ANTHROPIC_API_KEY

# Direct value
- name: MCP_TRANSPORT
  value: "http"
```

### 3. Multi-Environment Setup

```bash
# Development
helm install skillseekers-dev ./helm/skillseekers \
  --namespace skillseekers-dev \
  --values values-dev.yaml

# Staging
helm install skillseekers-staging ./helm/skillseekers \
  --namespace skillseekers-staging \
  --values values-staging.yaml

# Production
helm install skillseekers-prod ./helm/skillseekers \
  --namespace skillseekers-prod \
  --values values-prod.yaml
```

## Scaling

### 1. Manual Scaling

```bash
# Scale deployment
kubectl scale deployment skillseekers-mcp -n skillseekers --replicas=5

# Verify
kubectl get pods -n skillseekers
```

### 2. Horizontal Pod Autoscaler (HPA)

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: skillseekers-mcp
  namespace: skillseekers
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: skillseekers-mcp
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
      - type: Pods
        value: 2
        periodSeconds: 15
      selectPolicy: Max
```

```bash
kubectl apply -f hpa.yaml

# Monitor autoscaling
kubectl get hpa -n skillseekers --watch
```

### 3. Vertical Pod Autoscaler (VPA)

```yaml
# vpa.yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: skillseekers-mcp
  namespace: skillseekers
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: skillseekers-mcp
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: mcp-server
      minAllowed:
        cpu: 500m
        memory: 1Gi
      maxAllowed:
        cpu: 4000m
        memory: 8Gi
```

## High Availability

### 1. Pod Disruption Budget

```yaml
# pdb.yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: skillseekers-mcp
  namespace: skillseekers
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: skillseekers
      component: mcp-server
```

### 2. Pod Anti-Affinity

```yaml
spec:
  affinity:
    podAntiAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchExpressions:
            - key: app
              operator: In
              values:
              - skillseekers
          topologyKey: kubernetes.io/hostname
```

### 3. Node Affinity

```yaml
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: node-role
            operator: In
            values:
            - worker
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 1
        preference:
          matchExpressions:
          - key: node-type
            operator: In
            values:
            - high-cpu
```

### 4. Multi-Zone Deployment

```yaml
spec:
  topologySpreadConstraints:
  - maxSkew: 1
    topologyKey: topology.kubernetes.io/zone
    whenUnsatisfiable: DoNotSchedule
    labelSelector:
      matchLabels:
        app: skillseekers
```

## Monitoring

### 1. Prometheus Metrics

```yaml
# servicemonitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: skillseekers-mcp
  namespace: skillseekers
spec:
  selector:
    matchLabels:
      app: skillseekers
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
```

### 2. Grafana Dashboard

```bash
# Import dashboard
kubectl apply -f grafana/dashboard.json
```

### 3. Logging with Fluentd

```yaml
# fluentd-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluentd-config
data:
  fluent.conf: |
    <source>
      @type tail
      path /var/log/containers/skillseekers*.log
      pos_file /var/log/fluentd-skillseekers.pos
      tag kubernetes.*
      format json
    </source>
    <match **>
      @type elasticsearch
      host elasticsearch
      port 9200
    </match>
```

## Ingress & Load Balancing

### 1. Nginx Ingress

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: skillseekers
  namespace: skillseekers
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - api.skillseekers.example.com
    secretName: skillseekers-tls
  rules:
  - host: api.skillseekers.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: skillseekers-mcp
            port:
              number: 8765
```

### 2. TLS with cert-manager

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create ClusterIssuer
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

## Storage

### 1. Persistent Volume

```yaml
# pv.yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: skillseekers-data
spec:
  capacity:
    storage: 50Gi
  accessModes:
  - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: standard
  hostPath:
    path: /mnt/skillseekers-data
```

### 2. Persistent Volume Claim

```yaml
# pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: skillseekers-data
  namespace: skillseekers
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi
  storageClassName: standard
```

### 3. StatefulSet (for stateful workloads)

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: skillseekers-cache
spec:
  serviceName: skillseekers-cache
  replicas: 3
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 10Gi
```

## Security

### 1. Network Policies

```yaml
# networkpolicy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: skillseekers-mcp
  namespace: skillseekers
spec:
  podSelector:
    matchLabels:
      app: skillseekers
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: skillseekers
    ports:
    - protocol: TCP
      port: 8765
  egress:
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 443  # HTTPS
    - protocol: TCP
      port: 80   # HTTP
```

### 2. Pod Security Policy

```yaml
# psp.yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: skillseekers-restricted
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
  - ALL
  volumes:
  - 'configMap'
  - 'emptyDir'
  - 'projected'
  - 'secret'
  - 'persistentVolumeClaim'
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'RunAsAny'
  fsGroup:
    rule: 'RunAsAny'
```

### 3. RBAC

```yaml
# rbac.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: skillseekers
  namespace: skillseekers
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: skillseekers
  namespace: skillseekers
rules:
- apiGroups: [""]
  resources: ["configmaps", "secrets"]
  verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: skillseekers
  namespace: skillseekers
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: skillseekers
subjects:
- kind: ServiceAccount
  name: skillseekers
  namespace: skillseekers
```

## Troubleshooting

### Common Issues

#### 1. Pods Not Starting

```bash
# Check pod status
kubectl get pods -n skillseekers

# Describe pod
kubectl describe pod <pod-name> -n skillseekers

# Check events
kubectl get events -n skillseekers --sort-by='.lastTimestamp'

# Check logs
kubectl logs <pod-name> -n skillseekers
```

#### 2. Image Pull Errors

```bash
# Check image pull secrets
kubectl get secrets -n skillseekers

# Create image pull secret
kubectl create secret docker-registry regcred \
  --docker-server=registry.example.com \
  --docker-username=user \
  --docker-password=password \
  -n skillseekers

# Use in pod spec
spec:
  imagePullSecrets:
  - name: regcred
```

#### 3. Resource Constraints

```bash
# Check node resources
kubectl top nodes

# Check pod resources
kubectl top pods -n skillseekers

# Increase resources
kubectl edit deployment skillseekers-mcp -n skillseekers
```

#### 4. Service Not Accessible

```bash
# Check service
kubectl get svc -n skillseekers
kubectl describe svc skillseekers-mcp -n skillseekers

# Check endpoints
kubectl get endpoints -n skillseekers

# Port forward
kubectl port-forward svc/skillseekers-mcp 8765:8765 -n skillseekers
```

### Debug Commands

```bash
# Execute command in pod
kubectl exec -it <pod-name> -n skillseekers -- /bin/bash

# Copy files from pod
kubectl cp skillseekers/<pod-name>:/app/data ./data

# Check pod networking
kubectl exec <pod-name> -n skillseekers -- nslookup google.com

# View full pod spec
kubectl get pod <pod-name> -n skillseekers -o yaml

# Restart deployment
kubectl rollout restart deployment skillseekers-mcp -n skillseekers
```

## Best Practices

1. **Always set resource requests and limits**
2. **Use namespaces for environment separation**
3. **Enable autoscaling for variable workloads**
4. **Implement health checks (liveness & readiness)**
5. **Use Secrets for sensitive data**
6. **Enable monitoring and logging**
7. **Implement Pod Disruption Budgets for HA**
8. **Use RBAC for access control**
9. **Enable Network Policies**
10. **Regular backup of persistent volumes**

## Next Steps

- Review [PRODUCTION_DEPLOYMENT.md](./PRODUCTION_DEPLOYMENT.md) for general guidelines
- See [DOCKER_DEPLOYMENT.md](./DOCKER_DEPLOYMENT.md) for container-specific details
- Check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for common issues

---

**Need help?** Open an issue on [GitHub](https://github.com/yusufkaraaslan/Skill_Seekers/issues).
