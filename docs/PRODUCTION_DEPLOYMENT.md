# Production Deployment System for Kerykeion Features

This document describes the comprehensive production deployment system implemented for rolling out Kerykeion astrological features in the Astroloh project.

## Overview

The deployment system provides:

- **Phased Rollout**: 5% → 20% → 50% → 100% user rollout
- **Real-time Monitoring**: Health checks, performance metrics, error tracking
- **Automatic Rollback**: Emergency rollback on critical failures
- **Manual Control**: API endpoints for deployment management
- **Circuit Breaker**: Protection against rollback loops

## Architecture Components

### 1. Feature Flag Service (`feature_flag_service.py`)

Manages phased rollout of features using consistent user hashing.

**Key Features:**
- Percentage-based rollout with consistent user assignment
- Manual feature enabling/disabling
- Emergency rollback capabilities
- State persistence with Redis/cache

**Usage:**
```python
from app.services.feature_flag_service import feature_flags, KerykeionFeatureFlags

# Check if feature is enabled for user
enabled = feature_flags.is_feature_enabled(
    KerykeionFeatureFlags.KERYKEION_NATAL_CHARTS,
    user_id="user_123"
)

# Update rollout percentage
feature_flags.update_feature_flag(
    "kerykeion_natal_charts",
    rollout_percentage=20.0
)
```

### 2. Deployment Monitor (`deployment_monitor.py`)

Monitors system health and deployment metrics.

**Monitored Metrics:**
- Response times (Alice voice interface <3s requirement)
- Error rates (<5% threshold)
- Kerykeion fallback usage (<25% threshold) 
- User satisfaction scores (>7/10 threshold)
- System resource usage

**Health Checks:**
- **Excellent**: All metrics optimal
- **Good**: Metrics within acceptable ranges
- **Warning**: Some metrics approaching thresholds
- **Critical**: Metrics exceeding thresholds (triggers rollback)
- **Failure**: System failure detected (emergency rollback)

### 3. Rollback System (`rollback_system.py`)

Automated rollback with multiple strategies.

**Rollback Strategies:**
- **Immediate**: Instant feature disable (30s)
- **Gradual**: Step-down rollout percentages (3.5h)
- **Feature-Specific**: Rollback problem features only (1.5h)
- **Full System**: Complete rollback with service restart (4h)

**Rollback Triggers:**
- High error rates (>10%)
- Slow response times (>5s)
- High fallback usage (>50%)
- System failures
- User complaints (satisfaction <5/10)

### 4. Deployment API (`api/deployment.py`)

REST API for deployment management and monitoring.

**Key Endpoints:**
- `GET /api/v1/deployment/status` - Deployment dashboard
- `GET /api/v1/deployment/features` - Feature flag status
- `PUT /api/v1/deployment/features/{name}` - Update feature
- `POST /api/v1/deployment/features/{name}/advance-phase` - Advance rollout
- `POST /api/v1/deployment/rollback/manual` - Manual rollback
- `GET /api/v1/deployment/health-checks` - System health

## Kerykeion Features Rollout Plan

### Phase 1 (5% users, 2h monitoring)
**Features:**
- `kerykeion_natal_charts` - Enhanced natal chart calculations
- `kerykeion_synastry` - Professional synastry analysis  
- `performance_optimization` - Async processing and caching

**Success Criteria:**
- Error rate < 3%
- Response time < 2500ms
- Fallback rate < 15%
- User satisfaction > 8/10

### Phase 2 (20% users, 4h monitoring)
**Features:**
- `kerykeion_transits` - Advanced transit calculations
- `kerykeion_progressions` - Secondary progressions and returns

**Success Criteria:**
- Error rate < 4%
- Response time < 3000ms
- Fallback rate < 20%
- User satisfaction > 7.5/10

### Phase 3 (50% users, 8h monitoring)
**Features:**
- `enhanced_compatibility` - AI-enhanced compatibility analysis
- `ai_consultation` - AI-powered astrological consultations

**Success Criteria:**
- Error rate < 5%
- Response time < 3500ms
- Fallback rate < 25%
- User satisfaction > 7/10

### Phase 4 (100% users, 12h monitoring)
**Features:**
- `russian_localization` - Complete Russian localization system

**Success Criteria:**
- Error rate < 6%
- Response time < 4000ms
- Fallback rate < 30%
- User satisfaction > 6.5/10

## Deployment Execution

### Automated Deployment

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

### Manual Deployment Steps

```python
from deployment_config import ProductionDeploymentConfig

# 1. Initialize deployment
config = ProductionDeploymentConfig()
init_result = await config.initialize_deployment_systems()

# 2. Execute phased deployment
deployment_result = await config.execute_phased_deployment()
```

### Emergency Rollback

```bash
# Emergency rollback all features
python scripts/deploy_kerykeion.py --rollback

# Rollback specific features
python scripts/deploy_kerykeion.py --rollback --features kerykeion_transits kerykeion_progressions
```

## Monitoring and Alerting

### Real-time Dashboard

Access the deployment dashboard at:
- Local: `http://localhost:8000/api/v1/deployment/status`
- Production: `https://your-domain.com/api/v1/deployment/status`

### Performance Reports

```bash
# Get 24-hour performance report
curl -X GET http://localhost:8000/api/v1/deployment/performance-report

# Get system health checks
curl -X GET http://localhost:8000/api/v1/deployment/health-checks
```

### Alert Thresholds

Configure in `app/core/config.py`:

```python
# Monitoring thresholds
ALERT_RESPONSE_TIME_MS: int = 3000      # Max response time for Alice
ALERT_ERROR_RATE_PERCENT: float = 5.0   # Max error rate  
ALERT_FALLBACK_RATE_PERCENT: float = 25.0  # Max fallback usage
ALERT_USER_SATISFACTION_MIN: float = 7.0   # Min satisfaction score
```

## Circuit Breaker Protection

The system includes circuit breaker protection to prevent rollback loops:

- **Maximum rollbacks per hour**: 3
- **Cooldown period**: 30 minutes after max rollbacks
- **Auto-reset**: Counter resets after 1 hour

## Integration with Existing Services

### Kerykeion Service Integration

```python
# Example: Enhanced natal chart with deployment monitoring
from app.services.deployment_monitor import deployment_monitor
from app.services.feature_flag_service import feature_flags, KerykeionFeatureFlags

async def calculate_natal_chart(user_id: str, birth_data: dict):
    # Check if enhanced features are enabled
    if feature_flags.is_feature_enabled(KerykeionFeatureFlags.KERYKEION_NATAL_CHARTS, user_id):
        try:
            # Use Kerykeion for enhanced calculation
            result = await kerykeion_service.calculate_enhanced_natal_chart(birth_data)
            
            # Record successful usage
            await deployment_monitor.record_kerykeion_usage(
                "natal_chart", 
                success=True, 
                response_time_ms=result.calculation_time,
                fallback_used=False
            )
            
            return result
            
        except Exception as e:
            # Record failure and fall back
            await deployment_monitor.record_kerykeion_usage(
                "natal_chart",
                success=False,
                response_time_ms=0,
                fallback_used=True
            )
            
            # Use fallback calculation
            return await basic_natal_chart_calculation(birth_data)
    else:
        # Feature not enabled, use basic calculation
        return await basic_natal_chart_calculation(birth_data)
```

### Alice Voice Interface Integration

The deployment system ensures Alice voice interface compliance:

- **Response Time Limit**: 3-5 seconds maximum
- **Character Limits**: 800 chars for horoscopes, 600 for compatibility
- **Fallback Handling**: Graceful degradation to basic features
- **User Experience**: Seamless experience regardless of rollout phase

## Configuration

### Environment Variables

```bash
# Production deployment settings
ENABLE_DEPLOYMENT_MONITORING=true
ENABLE_FEATURE_FLAGS=true
ENABLE_ROLLBACK_AUTOMATION=true
REDIS_URL=redis://localhost:6379/0

# Deployment phase settings  
DEPLOYMENT_PHASE_1_PERCENTAGE=5.0
DEPLOYMENT_PHASE_2_PERCENTAGE=20.0
DEPLOYMENT_PHASE_3_PERCENTAGE=50.0
DEPLOYMENT_FULL_PERCENTAGE=100.0

# Monitoring thresholds
ALERT_RESPONSE_TIME_MS=3000
ALERT_ERROR_RATE_PERCENT=5.0
ALERT_FALLBACK_RATE_PERCENT=25.0
ALERT_USER_SATISFACTION_MIN=7.0
```

### Docker Configuration

Add to `docker-compose.yml`:

```yaml
services:
  backend:
    environment:
      - ENABLE_DEPLOYMENT_MONITORING=true
      - ENABLE_FEATURE_FLAGS=true
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

## Testing

### Validation Tests

```bash
# Run deployment system validation
python test_deployment_validation.py

# Run full test suite
pytest tests/test_deployment_system.py -v
```

### Load Testing

Test the deployment system under load:

```bash
# Simulate high traffic during rollout
python scripts/load_test_deployment.py --users 1000 --duration 300
```

## Troubleshooting

### Common Issues

1. **Feature flags not working**
   - Check Redis connection
   - Verify feature flag state in cache
   - Confirm user ID hashing consistency

2. **Rollback not triggering**
   - Check health check thresholds
   - Verify circuit breaker status
   - Review rollback rules configuration

3. **Performance degradation**
   - Monitor Kerykeion fallback rates
   - Check cache hit rates
   - Review resource usage metrics

### Debug Commands

```bash
# Check feature flag status
curl -X GET http://localhost:8000/api/v1/deployment/features

# Get rollback statistics
curl -X GET http://localhost:8000/api/v1/deployment/rollback/statistics

# Check system status
curl -X GET http://localhost:8000/api/v1/deployment/system-status
```

## Security Considerations

- Feature flag states are cached and encrypted
- Rollback triggers are logged with correlation IDs
- API endpoints require appropriate authentication
- User data privacy maintained during rollout tracking

## Future Enhancements

- A/B testing framework integration
- Canary deployment strategies
- Blue-green deployment support
- Automated performance regression detection
- Advanced ML-based rollback prediction

## Contact and Support

For issues with the deployment system:

1. Check logs: `/logs/astroloh.log`
2. Review deployment dashboard
3. Check rollback history
4. Consult troubleshooting section above

The deployment system is designed to be self-healing and should automatically handle most issues through its monitoring and rollback capabilities.