# Kerykeion Deployment Guide

This guide covers the complete deployment and configuration of Kerykeion astrological library for the Astroloh project.

## Overview

Kerykeion is the primary astrological calculation engine for Astroloh, providing:
- High-precision natal chart calculations
- Advanced aspect analysis
- Multiple house systems support
- SVG chart generation
- Secondary progressions and returns
- Synastry and compatibility analysis

## Prerequisites

### System Requirements

#### Docker Environment (Recommended)
- Docker 24.0+ with Docker Compose v2
- 4GB+ RAM available
- 10GB+ disk space

#### Local Environment
- Python 3.12+
- GCC/G++ compiler
- System libraries: `libffi-dev`, `libc6-dev`, `libswe-dev`

### Dependencies

Kerykeion requires the following key dependencies:
- **Kerykeion 4.26.0+**: Main astrological library
- **pyswisseph 2.10.3.2**: Swiss Ephemeris bindings
- **pydantic 1.10.12+**: Data validation
- **pytz**: Timezone handling

## Installation Methods

### 1. Automated Setup (Recommended)

Use the provided setup script for automated installation:

```bash
# For Docker environment
python scripts/setup_kerykeion.py --docker

# For local environment
python scripts/setup_kerykeion.py

# Force reinstallation
python scripts/setup_kerykeion.py --force

# Validate installation only
python scripts/setup_kerykeion.py --validate
```

### 2. Manual Installation

#### Using uv (Recommended)
```bash
# Install with full dependencies
uv pip install -e ".[full]"

# Or install specific packages
uv pip install kerykeion>=4.26.0 pyswisseph==2.10.3.2
```

#### Using pip
```bash
# Install with full dependencies
pip install -e ".[full]"

# Or install specific packages
pip install kerykeion>=4.26.0 pyswisseph==2.10.3.2
```

### 3. Docker Installation

The project includes a specialized Dockerfile for Kerykeion:

```bash
# Build Kerykeion-enabled container
docker build -f Dockerfile.kerykeion -t astroloh-kerykeion .

# Or use Docker Compose
docker-compose -f docker-compose.kerykeion.yml up --build
```

## Configuration

### Environment Variables

Set the following environment variables:

```bash
# Enable Kerykeion features
KERYKEION_ENABLED=true
SWISSEPH_ENABLED=true

# Swiss Ephemeris path
SWISS_EPHEMERIS_PATH=/app/swisseph

# Optional: Custom ephemeris files
SWISSEPH_EPHEMERIS_PATH=/app/swisseph/ephemeris
```

### Directory Structure

Ensure the following directories exist:

```
/app/
├── swisseph/          # Swiss Ephemeris files
├── logs/             # Application logs
└── tmp/              # Temporary files
```

## Deployment Process

### 1. Pre-deployment Validation

Always validate Kerykeion installation before deployment:

```bash
# Validate installation
python scripts/deploy_kerykeion.py --validate

# Or use setup script
python scripts/setup_kerykeion.py --validate
```

### 2. Phased Deployment

The deployment system uses a phased rollout approach:

```bash
# Full automated deployment
python scripts/deploy_kerykeion.py --auto-advance

# Dry run (simulate without changes)
python scripts/deploy_kerykeion.py --dry-run

# Start from specific phase
python scripts/deploy_kerykeion.py --phase phase_2

# Check current status
python scripts/deploy_kerykeion.py --status
```

### 3. Deployment Phases

#### Phase 1 (5% users, 2h monitoring)
- Basic natal chart calculations
- Synastry analysis
- Performance optimization

#### Phase 2 (20% users, 4h monitoring)
- Transit calculations
- Secondary progressions

#### Phase 3 (50% users, 8h monitoring)
- Enhanced compatibility analysis
- AI-powered consultations

#### Full Deployment (100% users, 12h monitoring)
- Complete Russian localization
- All advanced features

## Monitoring and Health Checks

### Real-time Monitoring

Access deployment dashboard:
```bash
# Local development
curl http://localhost:8000/api/v1/deployment/status

# Production
curl https://your-domain.com/api/v1/deployment/status
```

### Health Metrics

The system monitors:
- **Response Time**: < 3s for Alice voice interface
- **Error Rate**: < 5% threshold
- **Fallback Usage**: < 25% Kerykeion fallback rate
- **User Satisfaction**: > 7/10 score

### Performance Monitoring

```bash
# Get performance report
curl http://localhost:8000/api/v1/deployment/performance-report

# Get health checks
curl http://localhost:8000/api/v1/deployment/health-checks
```

## Troubleshooting

### Common Issues

#### 1. Kerykeion Import Error
```bash
# Error: ModuleNotFoundError: No module named 'kerykeion'
python scripts/setup_kerykeion.py --force
```

#### 2. Swiss Ephemeris Compilation Error
```bash
# Install system dependencies
sudo apt-get install gcc g++ pkg-config libffi-dev libc6-dev libswe-dev

# Reinstall pyswisseph
pip uninstall pyswisseph
pip install pyswisseph==2.10.3.2
```

#### 3. Memory Issues
```bash
# Check memory usage
docker stats

# Increase Docker memory limit
docker run --memory=4g astroloh-kerykeion
```

#### 4. Performance Issues
```bash
# Check Kerykeion performance
python scripts/deploy_kerykeion.py --status

# Monitor response times
curl http://localhost:8000/api/v1/deployment/performance-report
```

### Emergency Rollback

If issues occur during deployment:

```bash
# Emergency rollback all features
python scripts/deploy_kerykeion.py --rollback

# Rollback specific features
python scripts/deploy_kerykeion.py --rollback --features kerykeion_transits kerykeion_progressions
```

## Testing

### Unit Tests

```bash
# Run Kerykeion-specific tests
pytest tests/ -m kerykeion

# Run all tests
pytest tests/

# Performance tests
pytest tests/ -m performance
```

### Integration Tests

```bash
# Test Kerykeion service
python -c "
from app.services.kerykeion_service import KerykeionService
service = KerykeionService()
print(f'Kerykeion available: {service.is_available()}')
print(f'Service capabilities: {service.get_service_capabilities()}')
"
```

### Load Testing

```bash
# Test Kerykeion performance under load
python scripts/test_kerykeion_performance.py

# Monitor during load test
python scripts/deploy_kerykeion.py --status
```

## Production Considerations

### Performance Optimization

1. **Caching**: Enable Redis caching for chart calculations
2. **Async Processing**: Use async Kerykeion service for better performance
3. **Resource Limits**: Monitor memory and CPU usage
4. **Connection Pooling**: Optimize database connections

### Security

1. **Input Validation**: Validate all birth data inputs
2. **Rate Limiting**: Implement rate limits for chart calculations
3. **Error Handling**: Graceful fallback to basic calculations
4. **Logging**: Comprehensive logging for debugging

### Monitoring

1. **Health Checks**: Regular health check endpoints
2. **Metrics**: Track response times and error rates
3. **Alerts**: Set up alerts for performance degradation
4. **Logs**: Monitor application logs for issues

## Maintenance

### Regular Tasks

1. **Update Kerykeion**: Check for new versions monthly
2. **Ephemeris Updates**: Update Swiss Ephemeris files quarterly
3. **Performance Review**: Weekly performance analysis
4. **Backup**: Regular backup of configuration and data

### Updates

```bash
# Update Kerykeion
pip install --upgrade kerykeion

# Update Swiss Ephemeris
pip install --upgrade pyswisseph

# Validate after update
python scripts/setup_kerykeion.py --validate
```

## Support

### Documentation

- [Kerykeion Documentation](https://kerykeion.readthedocs.io/)
- [Swiss Ephemeris Documentation](https://www.astro.com/swisseph/)
- [Astroloh API Reference](docs/API_REFERENCE.md)

### Logs

Check logs for detailed information:
```bash
# Application logs
tail -f logs/astroloh.log

# Docker logs
docker logs astroloh-backend

# Kerykeion-specific logs
grep "KERYKEION" logs/astroloh.log
```

### Getting Help

1. Check the troubleshooting section above
2. Review application logs
3. Run validation scripts
4. Check deployment status
5. Contact support with detailed error information

## Conclusion

Kerykeion is essential for Astroloh's advanced astrological features. Follow this guide to ensure proper installation, configuration, and deployment. Regular monitoring and maintenance will ensure optimal performance and reliability.