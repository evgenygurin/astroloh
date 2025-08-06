# Docker Deployment Guide for Astroloh

This guide explains how to deploy the Astroloh application using Docker Compose, which includes both the backend (FastAPI) and frontend (React) services.

## Architecture Overview

The Docker setup includes three main services:

- **Frontend**: React application served by Nginx (port 80)
- **Backend**: FastAPI application (port 8000)
- **Database**: PostgreSQL 15 (port 5432)

## Prerequisites

- Docker Engine 20.10+
- Docker Compose v2.0+
- Make (optional, for using Makefile commands)

## Quick Start

### 1. Clone the repository

```bash
git clone <repository-url>
cd astroloh
```

### 2. Set up environment variables

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Start the application

**For Development (with hot reload):**

```bash
make docker-dev
```

Or without Make:

```bash
docker-compose -f docker-compose.dev.yml up
```

**For Production:**

```bash
make docker-prod
```

Or without Make:

```bash
docker-compose build
docker-compose up -d
```

## Available Commands

### Using Make (recommended)

```bash
# Development
make docker-dev      # Start development environment with hot reload
make docker-down     # Stop all services

# Production
make docker-prod     # Build and start production environment
make docker-up       # Start production services
make docker-down     # Stop all services

# Maintenance
make docker-build    # Build Docker images
make docker-rebuild  # Rebuild images without cache
make docker-logs     # View service logs
```

### Using Docker Compose directly

```bash
# Development
docker-compose -f docker-compose.dev.yml up    # Start dev environment
docker-compose -f docker-compose.dev.yml down  # Stop dev environment

# Production
docker-compose build            # Build images
docker-compose up -d           # Start in background
docker-compose down            # Stop services
docker-compose logs -f         # View logs
docker-compose ps              # Check service status
```

## Access Points

### Development Mode

- Frontend: <http://localhost:3000> (with hot reload)
- Backend API: <http://localhost:8000>
- API Documentation: <http://localhost:8000/docs>
- PostgreSQL: localhost:5432

### Production Mode

- Frontend: <http://localhost> (port 80)
- Backend API: <http://localhost:8000>
- API Documentation: <http://localhost:8000/docs>
- PostgreSQL: localhost:5432

## Configuration

### Environment Variables

Key environment variables (see `.env.example` for full list):

```env
# Backend
DEBUG=true
DATABASE_URL=postgresql+asyncpg://astroloh_user:astroloh_password@db:5432/astroloh_db
SECRET_KEY=your-secret-key

# Frontend (production)
REACT_APP_API_URL=http://localhost:8000

# Database
POSTGRES_USER=astroloh_user
POSTGRES_PASSWORD=astroloh_password
POSTGRES_DB=astroloh_db
```

### Docker Networks

All services communicate through the `astroloh-network` bridge network:

- Frontend → Backend: <http://backend:8000>
- Backend → Database: postgresql://db:5432

## Development Workflow

1. **Frontend Development**
   - Code changes in `./frontend/src` are automatically reflected (hot reload)
   - Node modules are cached in a Docker volume

2. **Backend Development**
   - Code changes in `./app` trigger automatic reload via uvicorn
   - Database migrations are handled via Alembic

3. **Database Management**

   ```bash
   # Run migrations
   docker-compose exec backend alembic upgrade head
   
   # Create new migration
   docker-compose exec backend alembic revision --autogenerate -m "description"
   ```

## Production Deployment

### Building for Production

1. **Frontend**: Multi-stage build creates optimized static files served by Nginx
2. **Backend**: Python slim image with production dependencies only
3. **Security**: Non-root user, minimal attack surface

### Deployment Checklist

- [ ] Set `DEBUG=false` in production
- [ ] Generate secure `SECRET_KEY` and `ENCRYPTION_KEY`
- [ ] Configure proper database credentials
- [ ] Set up SSL/TLS certificates (use reverse proxy)
- [ ] Configure firewall rules
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy for PostgreSQL

### Scaling Considerations

- Frontend: Can be scaled horizontally behind a load balancer
- Backend: Stateless, can be scaled with multiple instances
- Database: Consider replication for high availability

## Troubleshooting

### Common Issues

1. **Port conflicts**

   ```bash
   # Check if ports are in use
   lsof -i :80
   lsof -i :3000
   lsof -i :8000
   lsof -i :5432
   ```

2. **Permission issues**

   ```bash
   # Fix frontend node_modules permissions
   docker-compose exec frontend-dev chown -R node:node /app/node_modules
   ```

3. **Database connection issues**

   ```bash
   # Check database logs
   docker-compose logs db
   
   # Test connection
   docker-compose exec db psql -U astroloh_user -d astroloh_db
   ```

### Debugging

```bash
# View all logs
make docker-logs

# View specific service logs
docker-compose logs -f frontend
docker-compose logs -f backend
docker-compose logs -f db

# Access container shell
docker-compose exec backend /bin/bash
docker-compose exec frontend-dev /bin/sh
```

## Maintenance

### Backup Database

```bash
docker-compose exec db pg_dump -U astroloh_user astroloh_db > backup.sql
```

### Restore Database

```bash
docker-compose exec -T db psql -U astroloh_user astroloh_db < backup.sql
```

### Clean Up

```bash
# Remove all containers and networks
docker-compose down

# Remove all data (including database)
docker-compose down -v

# Remove unused images
docker image prune -a
```

## Security Notes

1. Always use HTTPS in production (configure reverse proxy)
2. Keep Docker and all base images updated
3. Use secrets management for sensitive data
4. Implement rate limiting and CORS policies
5. Regular security audits of dependencies

## Support

For issues or questions:

1. Check the logs: `make docker-logs`
2. Review the troubleshooting section
3. Check Docker and Docker Compose versions
4. Ensure all required ports are available
