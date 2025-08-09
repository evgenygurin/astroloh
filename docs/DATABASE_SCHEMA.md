# Database Schema

- Users, preferences, interactions (see `app/models/*`).
- Use Alembic for migrations.

Commands:
- `alembic upgrade head`
- `alembic revision --autogenerate -m "message"`

## Overview

Astroloh uses PostgreSQL 15 with SQLAlchemy 2.0 ORM for data persistence. The schema is designed for GDPR compliance with comprehensive encryption, audit trails, and performance optimization for astrological applications.

## Database Configuration

### Connection Settings
- **Database**: PostgreSQL 15+
- **ORM**: SQLAlchemy 2.0 with async support
- **Driver**: asyncpg for high-performance async operations
- **Migrations**: Alembic for schema versioning
- **Connection Pool**: 20 connections with overflow protection

### Security Features
- **Encryption**: AES-256 for sensitive personal data
- **GDPR Compliance**: Automated data retention and deletion
- **Audit Logging**: Comprehensive security event tracking
- **Data Anonymization**: Hashed identifiers for analytics

## Core Tables

### Users Table

Primary table for user data with comprehensive encryption.

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    yandex_user_id VARCHAR(255) UNIQUE NOT NULL,
    
    -- Encrypted personal data (AES-256)
    encrypted_birth_date BYTEA,
    encrypted_birth_time BYTEA,
    encrypted_birth_location BYTEA,
    encrypted_name BYTEA,
    
    -- Public data (non-sensitive)
    zodiac_sign VARCHAR(20),
    gender VARCHAR(10),
    
    -- Privacy settings
    data_consent BOOLEAN DEFAULT FALSE NOT NULL,
    data_retention_days INTEGER DEFAULT 365 NOT NULL,
    
    -- User preferences (JSON)
    preferences JSONB,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_users_yandex_user_id ON users(yandex_user_id);
CREATE INDEX idx_users_zodiac_sign ON users(zodiac_sign);
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_users_last_accessed ON users(last_accessed);
```

**Key Features**:
- **UUID Primary Key**: Platform-independent unique identifiers
- **Encrypted Fields**: Birth data, location, name encrypted at rest
- **GDPR Compliance**: Consent tracking and retention policies
- **JSON Preferences**: Flexible user customization storage
- **Audit Trail**: Creation, update, and access timestamps

### User Sessions Table

Manages dialog state and conversation flow across platforms.

```sql
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    
    -- Dialog state management
    current_state VARCHAR(50) DEFAULT 'initial' NOT NULL,
    context_data TEXT, -- JSON string for session context
    
    -- Session security
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Activity tracking
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Indexes for performance
CREATE INDEX idx_user_sessions_session_id ON user_sessions(session_id);
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX idx_user_sessions_is_active ON user_sessions(is_active);
```

**Key Features**:
- **Session State Management**: Tracks dialog flow and user context
- **Security**: Session expiration and active status tracking
- **Platform Agnostic**: Works across Yandex Alice, Telegram, Google Assistant
- **JSON Context**: Flexible storage for conversation state

### Horoscope Requests Table

Tracks astrological consultation requests with encrypted parameters.

```sql
CREATE TABLE horoscope_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    
    -- Request classification
    request_type VARCHAR(50) NOT NULL, -- daily, weekly, monthly, natal, compatibility
    
    -- Encrypted request parameters
    encrypted_target_date BYTEA,
    encrypted_partner_data BYTEA, -- For compatibility requests
    
    -- Request metadata
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    ip_hash VARCHAR(64), -- SHA-256 hash for analytics
    
    -- Performance tracking
    processing_time_ms INTEGER,
    cache_hit BOOLEAN DEFAULT FALSE
);

-- Indexes for analytics and performance
CREATE INDEX idx_horoscope_requests_user_id ON horoscope_requests(user_id);
CREATE INDEX idx_horoscope_requests_type ON horoscope_requests(request_type);
CREATE INDEX idx_horoscope_requests_processed_at ON horoscope_requests(processed_at);
CREATE INDEX idx_horoscope_requests_ip_hash ON horoscope_requests(ip_hash);
```

**Key Features**:
- **Request Types**: Supports all consultation types (daily, weekly, natal, etc.)
- **Encrypted Parameters**: Target dates and partner data encrypted
- **Analytics**: IP hashing for usage analysis while preserving privacy
- **Performance Metrics**: Response time and cache hit tracking

## ML and Personalization Tables

### User Preferences Table

Stores detailed personalization settings for recommendation engine.

```sql
CREATE TABLE user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    
    -- Interest categories with weights (JSON)
    interests JSONB, -- {"career": 0.8, "love": 0.9, "health": 0.6}
    
    -- Communication preferences
    communication_style VARCHAR(20) DEFAULT 'balanced', -- formal, casual, friendly, mystical
    complexity_level VARCHAR(20) DEFAULT 'intermediate', -- beginner, intermediate, advanced
    
    -- Temporal preferences
    preferred_time_slots JSONB, -- [{"start": "09:00", "end": "12:00"}]
    timezone VARCHAR(50),
    
    -- Cultural settings
    cultural_context VARCHAR(20), -- western, vedic, chinese
    language_preference VARCHAR(10) DEFAULT 'ru',
    
    -- Content preferences
    content_length_preference VARCHAR(20) DEFAULT 'medium', -- short, medium, long
    detail_level VARCHAR(20) DEFAULT 'standard', -- brief, standard, detailed
    
    -- ML-learned preferences
    preferences JSONB, -- Machine learning insights
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Indexes for recommendation queries
CREATE INDEX idx_user_preferences_user_id ON user_preferences(user_id);
CREATE INDEX idx_user_preferences_interests ON user_preferences USING GIN(interests);
CREATE INDEX idx_user_preferences_cultural_context ON user_preferences(cultural_context);
```

### User Interactions Table

Tracks user behavior for machine learning and recommendation improvement.

```sql
CREATE TABLE user_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    
    -- Interaction details
    interaction_type VARCHAR(50) NOT NULL, -- view, like, dislike, save, share
    content_type VARCHAR(50) NOT NULL, -- horoscope, compatibility, lunar
    content_id VARCHAR(255),
    
    -- User feedback
    session_duration INTEGER, -- seconds
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    feedback_text TEXT,
    
    -- Astrological context at time of interaction
    astronomical_data JSONB, -- Planet positions, transits at time of interaction
    
    -- Timestamp
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Indexes for ML queries
CREATE INDEX idx_user_interactions_user_id ON user_interactions(user_id);
CREATE INDEX idx_user_interactions_type ON user_interactions(interaction_type);
CREATE INDEX idx_user_interactions_content_type ON user_interactions(content_type);
CREATE INDEX idx_user_interactions_timestamp ON user_interactions(timestamp);
CREATE INDEX idx_user_interactions_rating ON user_interactions(rating);
```

### Recommendations Table

Stores ML-generated personalized recommendations.

```sql
CREATE TABLE recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    
    -- Recommendation details
    recommendation_type VARCHAR(50) NOT NULL, -- content, action, timing
    content_type VARCHAR(50) NOT NULL, -- daily, weekly, compatibility
    
    -- Content
    title VARCHAR(255) NOT NULL,
    description TEXT,
    recommendation_data JSONB,
    
    -- ML scoring
    confidence_score INTEGER CHECK (confidence_score >= 0 AND confidence_score <= 100) NOT NULL,
    priority INTEGER DEFAULT 1 CHECK (priority >= 1 AND priority <= 5),
    
    -- Algorithm metadata
    algorithm_used VARCHAR(50) NOT NULL, -- collaborative, content_based, hybrid
    model_version VARCHAR(20) NOT NULL,
    
    -- Status tracking
    status VARCHAR(20) DEFAULT 'active', -- active, shown, dismissed, expired
    expires_at TIMESTAMP WITH TIME ZONE,
    shown_at TIMESTAMP WITH TIME ZONE,
    
    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Indexes for recommendation retrieval
CREATE INDEX idx_recommendations_user_id ON recommendations(user_id);
CREATE INDEX idx_recommendations_status ON recommendations(status);
CREATE INDEX idx_recommendations_priority ON recommendations(priority);
CREATE INDEX idx_recommendations_confidence ON recommendations(confidence_score);
CREATE INDEX idx_recommendations_expires_at ON recommendations(expires_at);
```

### User Clusters Table

Manages user segmentation for collaborative filtering.

```sql
CREATE TABLE user_clusters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    
    -- Cluster identification
    cluster_id VARCHAR(50) NOT NULL,
    cluster_name VARCHAR(100),
    
    -- Cluster characteristics
    cluster_features JSONB, -- Astrological and behavioral features
    similarity_score INTEGER CHECK (similarity_score >= 0 AND similarity_score <= 100) NOT NULL,
    
    -- Metadata
    algorithm_version VARCHAR(20) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Indexes for clustering queries
CREATE INDEX idx_user_clusters_user_id ON user_clusters(user_id);
CREATE INDEX idx_user_clusters_cluster_id ON user_clusters(cluster_id);
CREATE INDEX idx_user_clusters_similarity ON user_clusters(similarity_score);
```

### A/B Test Groups Table

Manages experimentation and feature testing.

```sql
CREATE TABLE ab_test_groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    
    -- Test configuration
    test_name VARCHAR(100) NOT NULL,
    group_name VARCHAR(50) NOT NULL, -- control, variant_a, variant_b
    
    -- Test parameters
    test_parameters JSONB,
    test_start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    test_end_date TIMESTAMP WITH TIME ZONE,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Assignment timestamp
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Indexes for A/B test queries
CREATE INDEX idx_ab_test_groups_user_id ON ab_test_groups(user_id);
CREATE INDEX idx_ab_test_groups_test_name ON ab_test_groups(test_name);
CREATE INDEX idx_ab_test_groups_is_active ON ab_test_groups(is_active);
```

## Security and Compliance Tables

### Data Deletion Requests Table

Manages GDPR data deletion workflow.

```sql
CREATE TABLE data_deletion_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    
    -- Request status
    status VARCHAR(20) DEFAULT 'pending' NOT NULL, -- pending, processing, completed, failed
    
    -- Request details
    request_reason TEXT,
    requested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    processed_at TIMESTAMP WITH TIME ZONE,
    
    -- Verification
    verification_code VARCHAR(32) NOT NULL,
    verified BOOLEAN DEFAULT FALSE NOT NULL
);

-- Indexes for GDPR processing
CREATE INDEX idx_data_deletion_status ON data_deletion_requests(status);
CREATE INDEX idx_data_deletion_requested_at ON data_deletion_requests(requested_at);
```

### Security Logs Table

Comprehensive audit trail for security events.

```sql
CREATE TABLE security_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Event classification
    event_type VARCHAR(50) NOT NULL, -- login, data_access, encryption, decryption, deletion
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    session_id VARCHAR(255),
    
    -- Event details
    description TEXT NOT NULL,
    ip_hash VARCHAR(64), -- SHA-256 hashed IP
    user_agent_hash VARCHAR(64), -- SHA-256 hashed user agent
    
    -- Operation result
    success BOOLEAN NOT NULL,
    error_message TEXT,
    
    -- Timestamp
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Indexes for security analysis
CREATE INDEX idx_security_logs_event_type ON security_logs(event_type);
CREATE INDEX idx_security_logs_user_id ON security_logs(user_id);
CREATE INDEX idx_security_logs_timestamp ON security_logs(timestamp);
CREATE INDEX idx_security_logs_success ON security_logs(success);
```

## Analytics and Metrics Tables

### Recommendation Metrics Table

Tracks recommendation system performance.

```sql
CREATE TABLE recommendation_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    recommendation_id UUID REFERENCES recommendations(id) ON DELETE CASCADE,
    
    -- Metric details
    metric_name VARCHAR(50) NOT NULL, -- ctr, conversion, satisfaction
    metric_value INTEGER NOT NULL,
    
    -- Context
    context_data JSONB,
    session_id VARCHAR(255),
    
    -- Timestamp
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Indexes for metrics analysis
CREATE INDEX idx_recommendation_metrics_name ON recommendation_metrics(metric_name);
CREATE INDEX idx_recommendation_metrics_recorded_at ON recommendation_metrics(recorded_at);
```

## Database Functions and Triggers

### Automatic Timestamp Updates

```sql
-- Function to update updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to relevant tables
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at 
    BEFORE UPDATE ON user_preferences 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_clusters_updated_at 
    BEFORE UPDATE ON user_clusters 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### Session Cleanup Function

```sql
-- Function to clean up expired sessions
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM user_sessions 
    WHERE expires_at < NOW() OR (is_active = FALSE AND last_activity < NOW() - INTERVAL '1 day');
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Log cleanup activity
    INSERT INTO security_logs (event_type, description, success, timestamp)
    VALUES ('session_cleanup', 'Cleaned up ' || deleted_count || ' expired sessions', TRUE, NOW());
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Schedule cleanup (run via cron or application scheduler)
-- SELECT cleanup_expired_sessions();
```

### Data Retention Enforcement

```sql
-- Function to enforce data retention policies
CREATE OR REPLACE FUNCTION enforce_data_retention()
RETURNS INTEGER AS $$
DECLARE
    affected_users INTEGER;
BEGIN
    -- Mark users for deletion based on retention policy
    UPDATE users 
    SET data_consent = FALSE 
    WHERE last_accessed < NOW() - (data_retention_days || ' days')::INTERVAL
    AND data_consent = TRUE;
    
    GET DIAGNOSTICS affected_users = ROW_COUNT;
    
    -- Log retention enforcement
    INSERT INTO security_logs (event_type, description, success, timestamp)
    VALUES ('data_retention', 'Marked ' || affected_users || ' users for retention review', TRUE, NOW());
    
    RETURN affected_users;
END;
$$ LANGUAGE plpgsql;
```

## Performance Optimization

### Index Strategy

**Primary Indexes (Automatic)**:
- All primary keys (UUID)
- Foreign key constraints
- Unique constraints (session_id, yandex_user_id)

**Query-Specific Indexes**:
- User lookup: `yandex_user_id`, `zodiac_sign`
- Session management: `session_id`, `expires_at`, `is_active`
- Analytics: `timestamp` fields, `request_type`, `interaction_type`
- ML queries: `user_id`, `cluster_id`, `similarity_score`

**Composite Indexes**:
```sql
-- Multi-column indexes for complex queries
CREATE INDEX idx_user_sessions_active_user ON user_sessions(user_id, is_active, expires_at);
CREATE INDEX idx_recommendations_user_status ON recommendations(user_id, status, priority);
CREATE INDEX idx_security_logs_user_time ON security_logs(user_id, timestamp, event_type);
```

**JSON Indexes (PostgreSQL GIN)**:
```sql
-- Indexes for JSON/JSONB queries
CREATE INDEX idx_user_preferences_interests ON user_preferences USING GIN(interests);
CREATE INDEX idx_astronomical_data ON user_interactions USING GIN(astronomical_data);
CREATE INDEX idx_cluster_features ON user_clusters USING GIN(cluster_features);
```

### Query Performance Tips

1. **Use Prepared Statements**: SQLAlchemy automatically optimizes repeated queries
2. **Connection Pooling**: Configure appropriate pool sizes for your workload
3. **Async Operations**: Leverage asyncpg for non-blocking database operations
4. **Batch Operations**: Use bulk inserts for analytics data
5. **Partition Large Tables**: Consider partitioning by date for historical data

### Monitoring Queries

```sql
-- Check query performance
SELECT query, mean_exec_time, calls, total_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Check index usage
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE schemaname = 'public'
ORDER BY n_distinct DESC;

-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## Backup and Migration Strategy

### Database Migrations with Alembic

**Migration Commands**:
```bash
# Generate new migration
alembic revision --autogenerate -m "Add new feature"

# Apply migrations
alembic upgrade head

# Rollback migrations  
alembic downgrade -1

# Check current revision
alembic current

# Show migration history
alembic history
```

### Backup Strategy

**Full Backup**:
```bash
pg_dump -h localhost -U astroloh_user -d astroloh_db --format=custom --compress=9 > backup.dump
```

**Incremental Backup** (WAL-E or similar):
```bash
# Point-in-time recovery setup
archive_mode = on
archive_command = 'wal-e wal-push %p'
```

**Selective Backup** (excluding sensitive data):
```bash
pg_dump -h localhost -U astroloh_user -d astroloh_db \
    --exclude-table-data=security_logs \
    --exclude-table-data=user_interactions \
    > anonymized_backup.sql
```

## Data Privacy and Encryption

### Encryption Implementation

**Field-Level Encryption**:
- Uses AES-256-GCM for authenticated encryption
- Separate encryption keys for different data types
- Key rotation support through environment variables

**Encrypted Fields**:
- `encrypted_birth_date`: Date of birth
- `encrypted_birth_time`: Time of birth  
- `encrypted_birth_location`: Birth location coordinates
- `encrypted_name`: User's real name
- `encrypted_partner_data`: Partner information for compatibility

**Data Access Pattern**:
```python
# Encryption service handles automatic encrypt/decrypt
user.birth_date = date(1990, 8, 15)  # Automatically encrypted
retrieved_date = user.birth_date     # Automatically decrypted
```

### GDPR Compliance Features

1. **Right to Access**: Query all user data across tables
2. **Right to Rectification**: Update encrypted personal data
3. **Right to Erasure**: Automated deletion workflow
4. **Right to Portability**: Export user data in JSON format
5. **Data Retention**: Configurable retention periods per user
6. **Consent Management**: Tracking and enforcement of data consent

This schema provides a robust foundation for the Astroloh platform while ensuring security, performance, and regulatory compliance.

