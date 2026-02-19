# 🚀 Deployment Guide - Club Management SaaS

Complete guide for deploying the multi-tenant SaaS platform to production.

## 📋 Table of Contents
1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Docker Deployment](#docker-deployment)
4. [Cloud Deployment](#cloud-deployment)
5. [Database Setup](#database-setup)
6. [Security Checklist](#security-checklist)
7. [Monitoring](#monitoring)
8. [Backup Strategy](#backup-strategy)

---

## 🔧 Prerequisites

### Required Software
- Docker 20.10+
- Docker Compose 2.0+
- PostgreSQL 15+ (if not using Docker)
- Python 3.11+ (for local development)

### Required Accounts (for cloud deployment)
- Domain name (recommended)
- SSL certificate (Let's Encrypt recommended)
- Cloud provider account (AWS/GCP/DigitalOcean/Azure)

---

## 🌍 Environment Setup

### 1. Clone Repository
```bash
git clone https://github.com/EESSE52/cuociente_canotaje_app.git
cd cuociente_canotaje_app/backend
```

### 2. Create Production Environment File
```bash
cp .env.example .env
```

### 3. Configure Environment Variables

Edit `.env` with production values:

```bash
# Application
APP_NAME=Club Management SaaS
DEBUG=False

# Database (use strong password!)
DATABASE_URL=postgresql://club_admin:CHANGE_THIS_PASSWORD@db:5432/club_management

# Security (MUST CHANGE!)
SECRET_KEY=generate-a-strong-random-key-min-32-characters-use-openssl-rand-base64-32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS (adjust for your frontend domain)
CORS_ORIGINS=["https://yourdomain.com","https://app.yourdomain.com"]

# Redis
REDIS_URL=redis://redis:6379/0

# Email (configure your SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@yourdomain.com
```

### 4. Generate Secure SECRET_KEY
```bash
# Use OpenSSL to generate random key
openssl rand -base64 32
```

---

## 🐳 Docker Deployment

### Local/Development Deployment

#### 1. Build and Start Services
```bash
docker-compose up -d
```

This starts:
- PostgreSQL database (port 5432)
- Redis cache (port 6379)
- FastAPI backend (port 8000)

#### 2. Initialize Database
```bash
# Wait for services to be healthy
docker-compose ps

# Initialize database
docker-compose exec backend python scripts/init_db.py
```

#### 3. Verify Deployment
```bash
# Check logs
docker-compose logs -f backend

# Test API
curl http://localhost:8000/health
```

Access API documentation: http://localhost:8000/api/docs

### Production Docker Deployment

#### 1. Update docker-compose.yml for Production

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    container_name: club_db_prod
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: club_management
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    restart: always
    networks:
      - app-network

  redis:
    image: redis:7-alpine
    container_name: club_redis_prod
    restart: always
    networks:
      - app-network
    command: redis-server --requirepass ${REDIS_PASSWORD}

  backend:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: club_backend_prod
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/club_management
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
      SECRET_KEY: ${SECRET_KEY}
      DEBUG: "False"
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    restart: always
    networks:
      - app-network

  nginx:
    image: nginx:alpine
    container_name: club_nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - backend
    restart: always
    networks:
      - app-network

networks:
  app-network:
    driver: bridge

volumes:
  postgres_data:
```

#### 2. Create Nginx Configuration

Create `nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=60r/m;

    server {
        listen 80;
        server_name yourdomain.com www.yourdomain.com;
        
        # Redirect HTTP to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name yourdomain.com www.yourdomain.com;

        # SSL Configuration
        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;

        # API endpoints
        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;
            
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Health check
        location /health {
            proxy_pass http://backend;
        }

        # Static files (for future frontend)
        location / {
            root /usr/share/nginx/html;
            index index.html;
            try_files $uri $uri/ /index.html;
        }
    }
}
```

#### 3. Deploy with SSL

```bash
# Get SSL certificate with certbot
docker run -it --rm \
  -v $(pwd)/ssl:/etc/letsencrypt \
  certbot/certbot certonly --standalone \
  -d yourdomain.com -d www.yourdomain.com \
  --email your-email@example.com \
  --agree-tos --non-interactive

# Copy certificates
cp ssl/live/yourdomain.com/fullchain.pem ssl/
cp ssl/live/yourdomain.com/privkey.pem ssl/

# Start production stack
docker-compose -f docker-compose.prod.yml up -d
```

---

## ☁️ Cloud Deployment

### AWS Deployment

#### Using ECS (Elastic Container Service)

1. **Create ECR Repository**
```bash
aws ecr create-repository --repository-name club-management-backend
```

2. **Build and Push Image**
```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin YOUR_ECR_URL

# Build and tag
docker build -t club-management-backend .
docker tag club-management-backend:latest YOUR_ECR_URL/club-management-backend:latest

# Push
docker push YOUR_ECR_URL/club-management-backend:latest
```

3. **Create RDS PostgreSQL Instance**
- Engine: PostgreSQL 15
- Instance class: db.t3.medium (adjust as needed)
- Storage: 100 GB (with auto-scaling)
- Multi-AZ: Yes (for production)
- Backup: 7-day retention

4. **Create ECS Cluster**
- Launch type: Fargate
- Create task definition with environment variables
- Create service with load balancer
- Configure auto-scaling

5. **Setup Application Load Balancer**
- Target group: ECS service
- Health check: /health
- SSL/TLS certificate: Use ACM

### DigitalOcean Deployment

#### Using App Platform

1. **Connect GitHub Repository**
```bash
# Go to DigitalOcean App Platform
# Click "Create App"
# Select GitHub repository
```

2. **Configure App**
```yaml
name: club-management
services:
  - name: backend
    github:
      repo: EESSE52/cuociente_canotaje_app
      branch: main
      deploy_on_push: true
    build_command: pip install -r backend/requirements.txt
    run_command: uvicorn app.main:app --host 0.0.0.0 --port 8000
    envs:
      - key: DATABASE_URL
        value: ${db.DATABASE_URL}
      - key: SECRET_KEY
        type: SECRET

databases:
  - name: db
    engine: PG
    version: "15"
    size: db-s-1vcpu-1gb
```

3. **Add Managed Database**
- PostgreSQL 15
- Choose plan based on expected load

4. **Configure Environment Variables**
- Set all required variables from .env
- Use DO's secret management

5. **Deploy**
```bash
# App Platform will auto-deploy
# Access via provided URL
```

### Google Cloud Deployment

#### Using Cloud Run

1. **Build and Push to GCR**
```bash
# Configure gcloud
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Build and push
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/club-management-backend

# Deploy
gcloud run deploy club-management-backend \
  --image gcr.io/YOUR_PROJECT_ID/club-management-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL=$DATABASE_URL,SECRET_KEY=$SECRET_KEY
```

2. **Create Cloud SQL Instance**
```bash
gcloud sql instances create club-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1

# Create database
gcloud sql databases create club_management --instance=club-db
```

---

## 🗄️ Database Setup

### Initial Setup

```bash
# Using Docker
docker-compose exec backend python scripts/init_db.py

# Or directly with psql
psql $DATABASE_URL < schema.sql
python scripts/init_db.py
```

### Migrations with Alembic

```bash
# Initialize Alembic (first time only)
alembic init alembic

# Generate migration
alembic revision --autogenerate -m "Initial schema"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Database Optimization

Add indexes for performance:

```sql
-- Club-based queries
CREATE INDEX idx_members_club_status ON members(club_id, status);
CREATE INDEX idx_fees_club_status ON generated_fees(club_id, status);
CREATE INDEX idx_payments_club_date ON payments(club_id, payment_date DESC);

-- Date-based queries
CREATE INDEX idx_fees_due_date ON generated_fees(due_date) WHERE status IN ('pending', 'overdue');
CREATE INDEX idx_events_date ON events(event_date) WHERE is_active = true;
```

---

## 🔒 Security Checklist

### Pre-Deployment

- [ ] Change all default passwords
- [ ] Generate strong SECRET_KEY (min 32 chars)
- [ ] Update CORS_ORIGINS to production domains
- [ ] Disable DEBUG mode
- [ ] Review and update .gitignore
- [ ] Scan for secrets in code
- [ ] Update database credentials

### Application Security

- [ ] Enable HTTPS/SSL
- [ ] Configure rate limiting
- [ ] Enable security headers (CSP, HSTS, etc.)
- [ ] Set up Web Application Firewall (WAF)
- [ ] Configure IP whitelisting (if needed)
- [ ] Enable audit logging
- [ ] Set up intrusion detection

### Database Security

- [ ] Use strong database password
- [ ] Enable SSL connections
- [ ] Restrict database access by IP
- [ ] Enable query logging
- [ ] Set up automated backups
- [ ] Configure point-in-time recovery
- [ ] Encrypt sensitive data

### Network Security

- [ ] Use private networks for services
- [ ] Configure firewall rules
- [ ] Enable DDoS protection
- [ ] Set up VPN for admin access
- [ ] Regular security audits

---

## 📊 Monitoring

### Application Monitoring

#### Setup Health Checks

```python
# Already implemented in /health endpoint
# Monitor:
# - Database connectivity
# - Redis connectivity
# - Application responsiveness
```

#### Logging

Use structured logging:

```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

#### Error Tracking

Integrate Sentry:

```bash
pip install sentry-sdk[fastapi]
```

```python
import sentry_sdk
sentry_sdk.init(dsn="your-sentry-dsn")
```

### Database Monitoring

Monitor:
- Connection pool usage
- Query performance
- Slow queries
- Database size
- Transaction rate

Tools:
- pgAdmin
- DataDog
- New Relic
- AWS CloudWatch (for RDS)

### Infrastructure Monitoring

Use:
- Prometheus + Grafana
- AWS CloudWatch
- DigitalOcean Monitoring
- Google Cloud Monitoring

Key metrics:
- CPU usage
- Memory usage
- Disk I/O
- Network traffic
- Request latency
- Error rates

---

## 💾 Backup Strategy

### Database Backups

#### Automated Backups

```bash
# Create backup script: backup.sh
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
docker-compose exec -T db pg_dump -U club_admin club_management | \
  gzip > "$BACKUP_DIR/backup_$DATE.sql.gz"

# Keep only last 7 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete
```

#### Schedule with cron

```cron
# Daily backup at 2 AM
0 2 * * * /path/to/backup.sh
```

### Application Backups

- Code: Use Git with remote repository
- Configuration: Version control .env templates
- Uploads: Sync to S3/Cloud Storage
- Logs: Centralized logging service

### Disaster Recovery

1. **Regular testing**
   - Test restore process monthly
   - Document restore procedures
   - Keep offline backups

2. **Geographic redundancy**
   - Cross-region backups
   - Multi-zone deployment
   - CDN for static assets

3. **Recovery Time Objective (RTO)**
   - Target: < 4 hours
   - Automated restore scripts
   - Failover procedures

---

## 🔄 Continuous Deployment

### GitHub Actions CI/CD

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      
      - name: Run tests
        run: |
          cd backend
          pytest
      
      - name: Build Docker image
        run: |
          cd backend
          docker build -t club-management-backend .
      
      - name: Deploy to production
        run: |
          # Add your deployment commands here
          # e.g., push to ECR, update ECS service
```

---

## 📝 Post-Deployment

### Verify Deployment

```bash
# Health check
curl https://yourdomain.com/health

# API docs
open https://yourdomain.com/api/docs

# Test login
curl -X POST https://yourdomain.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@clubmanagement.com","password":"YOUR_PASSWORD"}'
```

### Change Default Credentials

```bash
# Login as SuperAdmin
# Navigate to user management
# Change password immediately
```

### Configure Monitoring Alerts

Set up alerts for:
- High error rates
- Slow responses
- Database issues
- High CPU/memory usage
- Failed backups

---

## 📞 Support

For deployment issues:
- GitHub Issues: [Create Issue](https://github.com/EESSE52/cuociente_canotaje_app/issues)
- Email: support@clubmanagement.com
- Documentation: See README.md and ARCHITECTURE.md

---

**Deployment checklist complete! ✅**

Last updated: 2026-02-19
