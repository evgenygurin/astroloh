# Deployment Guide

- Use Docker Compose. See `docs/DOCKER_DEPLOYMENT.md` for detailed commands.
- Expose webhook via ngrok for Yandex Dialogs testing. See `docs/NGROK_SETUP.md`.
- Set production env: `DEBUG=false`, strong `SECRET_KEY`, DB creds, Redis URL.

## Overview

This guide covers complete production deployment of Astroloh, including environment setup, configuration, security hardening, monitoring, and maintenance procedures.

## Prerequisites

### System Requirements

#### Minimum Hardware
- **CPU**: 2 cores (4 recommended)
- **RAM**: 4GB (8GB recommended)
- **Storage**: 20GB SSD (50GB recommended)
- **Network**: 1Gbps connection

#### Optimal Production Hardware
- **CPU**: 4-8 cores
- **RAM**: 16-32GB
- **Storage**: 100GB+ SSD with backup
- **Network**: High-speed connection with redundancy

#### Software Requirements
- **OS**: Ubuntu 22.04 LTS, CentOS 8+, or Debian 11+ (recommended)
- **Docker**: 24.0+ with Docker Compose v2
- **Python**: 3.11+ (if not using Docker)
- **PostgreSQL**: 15+ (if not using Docker)
- **Redis**: 7+ (if not using Docker)
- **Nginx**: 1.20+ (reverse proxy)
- **SSL Certificate**: Let's Encrypt or commercial

## Environment Variables

### Required Environment Variables

Create a production `.env` file with the following variables:

```bash
# === Core Application Settings ===
DEBUG=false
SECRET_KEY=your-secret-key-here-minimum-32-characters
ENCRYPTION_KEY=your-encryption-key-here-32-bytes-base64

# === Database Configuration ===
DATABASE_URL=postgresql+asyncpg://astroloh_user:secure_password@db:5432/astroloh_db
POSTGRES_USER=astroloh_user
POSTGRES_PASSWORD=secure_password_here
POSTGRES_DB=astroloh_db

# === Redis Cache Configuration ===
REDIS_URL=redis://redis:6379/0
REDIS_PASSWORD=your-redis-password

# === Yandex API Configuration ===
YANDEX_API_KEY=your-yandex-gpt-api-key
YANDEX_FOLDER_ID=your-yandex-cloud-folder-id
YANDEX_CATALOG_ID=your-yandex-catalog-id
ENABLE_AI_GENERATION=true

# === External Integrations ===
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
GOOGLE_CREDENTIALS_PATH=/app/config/google-credentials.json

# === Performance & Monitoring ===
SENTRY_DSN=your-sentry-dsn-for-error-tracking
LOG_LEVEL=INFO
ENABLE_PERFORMANCE_MONITORING=true
PERFORMANCE_ALERT_THRESHOLD_MS=2000

# === Security Settings ===
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
RATE_LIMIT_PER_MINUTE=100
ENABLE_SECURITY_HEADERS=true

# === Feature Flags ===
ENABLE_KERYKEION=true
ENABLE_CACHE_WARMUP=true
ENABLE_BACKGROUND_MONITORING=true
ENABLE_PRECOMPUTATION=true

# === GDPR Compliance ===
DATA_RETENTION_DAYS=365
ENABLE_GDPR_COMPLIANCE=true
GDPR_CONTACT_EMAIL=privacy@yourdomain.com

# === SSL/TLS Configuration ===
USE_SSL=true
SSL_CERT_PATH=/etc/ssl/certs/yourdomain.pem
SSL_KEY_PATH=/etc/ssl/private/yourdomain.key
```

### Environment Variable Security

⚠️ **Critical Security Requirements**:

1. **Never commit `.env` files to version control**
2. **Use strong, unique passwords (minimum 32 characters)**
3. **Generate SECRET_KEY with cryptographic randomness**:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
4. **Generate ENCRYPTION_KEY properly**:
   ```bash
   python -c "import base64; import os; print(base64.b64encode(os.urandom(32)).decode())"
   ```

## Production Docker Deployment

### Production docker-compose.yml

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  # Backend service
  backend:
    build:
      context: .
      dockerfile: Dockerfile.prod
    ports:
      - "127.0.0.1:8000:8000"  # Bind to localhost only
    environment:
      - DEBUG=false
      - DATABASE_URL=postgresql+asyncpg://astroloh_user:${POSTGRES_PASSWORD}@db:5432/astroloh_db
      - REDIS_URL=redis://redis:6379/0
      - YANDEX_API_KEY=${YANDEX_API_KEY}
      - YANDEX_FOLDER_ID=${YANDEX_FOLDER_ID}
      - YANDEX_CATALOG_ID=${YANDEX_CATALOG_ID}
      - SECRET_KEY=${SECRET_KEY}
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}
      - LOG_LEVEL=INFO
      - ENABLE_AI_GENERATION=${ENABLE_AI_GENERATION}
      - ENABLE_KERYKEION=${ENABLE_KERYKEION}
      - SENTRY_DSN=${SENTRY_DSN}
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - astroloh-network
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # Frontend service  
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    ports:
      - "127.0.0.1:3000:80"  # Bind to localhost only
    depends_on:
      - backend
    restart: unless-stopped
    environment:
      - NODE_ENV=production
    networks:
      - astroloh-network
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # Database service with backup
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_INITDB_ARGS: "--auth-host=scram-sha-256"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
      - ./init-scripts:/docker-entrypoint-initdb.d
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - astroloh-network
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    command: >
      postgres 
      -c log_statement=all
      -c log_duration=on
      -c log_min_duration_statement=1000
      -c max_connections=100
      -c shared_preload_libraries=pg_stat_statements

  # Redis cache with persistence
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
      - ./redis.conf:/usr/local/etc/redis/redis.conf
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - astroloh-network
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    command: redis-server /usr/local/etc/redis/redis.conf --appendonly yes

  # Nginx reverse proxy
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/conf.d:/etc/nginx/conf.d
      - ./ssl:/etc/nginx/ssl
      - nginx_logs:/var/log/nginx
    depends_on:
      - backend
      - frontend
    restart: unless-stopped
    networks:
      - astroloh-network
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # Monitoring with Prometheus
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "127.0.0.1:9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    restart: unless-stopped
    networks:
      - astroloh-network

  # Grafana for visualization
  grafana:
    image: grafana/grafana:latest
    ports:
      - "127.0.0.1:3001:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana:/etc/grafana/provisioning
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    restart: unless-stopped
    networks:
      - astroloh-network

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  nginx_logs:
    driver: local
  prometheus_data:
    driver: local
  grafana_data:
    driver: local

networks:
  astroloh-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### Production Dockerfile

Create `Dockerfile.prod`:

```dockerfile
FROM python:3.11-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim

# Create non-root user
RUN groupadd -r astroloh && useradd --no-log-init -r -g astroloh astroloh

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /home/astroloh/.local

# Copy application code
COPY . .

# Set ownership and permissions
RUN chown -R astroloh:astroloh /app
RUN chmod +x /app/scripts/*.sh

# Switch to non-root user
USER astroloh

# Set environment variables
ENV PATH=/home/astroloh/.local/bin:$PATH
ENV PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

## Nginx Configuration

### Main nginx.conf

```nginx
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for" '
                    'rt=$request_time uct="$upstream_connect_time" '
                    'uht="$upstream_header_time" urt="$upstream_response_time"';

    access_log /var/log/nginx/access.log main;

    # Performance optimizations
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 16M;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 10240;
    gzip_proxied expired no-cache no-store private auth;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/x-javascript
        application/javascript
        application/xml+rss
        application/json;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/m;

    # Include additional configurations
    include /etc/nginx/conf.d/*.conf;
}
```

### Site configuration (astroloh.conf)

```nginx
# Upstream backends
upstream backend {
    server backend:8000;
    keepalive 32;
}

upstream frontend {
    server frontend:80;
    keepalive 32;
}

# HTTP redirect to HTTPS
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Let's Encrypt ACME challenge
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    # Redirect all other traffic to HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
}

# Main HTTPS server
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/yourdomain.crt;
    ssl_certificate_key /etc/nginx/ssl/yourdomain.key;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;

    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:;" always;

    # API endpoints
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 5s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buffering
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
        proxy_max_temp_file_size 1024m;
        
        # Health check endpoint
        location /api/v1/yandex/webhook {
            limit_req zone=api burst=50 nodelay;
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }

    # Health check (no rate limiting)
    location /health {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        access_log off;
    }

    # Static files and frontend
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Caching for static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
            access_log off;
            proxy_pass http://frontend;
        }
    }

    # Security: Block access to sensitive files
    location ~ /\. {
        deny all;
        access_log off;
    }

    location ~ /_(.*) {
        deny all;
        access_log off;
    }
}
```

## SSL/TLS Setup with Let's Encrypt

### Automated SSL Certificate Setup

1. **Install Certbot**:
```bash
sudo apt update
sudo apt install certbot python3-certbot-nginx
```

2. **Obtain SSL Certificate**:
```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

3. **Auto-renewal Setup**:
```bash
sudo crontab -e
# Add this line for automatic renewal
0 12 * * * /usr/bin/certbot renew --quiet
```

4. **Verify Auto-renewal**:
```bash
sudo certbot renew --dry-run
```

## Database Configuration

### PostgreSQL Production Settings

Create `init-scripts/01-init.sql`:

```sql
-- Create additional indexes for performance
CREATE INDEX CONCURRENTLY idx_users_yandex_user_id ON users(yandex_user_id);
CREATE INDEX CONCURRENTLY idx_user_sessions_session_id ON user_sessions(session_id);
CREATE INDEX CONCURRENTLY idx_user_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX CONCURRENTLY idx_horoscope_requests_processed_at ON horoscope_requests(processed_at);
CREATE INDEX CONCURRENTLY idx_security_logs_timestamp ON security_logs(timestamp);

-- Enable pg_stat_statements for query monitoring
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Create read-only user for monitoring
CREATE USER astroloh_monitoring WITH PASSWORD 'monitoring_password_here';
GRANT CONNECT ON DATABASE astroloh_db TO astroloh_monitoring;
GRANT USAGE ON SCHEMA public TO astroloh_monitoring;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO astroloh_monitoring;
```

### Database Backup Strategy

Create `scripts/backup-db.sh`:

```bash
#!/bin/bash
set -e

# Configuration
BACKUP_DIR="/backups"
DB_NAME="astroloh_db"
DB_USER="astroloh_user"
RETENTION_DAYS=30

# Create backup directory
mkdir -p $BACKUP_DIR

# Generate backup filename
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/astroloh_backup_$TIMESTAMP.sql.gz"

# Perform backup
echo "Starting database backup..."
PGPASSWORD=$POSTGRES_PASSWORD pg_dump -h db -U $DB_USER -d $DB_NAME | gzip > $BACKUP_FILE

# Verify backup
if [ -s "$BACKUP_FILE" ]; then
    echo "Backup completed successfully: $BACKUP_FILE"
    
    # Calculate backup size
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "Backup size: $SIZE"
    
    # Remove old backups
    find $BACKUP_DIR -name "astroloh_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete
    echo "Cleaned up backups older than $RETENTION_DAYS days"
else
    echo "ERROR: Backup failed!"
    exit 1
fi
```

### Redis Configuration

Create `redis.conf`:

```
# Network security
bind 127.0.0.1
protected-mode yes
port 6379

# Memory management
maxmemory 1gb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfsync everysec

# Security
requirepass your-redis-password-here

# Logging
loglevel notice
logfile "/var/log/redis/redis-server.log"

# Performance
tcp-keepalive 300
timeout 0
databases 16
```

## Monitoring and Logging

### Prometheus Configuration

Create `monitoring/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "rules/*.yml"

scrape_configs:
  - job_name: 'astroloh-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'postgres'
    static_configs:
      - targets: ['db:5432']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx:80']

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

### Grafana Dashboard Configuration

Create `monitoring/grafana/dashboards/astroloh.json` with key metrics:
- Request rates and response times
- Database connection pool usage
- Cache hit rates
- Error rates by endpoint
- System resource usage (CPU, memory, disk)
- Astrological service performance

## Security Hardening

### Application Security

1. **Environment Variable Security**:
   - Never log sensitive environment variables
   - Use secrets management for production
   - Rotate keys regularly

2. **Database Security**:
   - Use connection pooling with limits
   - Enable query logging for audit
   - Regular security updates

3. **Redis Security**:
   - Enable password authentication
   - Bind to localhost only
   - Use TLS for external connections

### System Security

1. **Firewall Configuration**:
```bash
# Ubuntu UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp     # SSH
sudo ufw allow 80/tcp     # HTTP
sudo ufw allow 443/tcp    # HTTPS
sudo ufw enable
```

2. **SSH Hardening**:
```bash
# Disable root login
sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config

# Use key-based authentication only
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config

# Restart SSH service
sudo systemctl restart sshd
```

3. **System Updates**:
```bash
# Automated security updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure unattended-upgrades
```

## Deployment Process

### Initial Deployment

1. **Server Setup**:
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

2. **Application Deployment**:
```bash
# Clone repository
git clone https://github.com/yourusername/astroloh.git
cd astroloh

# Copy production configuration
cp .env.example .env
# Edit .env with production values

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Run database migrations
docker-compose exec backend alembic upgrade head

# Verify deployment
curl https://yourdomain.com/health
```

### Updates and Maintenance

1. **Application Updates**:
```bash
# Pull latest changes
git pull origin main

# Build and restart services
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Run any pending migrations
docker-compose exec backend alembic upgrade head
```

2. **Zero-downtime Deployment** (Blue-Green):
```bash
# Scale up new containers
docker-compose -f docker-compose.prod.yml up -d --scale backend=2

# Health check new containers
# Update load balancer to new containers
# Scale down old containers
```

## Troubleshooting

### Common Issues

1. **Environment Variables Not Loading**:
```bash
# Check Docker environment
docker-compose exec backend env | grep YANDEX_API_KEY

# Restart containers with new environment
docker-compose down && docker-compose up -d
```

2. **Database Connection Issues**:
```bash
# Check database status
docker-compose exec db pg_isready -U astroloh_user -d astroloh_db

# Check database logs
docker-compose logs db
```

3. **High Memory Usage**:
```bash
# Monitor memory usage
docker stats

# Check Redis memory usage
docker-compose exec redis redis-cli info memory
```

4. **SSL Certificate Issues**:
```bash
# Check certificate expiry
openssl x509 -in /path/to/cert.pem -text -noout | grep "Not After"

# Test SSL configuration
curl -I https://yourdomain.com/health
```

### Performance Optimization

1. **Database Query Optimization**:
```sql
-- Check slow queries
SELECT query, mean_exec_time, calls 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;
```

2. **Cache Performance**:
```bash
# Check Redis hit rate
docker-compose exec redis redis-cli info stats | grep keyspace
```

3. **Application Monitoring**:
```bash
# Check application metrics
curl http://localhost:8000/metrics
```

## Backup and Recovery

### Full System Backup

Create `scripts/full-backup.sh`:

```bash
#!/bin/bash
set -e

BACKUP_DATE=$(date +%Y%m%d)
BACKUP_DIR="/backups/full-$BACKUP_DATE"
mkdir -p $BACKUP_DIR

echo "Starting full system backup..."

# Database backup
./scripts/backup-db.sh

# Configuration backup
tar -czf $BACKUP_DIR/config-$BACKUP_DATE.tar.gz \
    .env docker-compose.prod.yml nginx/ monitoring/ ssl/

# Application data backup
tar -czf $BACKUP_DIR/volumes-$BACKUP_DATE.tar.gz \
    -C /var/lib/docker/volumes/ \
    astroloh_postgres_data astroloh_redis_data

echo "Full backup completed: $BACKUP_DIR"
```

### Disaster Recovery

1. **System Recovery**:
```bash
# Restore from backup
./scripts/restore-system.sh /backups/full-20250809

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Verify system health
curl https://yourdomain.com/health
```

2. **Database Recovery**:
```bash
# Restore database from backup
gunzip -c /backups/astroloh_backup_20250809.sql.gz | \
docker-compose exec -T db psql -U astroloh_user -d astroloh_db
```

This deployment guide provides comprehensive coverage of production deployment requirements, security considerations, and operational procedures for the Astroloh platform.

