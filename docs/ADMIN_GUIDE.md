# Administrator Guide

## Overview

This guide is for system administrators managing the Short Chain Commerce deployment.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Load Balancer / Nginx                   │
└─────────────────────────────────────────────────────────────┘
                            │
           ┌────────────────┼────────────────┐
           │                │                │
           ▼                ▼                ▼
    ┌──────────┐     ┌──────────┐     ┌──────────┐
    │   API    │     │  Worker  │     │  Frontend│
    │ (FastAPI)│     │ (Celery) │     │  (React) │
    └──────────┘     └──────────┘     └──────────┘
           │                │                │
           └────────────────┼────────────────┘
                            │
           ┌────────────────┼────────────────┐
           │                │                │
           ▼                ▼                ▼
    ┌──────────┐     ┌──────────┐     ┌──────────┐
    │ PostgreSQL │   │  Redis   │   │  Storage │
    │  (DB)     │   │ (Queue)  │   │  (Files) │
    └──────────┘     └──────────┘     └──────────┘
```

## User Management

### Creating API Keys

```bash
# Generate new API key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Hash and store
python -c "import hashlib; print(hashlib.sha256(b'YOUR_KEY').hexdigest())"

# Add to data/api_keys.json
```

### User Roles

| Role | Permissions |
|------|-------------|
| admin | Full access, user management |
| operator | Extractions, history, reports |
| viewer | Read-only access |

### Managing Users

```sql
-- List all users
SELECT * FROM users;

-- Create user
INSERT INTO users (username, email, role, created_at)
VALUES ('newuser', 'user@company.com', 'operator', NOW());

-- Reset password
UPDATE users SET password_hash = 'hash' WHERE username = 'newuser';
```

## Monitoring

### Health Check Commands

```bash
# All services
docker-compose -f docker-compose.prod.yml ps

# Service status
docker-compose -f docker-compose.prod.yml logs --tail=100 api
docker-compose -f docker-compose.prod.yml logs --tail=100 worker
docker-compose -f docker-compose.prod.yml logs --tail=100 db
```

### Metrics to Watch

| Metric | Warning | Critical |
|--------|---------|----------|
| API Response Time | >500ms | >2000ms |
| Error Rate | >5% | >10% |
| Memory Usage | >70% | >90% |
| Disk Space | <20% free | <10% free |
| Queue Length | >100 | >500 |

### Setting Up Alerts

```bash
# Example: Disk space alert
df -h | grep -v "Filesystem" | awk '{if ($5+0 > 80) print "WARNING: "$5" used on "$6}'
```

## Maintenance Tasks

### Daily Checks

```bash
# 1. Check service health
curl http://localhost:8000/health

# 2. Review error logs
docker logs shortchain-api-prod --tail 50 | grep ERROR

# 3. Check disk space
df -h

# 4. Verify backups ran
ls -la backups/ | grep $(date +%Y%m%d)
```

### Weekly Tasks

```bash
# 1. Database backup
pg_dump -U prod_user shortchain_prod | gzip > backups/$(date +%Y%m%d).sql.gz

# 2. Cleanup old logs
find /var/log -name "*.log" -mtime +30 -delete

# 3. Review user activity
docker logs shortchain-api-prod | grep "POST /api/v1/extract" | wc -l

# 4. Check certificate expiry
openssl s_client -connect your-domain.com:443 2>/dev/null | openssl x509 -noout -dates
```

### Monthly Tasks

```bash
# 1. Security updates
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d

# 2. Database vacuum
docker exec shortchain-db-prod psql -U prod_user -d shortchain_prod -c "VACUUM ANALYZE;"

# 3. Review access logs
docker logs shortchain-nginx-prod | grep " 401 " | wc -l

# 4. Performance review
# Check average processing times from metrics
```

### Quarterly Tasks

```bash
# 1. Full system backup
docker-compose -f docker-compose.prod.yml down
docker run --rm -v shortchain_prod_data:/data -v $(pwd):/backup alpine tar czf /backup/full_backup.tar.gz /data
docker-compose -f docker-compose.prod.yml up -d

# 2. Security audit
# Review all users, API keys, access logs

# 3. Capacity planning
# Review growth trends, plan upgrades

# 4. Documentation update
# Update runbooks, procedures
```

## Database Management

### Connection Pool

```sql
-- Check connections
SELECT count(*) FROM pg_stat_activity;

-- Terminate idle connections
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE state = 'idle' AND query_start < NOW() - INTERVAL '30 minutes';
```

### Performance Tuning

```sql
-- Enable slow query logging
ALTER SYSTEM SET log_min_duration_statement = 1000;

-- Analyze table statistics
ANALYZE extractions;
ANALYZE products;

-- Rebuild indexes
REINDEX TABLE extractions;
```

### Migration Guide

```bash
# 1. Backup current database
pg_dump -U prod_user shortchain_prod > migration_backup.sql

# 2. Apply migrations
docker exec shortchain-db-prod psql -U prod_user -d shortchain_prod < new_schema.sql

# 3. Verify
docker exec shortchain-db-prod psql -U prod_user -d shortchain_prod -c "SELECT count(*) FROM extractions;"

# 4. Test application
curl http://localhost:8000/health
```

## Disaster Recovery

### Full System Restore

```bash
# 1. Stop services
docker-compose -f docker-compose.prod.yml down

# 2. Restore database
gunzip < backups/latest.sql.gz | docker exec -i shortchain-db-prod psql -U prod_user -d shortchain_prod

# 3. Restore files
tar xzf backups/files_latest.tar.gz -C /app/data

# 4. Restart services
docker-compose -f docker-compose.prod.yml up -d

# 5. Verify
curl http://localhost:8000/health
docker exec shortchain-db-prod pg_isready
```

### Partial Restore

```bash
# Restore single table
pg_restore -U prod_user -d shortchain_prod -t extractions backups/latest.sql

# Restore specific row
docker exec -i shortchain-db-prod psql -U prod_user -d shortchain_prod <<EOF
DELETE FROM extractions WHERE id = 'problematic_id';
COMMIT;
EOF
```

## Security Hardening

### Firewall Rules

```bash
# Allow only necessary ports
ufw allow 443/tcp  # HTTPS
ufw allow 22/tcp   # SSH (restricted IPs)
ufw deny 5432/tcp  # Database (internal only)
ufw enable
```

### SSL/TLS Configuration

```nginx
# nginx.conf
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
ssl_prefer_server_ciphers on;
```

### Audit Logging

```bash
# Enable query logging
docker exec shortchain-db-prod psql -U prod_user -d shortchain_prod \
  -c "ALTER SYSTEM SET log_statement = 'all';"

# Review logs
docker logs shortchain-db-prod | grep "LOG:"
```

## Contact & Escalation

| Issue Type | Contact | Response Time |
|------------|---------|---------------|
| Service Down | oncall@company.com | 15 minutes |
| Security Incident | security@company.com | 1 hour |
| Data Loss | dba@company.com | 1 hour |
| Feature Request | product@company.com | 1 week |
