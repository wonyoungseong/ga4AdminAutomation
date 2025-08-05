# GA4 Admin Portal - Infrastructure Architecture

## 🏗️ Enterprise Infrastructure Overview

The GA4 Admin Portal is deployed using a robust, enterprise-grade infrastructure that provides high availability, scalability, and security for production environments.

### Architecture Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        Internet / CDN                            │
└─────────────────┬───────────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────────┐
│                    Load Balancer / Nginx                       │
│  • SSL/TLS Termination                                         │
│  • Rate Limiting & DDoS Protection                             │
│  • Static Content Caching                                      │
│  • Health Checks & Failover                                    │
└─────────────────┬───────────────────────────────────────────────┘
                  │
         ┌────────▼────────┐          ┌─────────────────────┐
         │   Frontend      │          │      Backend        │
         │   (Next.js)     │◄────────►│     (FastAPI)      │
         │   Port: 3000    │          │     Port: 8000     │
         └─────────────────┘          └─────────┬───────────┘
                                                │
                   ┌────────────────────────────┼────────────────────┐
                   │                            │                    │
         ┌─────────▼──────────┐    ┌──────────▼──────────┐ ┌────────▼────────┐
         │    PostgreSQL      │    │       Redis         │ │   Monitoring    │
         │    Database        │    │      Cache          │ │ Prometheus +    │
         │    Port: 5432      │    │    Port: 6379       │ │    Grafana      │
         └────────────────────┘    └─────────────────────┘ └─────────────────┘
```

## 🐳 Docker Containerization

### Frontend Container (Next.js)
- **Base Image**: `node:20-alpine`
- **Multi-stage Build**: Development deps → Build → Production runtime
- **Security**: Non-root user, minimal attack surface
- **Performance**: Static optimization, output caching
- **Health Checks**: Built-in health endpoints

### Backend Container (FastAPI)
- **Base Image**: `python:3.11-slim`
- **Multi-stage Build**: Dependencies → Application → Runtime
- **Security**: Non-root user, minimal dependencies
- **Performance**: Uvicorn with multiple workers
- **Health Checks**: `/health` endpoint with database connectivity

### Database Container (PostgreSQL)
- **Base Image**: `postgres:16-alpine`
- **Persistence**: Volume mounts for data persistence
- **Security**: Custom user/password, network isolation
- **Performance**: Optimized configuration for production workloads
- **Backup**: Automated backup strategies

## 🔧 Infrastructure Services

### Reverse Proxy (Nginx)
**Configuration**: `/nginx/nginx-optimized.conf`

#### Key Features:
- **SSL/TLS**: Let's Encrypt integration with auto-renewal
- **Performance**: HTTP/2, gzip compression, caching
- **Security**: Rate limiting, security headers, DDoS protection
- **Load Balancing**: Upstream health checks, failover
- **Monitoring**: Detailed access logs with performance metrics

#### Rate Limiting:
```nginx
limit_req_zone $binary_remote_addr zone=api:20m rate=100r/s;
limit_req_zone $binary_remote_addr zone=auth:10m rate=10r/m;
limit_req_zone $binary_remote_addr zone=upload:10m rate=5r/m;
```

#### Caching Strategy:
- **Static Assets**: 1 year cache with immutable headers
- **API Responses**: 5-minute cache with auth bypass
- **Dynamic Content**: 1-minute cache with intelligent invalidation

### Database Layer

#### PostgreSQL Configuration:
- **Version**: PostgreSQL 16 with Alpine Linux
- **Connection Pooling**: Built-in connection management
- **Performance**: Optimized for concurrent connections
- **Backup**: Automated daily backups with retention policy
- **Migration**: Automated SQLite → PostgreSQL migration

#### Redis Configuration:
- **Purpose**: Session storage, API caching, rate limiting
- **Persistence**: RDB + AOF for data durability
- **Performance**: Memory optimization for high throughput
- **Security**: Password protection, network isolation

## 📊 Monitoring & Observability

### Prometheus Metrics Collection
- **Application Metrics**: Request duration, error rates, throughput
- **Infrastructure Metrics**: CPU, memory, disk, network
- **Business Metrics**: User activity, feature usage, performance
- **Custom Metrics**: GA4-specific analytics and reporting

### Grafana Dashboards
- **System Overview**: Infrastructure health and performance
- **Application Metrics**: Request patterns, error analysis
- **User Analytics**: Usage patterns, performance impact
- **Alerting**: Proactive notification of issues

### Log Aggregation (Loki + Promtail)
- **Centralized Logging**: All services log to central location
- **Log Correlation**: Request tracing across services
- **Search & Analysis**: Full-text search and filtering
- **Retention**: Configurable log retention policies

## 🔒 Security Architecture

### Network Security
- **Firewall Rules**: Restrict access to essential ports only
- **Private Networks**: Internal service communication isolation
- **SSL/TLS**: End-to-end encryption with modern protocols
- **VPN Access**: Secure administrative access

### Application Security
- **Authentication**: JWT-based with refresh tokens
- **Authorization**: Role-based access control (RBAC)
- **Input Validation**: Comprehensive request validation
- **Rate Limiting**: API and authentication endpoint protection

### Container Security
- **Non-root Users**: All containers run as non-root
- **Minimal Images**: Alpine-based images with minimal attack surface
- **Security Scanning**: Automated vulnerability scanning
- **Resource Limits**: Memory and CPU limits to prevent abuse

### Data Security
- **Encryption at Rest**: Database encryption
- **Encryption in Transit**: All communications encrypted
- **Backup Encryption**: Encrypted backup storage
- **Secrets Management**: Environment-based secrets

## 🚀 Deployment Architecture

### Deployment Strategies

#### Container Orchestration Options:

1. **Docker Compose (Recommended for Small-Medium Scale)**
   ```bash
   # Production deployment
   ./scripts/deploy.sh --env production --domain your-domain.com
   
   # Development deployment
   ./scripts/deploy.sh --env development
   ```

2. **Kubernetes (Enterprise Scale)**
   ```bash
   # K8s deployment
   ./scripts/deploy.sh deploy --environment production
   ```

### CI/CD Pipeline Integration

#### GitHub Actions Workflow:
```yaml
name: Deploy GA4 Admin Portal
on:
  push:
    branches: [main]
    
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Production
        run: ./scripts/deploy.sh --env production
        env:
          DOMAIN: ${{ secrets.DOMAIN }}
          EMAIL: ${{ secrets.EMAIL }}
```

## 📈 Scalability & Performance

### Horizontal Scaling
- **Load Balancer**: Nginx upstream configuration
- **Frontend Scaling**: Multiple Next.js instances
- **Backend Scaling**: Multiple FastAPI workers
- **Database Scaling**: Read replicas, connection pooling

### Performance Optimizations
- **Caching Layers**: Multi-level caching strategy
- **CDN Integration**: Static asset distribution
- **Database Optimization**: Indexes, query optimization
- **Connection Pooling**: Efficient resource utilization

### Capacity Planning
- **Monitoring**: Real-time performance metrics
- **Alerting**: Proactive scaling notifications
- **Auto-scaling**: Container orchestration scaling
- **Resource Allocation**: Dynamic resource management

## 🛠️ Operations & Maintenance

### Deployment Procedures

#### 1. SSL Certificate Setup
```bash
# Development (self-signed)
./scripts/generate-ssl-certs.sh

# Production (Let's Encrypt)
./scripts/generate-ssl-certs.sh --production --domain your-domain.com --email admin@your-domain.com
```

#### 2. Database Migration
```bash
# Migrate from SQLite to PostgreSQL
python scripts/migrate-to-postgres.py \
  --sqlite-path ./backend/data/ga4_admin.db \
  --postgres-url "postgresql+asyncpg://user:pass@localhost:5432/ga4_admin"
```

#### 3. Full Deployment
```bash
# Production deployment with health checks
./scripts/deploy.sh \
  --env production \
  --domain your-domain.com \
  --email admin@your-domain.com
```

### Health Monitoring

#### Automated Health Checks:
- **Frontend**: HTTP 200 response on root path
- **Backend**: `/health` endpoint with database connectivity
- **Database**: Connection and query response time
- **Redis**: Ping response and memory usage
- **SSL**: Certificate validity and expiration

#### Performance Monitoring:
- **Response Time**: < 200ms for API endpoints
- **Throughput**: Requests per second capacity
- **Error Rate**: < 0.1% error rate target
- **Availability**: 99.9% uptime SLA

### Backup & Recovery

#### Backup Strategy:
- **Database**: Daily automated backups with 30-day retention
- **Configuration**: Version-controlled infrastructure as code
- **Application Data**: Regular data exports
- **SSL Certificates**: Automated renewal and backup

#### Recovery Procedures:
1. **Database Recovery**: Point-in-time recovery from backups
2. **Application Recovery**: Container restart with health checks
3. **Full System Recovery**: Infrastructure recreation from code
4. **Rollback**: Automated rollback to previous stable version

## 🔧 Troubleshooting Guide

### Common Issues & Solutions

#### 1. SSL Certificate Issues
```bash
# Check certificate validity
openssl s_client -connect your-domain.com:443 -servername your-domain.com

# Regenerate certificates
./scripts/generate-ssl-certs.sh --production --domain your-domain.com --email admin@your-domain.com
```

#### 2. Database Connection Issues
```bash
# Check PostgreSQL connectivity
docker-compose exec postgres pg_isready -U postgres

# View database logs
docker-compose logs postgres
```

#### 3. Performance Issues
```bash
# Check resource usage
docker stats

# View application logs
docker-compose logs backend frontend

# Check health endpoints
curl https://your-domain.com/health
curl https://api.your-domain.com/health
```

#### 4. Nginx Configuration Issues
```bash
# Test nginx configuration
docker-compose exec nginx nginx -t

# Reload nginx configuration
docker-compose exec nginx nginx -s reload
```

### Monitoring Dashboards

#### Access URLs:
- **Application**: https://your-domain.com
- **API**: https://api.your-domain.com
- **Grafana**: https://your-domain.com:3002
- **Prometheus**: https://your-domain.com:9090

#### Key Metrics to Monitor:
- **Request Rate**: Requests per second
- **Response Time**: 95th percentile latency
- **Error Rate**: 4xx/5xx error percentage
- **System Resources**: CPU, memory, disk usage
- **Database Performance**: Query time, connection count

## 📚 Additional Resources

### Documentation:
- [Docker Compose Reference](./docker-compose.yml)
- [Nginx Configuration](./nginx/nginx-optimized.conf)
- [SSL Setup Guide](./scripts/generate-ssl-certs.sh)
- [Migration Scripts](./scripts/migrate-to-postgres.py)

### Scripts:
- `./scripts/deploy.sh` - Main deployment automation
- `./scripts/generate-ssl-certs.sh` - SSL certificate management
- `./scripts/migrate-to-postgres.py` - Database migration

### Configuration Files:
- `.env` - Environment configuration
- `docker-compose.yml` - Service orchestration
- `nginx/nginx-optimized.conf` - Web server configuration
- `k8s/` - Kubernetes manifests (enterprise)

## 🎯 Next Steps

### Immediate Actions:
1. **Configure Environment**: Update `.env` with production values
2. **SSL Setup**: Generate and install SSL certificates
3. **Deploy**: Run full deployment with health checks
4. **Monitor**: Set up alerting and monitoring dashboards

### Advanced Features:
1. **Auto-scaling**: Implement container auto-scaling
2. **CDN Integration**: Add CloudFlare or AWS CloudFront
3. **Multi-region**: Deploy across multiple regions
4. **Disaster Recovery**: Implement cross-region backups

### Security Enhancements:
1. **WAF**: Web Application Firewall integration
2. **Intrusion Detection**: Network monitoring and alerting
3. **Compliance**: SOC2/GDPR compliance implementation
4. **Penetration Testing**: Regular security assessments

---

*For technical support or infrastructure questions, please refer to the troubleshooting guide or contact the infrastructure team.*