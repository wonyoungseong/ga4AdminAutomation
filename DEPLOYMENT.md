# GA4 Admin Portal - Production Deployment Guide

## 🏗️ Architecture Overview

The GA4 Admin Portal is deployed using a microservices architecture with the following components:

- **Frontend**: Next.js 15 application with server-side rendering
- **Backend**: FastAPI with async PostgreSQL database
- **Database**: PostgreSQL 16 with connection pooling
- **Caching**: Redis for session management and caching
- **Reverse Proxy**: Nginx with SSL termination and load balancing
- **Monitoring**: Prometheus + Grafana + Loki stack
- **Container Orchestration**: Kubernetes with auto-scaling

## 🚀 Quick Start

### Prerequisites

1. **Container Runtime**: Docker Desktop or Docker Engine
2. **Kubernetes**: kubectl configured with cluster access
3. **Registry Access**: GitHub Container Registry or similar
4. **Domain**: SSL certificates for your domain

### 1. Clone and Configure

```bash
git clone <repository-url>
cd ga4AdminAutomation

# Copy and configure environment
cp .env.production .env.local
# Edit .env.local with your production values
```

### 2. Build and Deploy

```bash
# Full deployment
./scripts/deploy.sh

# Or step by step
./scripts/deploy.sh build
./scripts/deploy.sh push
./scripts/deploy.sh deploy
```

### 3. Verify Deployment

```bash
# Check deployment status
kubectl get pods -n ga4-admin

# Run health checks
./scripts/deploy.sh health-check

# Access application
kubectl port-forward service/nginx 8080:80 -n ga4-admin
```

## 📋 Detailed Setup

### Environment Configuration

Edit `.env.production` with your production values:

```bash
# Database
DB_PASSWORD=your_secure_password_here
DATABASE_URL=postgresql+asyncpg://postgres:your_secure_password_here@postgres:5432/ga4_admin

# Security
SECRET_KEY=your-super-secure-secret-key-min-32-characters
JWT_SECRET_KEY=another-secure-key-for-jwt-tokens

# Domain
FRONTEND_URL=https://your-domain.com
NEXT_PUBLIC_API_URL=https://api.your-domain.com

# Google API
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Email
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password
```

### SSL Certificate Setup

1. **Option A: Let's Encrypt (Recommended)**
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
    email: your-email@your-domain.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

2. **Option B: Custom Certificates**
```bash
# Create SSL secret
kubectl create secret tls ssl-cert \
  --cert=path/to/cert.pem \
  --key=path/to/key.pem \
  -n ga4-admin
```

### Database Migration (from SQLite)

If migrating from existing SQLite database:

```bash
# Set migration flag
export MIGRATE_FROM_SQLITE=true

# Run deployment with migration
./scripts/deploy.sh deploy

# Or run migration manually
python scripts/migrate-to-postgres.py \
  --sqlite-path ./backend/ga4_admin.db \
  --postgres-url "postgresql+asyncpg://postgres:password@localhost:5432/ga4_admin"
```

## 🔍 Monitoring and Observability

### Accessing Monitoring Dashboards

```bash
# Grafana Dashboard
kubectl port-forward service/grafana 3002:3000 -n ga4-admin
# Access: http://localhost:3002 (admin/admin)

# Prometheus Metrics
kubectl port-forward service/prometheus 9090:9090 -n ga4-admin
# Access: http://localhost:9090

# Application Logs
kubectl logs -f deployment/backend -n ga4-admin
kubectl logs -f deployment/frontend -n ga4-admin
```

### Key Metrics to Monitor

- **Application**: Response time, error rate, throughput
- **Database**: Connection count, query performance, disk usage
- **Infrastructure**: CPU, memory, disk, network
- **Business**: User registrations, API usage, feature adoption

## 🔒 Security Hardening

### Network Security

The deployment includes:
- Network policies for pod-to-pod communication
- RBAC for service account permissions
- Security contexts with non-root users
- Secrets management for sensitive data

### Application Security

- JWT token authentication with refresh tokens
- Rate limiting on API endpoints
- CORS protection with specific origins
- Security headers (HSTS, CSP, X-Frame-Options)
- Input validation and sanitization

### Database Security

- Connection encryption with SSL/TLS
- Role-based access control
- Regular security updates
- Backup encryption

## 📈 Scaling and Performance

### Auto-scaling Configuration

The deployment includes Horizontal Pod Autoscalers (HPA):

```yaml
# Backend: 3-10 pods based on CPU/Memory
minReplicas: 3
maxReplicas: 10
targetCPUUtilization: 70%
targetMemoryUtilization: 80%

# Frontend: 2-5 pods based on CPU
minReplicas: 2
maxReplicas: 5
targetCPUUtilization: 70%
```

### Performance Optimization

- **Frontend**: Next.js with static generation and caching
- **Backend**: FastAPI with async database connections
- **Database**: Connection pooling and query optimization
- **Caching**: Redis for session and application caches
- **CDN**: Static asset delivery optimization

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

The project includes a comprehensive CI/CD pipeline:

1. **Code Quality**: Linting, type checking, testing
2. **Security**: Vulnerability scanning with Trivy
3. **Build**: Multi-stage Docker builds with caching
4. **Deploy**: Automated deployment to staging/production
5. **Verify**: Health checks and smoke tests

### Manual Deployment Commands

```bash
# Build and test locally
docker-compose up --build

# Deploy to staging
TAG=v1.0.0 ENVIRONMENT=staging ./scripts/deploy.sh

# Deploy to production
TAG=v1.0.0 ENVIRONMENT=production ./scripts/deploy.sh

# Rollback if needed
./scripts/deploy.sh rollback
```

## 🛠️ Troubleshooting

### Common Issues

1. **Pods not starting**
```bash
# Check pod status and logs
kubectl describe pod <pod-name> -n ga4-admin
kubectl logs <pod-name> -n ga4-admin
```

2. **Database connection issues**
```bash
# Check PostgreSQL pod
kubectl exec -it deployment/postgres -n ga4-admin -- psql -U postgres -d ga4_admin

# Test connection from backend
kubectl exec -it deployment/backend -n ga4-admin -- python -c "
from sqlalchemy import create_engine
engine = create_engine('postgresql://postgres:password@postgres:5432/ga4_admin')
print('Connection successful!')
"
```

3. **SSL certificate issues**
```bash
# Check certificate status
kubectl describe certificate ssl-cert -n ga4-admin

# Check cert-manager logs
kubectl logs -f deployment/cert-manager -n cert-manager
```

### Performance Debugging

```bash
# Check resource usage
kubectl top pods -n ga4-admin
kubectl top nodes

# Check application metrics
curl http://localhost:8000/metrics  # Backend metrics
curl http://localhost:3000/api/metrics  # Frontend metrics
```

## 📚 Additional Resources

### Documentation

- [Backend API Documentation](/api/docs)
- [Frontend Component Library](/storybook)
- [Database Schema](/docs/schema.md)
- [Security Policies](/docs/security.md)

### Support

- **Issues**: GitHub Issues for bug reports
- **Discussions**: GitHub Discussions for questions
- **Security**: security@your-domain.com for security issues

## 🔄 Maintenance

### Regular Tasks

1. **Weekly**: Review monitoring dashboards and alerts
2. **Monthly**: Update dependencies and security patches
3. **Quarterly**: Performance review and capacity planning
4. **Annually**: Security audit and penetration testing

### Backup Strategy

- **Database**: Daily automated backups with 30-day retention
- **Application Data**: Persistent volume snapshots
- **Configuration**: Git repository with infrastructure as code

### Disaster Recovery

- **RTO**: 4 hours (Recovery Time Objective)
- **RPO**: 1 hour (Recovery Point Objective)
- **Backup Locations**: Multi-region backup storage
- **Testing**: Monthly disaster recovery testing

---

## 📞 Emergency Contacts

- **DevOps Team**: devops@your-domain.com
- **Security Team**: security@your-domain.com
- **On-call Engineer**: +1-xxx-xxx-xxxx

For immediate issues, use the on-call rotation or create a P0 incident in your incident management system.