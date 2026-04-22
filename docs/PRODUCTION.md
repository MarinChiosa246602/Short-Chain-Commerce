# Production Deployment Guide

## Prerequisites

- Docker & Docker Compose installed
- Domain name configured (optional)
- SSL certificates ready (for HTTPS)
- Database backup strategy in place

## Environment Setup

### 1. Create Production Environment File

```bash
cp .env.prod.example .env.prod
```

Edit `.env.prod` with your values:

```bash
# Required values
DATABASE_URL=postgresql://user:password@db:5432/shortchain_prod
REDIS_URL=redis://:password@redis:6379/0
JWT_SECRET_KEY=<generate-random-32-char-string>
POSTGRES_USER=prod_user
POSTGRES_PASSWORD=<strong-password>
POSTGRES_DB=shortchain_prod
REDIS_PASSWORD=<strong-password>
```

### 2. Generate Secure Keys

```bash
# Generate JWT secret
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate API keys
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Deployment Steps

### Step 1: Database Initialization

```bash
# Start database only
docker-compose -f docker-compose.prod.yml up -d db redis

# Wait for database to be ready
sleep 10

# Run migrations
docker exec shortchain-db-prod psql -U prod_user -d shortchain_prod -f /docker-entrypoint-initdb.d/init.sql
```

### Step 2: Deploy Application

```bash
# Build and start all services
docker-compose -f docker-compose.prod.yml up -d --build

# Check health
curl http://localhost:8000/health
```

### Step 3: Verify Deployment

```bash
# Test API endpoints
curl http://localhost:8000/api/v1/metrics
curl http://localhost:8000/api/v1/health/detailed

# Check logs
docker-compose -f docker-compose.prod.yml logs -f
```

## Security Checklist

### Before Going Live

- [ ] All default passwords changed
- [ ] JWT secret is cryptographically random
- [ ] API keys generated and stored securely
- [ ] Database port not exposed to public
- [ ] HTTPS/SSL configured
- [ ] Rate limiting enabled
- [ ] Logging configured (no sensitive data)
- [ ] Backup strategy in place
- [ ] Monitoring/alerting configured
- [ ] Firewall rules configured

### Ongoing Security

- [ ] Regular security updates
- [ ] Log review schedule
- [ ] Access audit trail
- [ ] Vulnerability scanning
- [ ] Penetration testing (annual)

## Performance Optimization

### Database

```sql
-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_extractions_timestamp ON extractions(timestamp);
CREATE INDEX IF NOT EXISTS idx_extractions_status ON extractions(status);
CREATE INDEX IF NOT EXISTS idx_products_product_id ON products(product_id);

-- Enable connection pooling
ALTER SYSTEM SET max_connections = 200;
```

### Redis Caching

```python
# Cache configuration
CACHE_TTL = 300  # 5 minutes
CACHE_KEY_PREFIX = "shortchain:"
```

### API Optimization

- Enable gzip compression (in nginx)
- Set response caching headers
- Limit payload sizes
- Use connection pooling

### Resource Limits

```yaml
# In docker-compose.prod.yml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 4G
    reservations:
      cpus: '1'
      memory: 2G
```

## Monitoring Setup

### Health Checks

```bash
# Every 30 seconds
curl -f http://localhost:8000/health || exit 1

# Detailed health
curl http://localhost:8000/api/v1/health/detailed
```

### Metrics Collection

```bash
# Prometheus scrape endpoint
curl http://localhost:8000/api/v1/metrics
```

### Log Aggregation

```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f api

# Search logs
docker-compose -f docker-compose.prod.yml logs api | grep ERROR
```

## Backup & Recovery

### Database Backup

```bash
# Daily backup
docker exec shortchain-db-prod pg_dump -U prod_user shortchain_prod > backup_$(date +%Y%m%d).sql

# Compress
gzip backup_$(date +%Y%m%d).sql

# Store securely (S3, external storage)
```

### Restore Procedure

```bash
# Stop services
docker-compose -f docker-compose.prod.yml down

# Restore database
gunzip backup_20240101.sql.gz
docker exec -i shortchain-db-prod psql -U prod_user -d shortchain_prod < backup_20240101.sql

# Restart services
docker-compose -f docker-compose.prod.yml up -d
```

## Rollback Plan

### If Deployment Fails

```bash
# Stop current version
docker-compose -f docker-compose.prod.yml down

# Start previous version
docker-compose -f docker-compose.prod.yml pull previous
docker-compose -f docker-compose.prod.yml up -d

# Verify rollback
curl http://localhost:8000/health
```

## Troubleshooting

### Common Issues

#### High Memory Usage
```bash
# Check memory
docker stats

# Restart if needed
docker-compose -f docker-compose.prod.yml restart
```

#### Database Connection Errors
```bash
# Check database status
docker logs shortchain-db-prod

# Verify connection
docker exec shortchain-db-prod pg_isready -U prod_user
```

#### API Not Responding
```bash
# Check API logs
docker logs shortchain-api-prod --tail 100

# Check health
curl -v http://localhost:8000/health
```

## Scaling

### Vertical Scaling
```bash
# Update docker-compose.prod.yml
deploy:
  resources:
    limits:
      memory: 8G  # Increase from 4G
```

### Horizontal Scaling
```bash
# Run multiple API instances
docker-compose -f docker-compose.prod.yml up -d --scale api=3
```

## Contact & Support

- Documentation: [./docs/PRODUCTION.md](./docs/PRODUCTION.md)
- API Docs: http://your-domain.com/docs
- Emergency: [on-call contact]
