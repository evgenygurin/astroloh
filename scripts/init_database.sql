-- Full Database Initialization Script for Astroloh
-- This script ensures all users, roles, and tables are properly created

-- Create extension for UUID generation if not exists
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Ensure user exists (if not using Docker environment variables)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'astroloh_user') THEN
        CREATE USER astroloh_user WITH PASSWORD 'astroloh_password';
        GRANT ALL PRIVILEGES ON DATABASE astroloh_db TO astroloh_user;
        ALTER USER astroloh_user CREATEDB;
        ALTER USER astroloh_user SUPERUSER;
    ELSE
        -- Update password for existing user to ensure scram-sha-256 compatibility
        ALTER USER astroloh_user WITH PASSWORD 'astroloh_password';
    END IF;
END
$$;

-- Grant necessary permissions
GRANT CREATE ON SCHEMA public TO astroloh_user;
GRANT USAGE ON SCHEMA public TO astroloh_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO astroloh_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO astroloh_user;

-- Create Alembic version table if not exists
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Migration 000: Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    yandex_user_id VARCHAR(255) NOT NULL UNIQUE,
    encrypted_birth_date BYTEA,
    encrypted_birth_time BYTEA,
    encrypted_birth_location BYTEA,
    encrypted_name BYTEA,
    zodiac_sign VARCHAR(20),
    gender VARCHAR(10),
    data_consent BOOLEAN NOT NULL DEFAULT FALSE,
    data_retention_days INTEGER NOT NULL DEFAULT 365,
    preferences JSON,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    last_accessed TIMESTAMP
);

-- Create indexes for users table
CREATE INDEX IF NOT EXISTS idx_users_yandex_user_id ON users (yandex_user_id);
CREATE INDEX IF NOT EXISTS idx_users_data_consent ON users (data_consent);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users (created_at);
CREATE INDEX IF NOT EXISTS idx_users_last_accessed ON users (last_accessed);

-- Migration 001: Create IoT tables
CREATE TABLE IF NOT EXISTS iot_devices (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    device_id VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    device_type VARCHAR(50) NOT NULL,
    protocol VARCHAR(50) NOT NULL,
    manufacturer VARCHAR(255),
    model VARCHAR(255),
    firmware_version VARCHAR(100),
    status VARCHAR(50),
    capabilities JSON,
    configuration JSON,
    location VARCHAR(255),
    room VARCHAR(255),
    last_seen TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    CONSTRAINT fk_iot_devices_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS home_automations (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    automation_type VARCHAR(50) NOT NULL,
    trigger_conditions JSON,
    actions JSON,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    schedule JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    last_executed TIMESTAMP,
    CONSTRAINT fk_home_automations_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS device_events (
    id BIGSERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL,
    user_id UUID NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    event_data JSON,
    astro_context JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_device_events_device FOREIGN KEY (device_id) REFERENCES iot_devices(id) ON DELETE CASCADE,
    CONSTRAINT fk_device_events_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create indexes for IoT tables
CREATE INDEX IF NOT EXISTS idx_iot_devices_user_id ON iot_devices (user_id);
CREATE INDEX IF NOT EXISTS idx_iot_devices_device_id ON iot_devices (device_id);
CREATE INDEX IF NOT EXISTS idx_iot_devices_type ON iot_devices (device_type);
CREATE INDEX IF NOT EXISTS idx_iot_devices_status ON iot_devices (status);

CREATE INDEX IF NOT EXISTS idx_home_automations_user_id ON home_automations (user_id);
CREATE INDEX IF NOT EXISTS idx_home_automations_type ON home_automations (automation_type);
CREATE INDEX IF NOT EXISTS idx_home_automations_active ON home_automations (is_active);

CREATE INDEX IF NOT EXISTS idx_device_events_device_id ON device_events (device_id);
CREATE INDEX IF NOT EXISTS idx_device_events_user_id ON device_events (user_id);
CREATE INDEX IF NOT EXISTS idx_device_events_type ON device_events (event_type);
CREATE INDEX IF NOT EXISTS idx_device_events_created_at ON device_events (created_at);

-- Migration 002: Create core astrology tables
CREATE TABLE IF NOT EXISTS astrology_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    session_id VARCHAR(255) NOT NULL,
    platform VARCHAR(50) NOT NULL,
    session_data JSON,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    expired_at TIMESTAMP,
    CONSTRAINT fk_astrology_sessions_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS horoscope_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cache_key VARCHAR(255) NOT NULL UNIQUE,
    horoscope_data JSON NOT NULL,
    zodiac_sign VARCHAR(20) NOT NULL,
    period VARCHAR(20) NOT NULL,
    generation_method VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP
);

CREATE TABLE IF NOT EXISTS compatibility_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cache_key VARCHAR(255) NOT NULL UNIQUE,
    sign1 VARCHAR(20) NOT NULL,
    sign2 VARCHAR(20) NOT NULL,
    compatibility_data JSON NOT NULL,
    generation_method VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    access_count INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS user_queries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID,
    session_id VARCHAR(255),
    platform VARCHAR(50) NOT NULL,
    query_text TEXT NOT NULL,
    intent VARCHAR(100),
    entities JSON,
    response_text TEXT,
    response_type VARCHAR(50),
    processing_time_ms INTEGER,
    success BOOLEAN NOT NULL DEFAULT TRUE,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_user_queries_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS analytics_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID,
    session_id VARCHAR(255),
    event_type VARCHAR(100) NOT NULL,
    platform VARCHAR(50) NOT NULL,
    event_data JSON,
    user_agent VARCHAR(500),
    ip_address INET,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_analytics_events_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Create indexes for core tables
CREATE INDEX IF NOT EXISTS idx_astrology_sessions_user_id ON astrology_sessions (user_id);
CREATE INDEX IF NOT EXISTS idx_astrology_sessions_session_id ON astrology_sessions (session_id);
CREATE INDEX IF NOT EXISTS idx_astrology_sessions_platform ON astrology_sessions (platform);
CREATE INDEX IF NOT EXISTS idx_astrology_sessions_active ON astrology_sessions (is_active);
CREATE INDEX IF NOT EXISTS idx_astrology_sessions_created_at ON astrology_sessions (created_at);

CREATE INDEX IF NOT EXISTS idx_horoscope_cache_cache_key ON horoscope_cache (cache_key);
CREATE INDEX IF NOT EXISTS idx_horoscope_cache_zodiac_sign ON horoscope_cache (zodiac_sign);
CREATE INDEX IF NOT EXISTS idx_horoscope_cache_period ON horoscope_cache (period);
CREATE INDEX IF NOT EXISTS idx_horoscope_cache_expires_at ON horoscope_cache (expires_at);
CREATE INDEX IF NOT EXISTS idx_horoscope_cache_created_at ON horoscope_cache (created_at);

CREATE INDEX IF NOT EXISTS idx_compatibility_cache_cache_key ON compatibility_cache (cache_key);
CREATE INDEX IF NOT EXISTS idx_compatibility_cache_signs ON compatibility_cache (sign1, sign2);
CREATE INDEX IF NOT EXISTS idx_compatibility_cache_expires_at ON compatibility_cache (expires_at);

CREATE INDEX IF NOT EXISTS idx_user_queries_user_id ON user_queries (user_id);
CREATE INDEX IF NOT EXISTS idx_user_queries_session_id ON user_queries (session_id);
CREATE INDEX IF NOT EXISTS idx_user_queries_platform ON user_queries (platform);
CREATE INDEX IF NOT EXISTS idx_user_queries_intent ON user_queries (intent);
CREATE INDEX IF NOT EXISTS idx_user_queries_created_at ON user_queries (created_at);
CREATE INDEX IF NOT EXISTS idx_user_queries_success ON user_queries (success);

CREATE INDEX IF NOT EXISTS idx_analytics_events_user_id ON analytics_events (user_id);
CREATE INDEX IF NOT EXISTS idx_analytics_events_session_id ON analytics_events (session_id);
CREATE INDEX IF NOT EXISTS idx_analytics_events_event_type ON analytics_events (event_type);
CREATE INDEX IF NOT EXISTS idx_analytics_events_platform ON analytics_events (platform);
CREATE INDEX IF NOT EXISTS idx_analytics_events_created_at ON analytics_events (created_at);

-- Set migration version
INSERT INTO alembic_version (version_num) 
VALUES ('002_create_core_tables') 
ON CONFLICT (version_num) DO NOTHING;

-- Final permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO astroloh_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO astroloh_user;

SELECT 'Database initialization completed successfully!' as result;