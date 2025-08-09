# API Reference

- GET `/` – service info
- GET `/health` – health
- POST `/api/v1/yandex/webhook` – Yandex Dialogs
- Astrology (`/api/astrology`):
  - POST `/natal-chart`
  - GET `/horoscope/{sign}/{type}` (daily|weekly|monthly)
  - POST `/compatibility`
- Lunar (`/api/lunar/*`) – phases and calendar

Auth: token-based (see `app/api/auth.py`).

## Overview

Astroloh provides a comprehensive multi-platform astrological API supporting Yandex Alice, Telegram Bot, Google Assistant, and IoT Smart Home integrations. All endpoints follow RESTful principles and return JSON responses.

**Base URL**: `http://localhost:8000` (development) or your deployed domain

## Authentication

Most endpoints are public and require no authentication. Secure endpoints use:
- Rate limiting (default: per-IP limits)
- CORS protection
- Security headers middleware

## Core API Endpoints

### Application Status

#### GET /
Root endpoint providing service overview.

**Response**:
```json
{
  "message": "Astroloh - Multi-Platform Astrological Assistant is running!",
  "platforms": [
    "Yandex Alice",
    "Telegram Bot", 
    "Google Assistant",
    "IoT Smart Home"
  ]
}
```

#### GET /health
Service health check endpoint.

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-08-09T02:00:00.000Z",
  "version": "1.0.0"
}
```

## Yandex Alice Integration

### POST /api/v1/yandex/webhook
Main webhook for processing Yandex Alice voice requests.

**Headers**:
- `Content-Type: application/json`

**Request Body**:
```json
{
  "request": {
    "command": "дай гороскоп для льва",
    "original_utterance": "дай гороскоп для льва",
    "type": "SimpleUtterance",
    "markup": {
      "dangerous_context": false
    },
    "payload": {}
  },
  "session": {
    "user_id": "anonymous_user_id",
    "session_id": "session_id_here",
    "message_id": 1,
    "new": false
  },
  "version": "1.0"
}
```

**Response**:
```json
{
  "response": {
    "text": "Сегодня для Львов благоприятный день...",
    "tts": "Сегодня для Львов благоприятный день...",
    "buttons": [
      {
        "title": "Совместимость",
        "hide": true
      }
    ],
    "end_session": false
  },
  "session": {
    "user_id": "anonymous_user_id",
    "session_id": "session_id_here",
    "message_id": 2
  },
  "version": "1.0"
}
```

**Supported Intents**:
- **GREET**: Приветствие и знакомство
- **HOROSCOPE**: Гороскопы (ежедневные, недельные, месячные)
- **COMPATIBILITY**: Анализ совместимости знаков зодиака
- **NATAL_CHART**: Натальные карты и персональные расчеты
- **LUNAR_CALENDAR**: Лунный календарь и фазы луны
- **TRANSITS**: Текущие планетарные влияния
- **PROGRESSIONS**: Персональное развитие и прогрессии
- **SOLAR_RETURN**: Годичные прогнозы
- **LUNAR_RETURN**: Месячные прогнозы
- **ADVICE**: Персонализированные рекомендации
- **AI_NATAL_INTERPRETATION**: ИИ-интерпретация натальной карты
- **AI_CAREER_CONSULTATION**: Карьерные консультации с ИИ
- **AI_LOVE_CONSULTATION**: Любовные консультации с ИИ
- **AI_HEALTH_CONSULTATION**: Консультации по здоровью с ИИ
- **AI_FINANCIAL_CONSULTATION**: Финансовые консультации с ИИ
- **AI_SPIRITUAL_CONSULTATION**: Духовные консультации с ИИ
- **SIGN_DESCRIPTION**: Описание знаков зодиака
- **PLANET_IN_SIGN**: Планеты в знаках
- **HOUSE_CHARACTERISTICS**: Характеристики домов
- **RETROGRADE_INFLUENCE**: Влияние ретроградных планет
- **HELP**: Справочная информация
- **EXIT**: Завершение сессии
- **UNKNOWN**: Обработка неизвестных запросов

#### GET /api/v1/yandex/health
Health check specifically for Yandex Dialogs service.

**Response**:
```json
{
  "status": "healthy",
  "service": "yandex_dialogs",
  "active_sessions": 15,
  "components": {
    "intent_recognizer": "ok",
    "session_manager": "ok",
    "response_formatter": "ok",
    "error_handler": "ok"
  }
}
```

#### POST /api/v1/yandex/cleanup-sessions
Force cleanup of expired sessions.

**Response**:
```json
{
  "status": "success",
  "cleaned_sessions": 3
}
```

## Telegram Bot Integration

### POST /api/v1/telegram/webhook
Webhook for processing Telegram bot updates.

**Request Body**:
```json
{
  "update_id": 123456789,
  "message": {
    "message_id": 1234,
    "from": {
      "id": 987654321,
      "is_bot": false,
      "first_name": "User",
      "username": "username"
    },
    "chat": {
      "id": 987654321,
      "first_name": "User",
      "username": "username",
      "type": "private"
    },
    "date": 1640995200,
    "text": "/start"
  }
}
```

## Google Assistant Integration

### POST /api/v1/google/webhook
Webhook for processing Google Assistant requests.

**Request Body** (follows Actions on Google format):
```json
{
  "responseId": "response-id",
  "queryResult": {
    "queryText": "talk to astroloh",
    "languageCode": "en-US"
  },
  "originalDetectIntentRequest": {
    "source": "google",
    "payload": {
      "user": {
        "userId": "user-id"
      }
    }
  }
}
```

## IoT Smart Home Integration

### POST /api/v1/iot/process
Process smart home voice commands with astrological context.

**Request Body**:
```json
{
  "device_id": "living_room_assistant",
  "user_command": "What does astrology say about today?",
  "device_capabilities": ["voice_output", "light_control"],
  "user_context": {
    "zodiac_sign": "leo",
    "location": "Moscow"
  }
}
```

**Response**:
```json
{
  "response_text": "Today is favorable for Leos...",
  "device_actions": [
    {
      "action_type": "set_lighting",
      "parameters": {
        "color": "warm_gold",
        "brightness": 75
      }
    }
  ],
  "follow_up_suggestions": [
    "Ask about compatibility",
    "Get lunar calendar"
  ]
}
```

### GET /api/v1/iot/analytics
Retrieve IoT usage analytics.

**Query Parameters**:
- `device_id` (optional): Filter by specific device
- `date_from` (optional): Start date (YYYY-MM-DD)
- `date_to` (optional): End date (YYYY-MM-DD)

**Response**:
```json
{
  "total_interactions": 1250,
  "devices": {
    "living_room_assistant": {
      "interactions": 750,
      "most_requested": "daily_horoscope",
      "avg_session_duration": 45
    }
  },
  "popular_queries": [
    "daily horoscope",
    "compatibility check",
    "lunar calendar"
  ]
}
```

## Astrology Core API

### POST /astrology/calculate
Direct access to astrological calculations.

**Request Body**:
```json
{
  "calculation_type": "natal_chart",
  "birth_data": {
    "date": "1990-08-15",
    "time": "14:30",
    "location": {
      "latitude": 55.7558,
      "longitude": 37.6176,
      "timezone": "Europe/Moscow"
    }
  },
  "options": {
    "house_system": "Placidus",
    "zodiac_type": "Tropical",
    "include_aspects": true,
    "include_arabic_parts": true
  }
}
```

**Response**:
```json
{
  "calculation_id": "calc_123456",
  "natal_chart": {
    "planets": {
      "Sun": {
        "sign": "Leo",
        "degree": 22.5,
        "house": 10,
        "retrograde": false
      }
    },
    "houses": {
      "1": {
        "sign": "Scorpio",
        "degree": 15.3
      }
    },
    "aspects": [
      {
        "planet1": "Sun",
        "planet2": "Moon", 
        "aspect": "Trine",
        "orb": 2.3,
        "exact": false
      }
    ],
    "arabic_parts": {
      "Part of Fortune": {
        "sign": "Sagittarius",
        "degree": 8.7,
        "house": 2
      }
    }
  },
  "interpretation": {
    "dominant_element": "Fire",
    "chart_shape": "Bowl",
    "life_themes": [
      "Creative leadership",
      "Emotional depth",
      "Career focus"
    ]
  }
}
```

### GET /astrology/ephemeris
Get current planetary positions.

**Query Parameters**:
- `date` (optional): Target date (YYYY-MM-DD), defaults to today
- `location` (optional): Latitude,Longitude format
- `format` (optional): `json` or `text`

**Response**:
```json
{
  "date": "2025-08-09",
  "location": {
    "latitude": 55.7558,
    "longitude": 37.6176
  },
  "planets": {
    "Sun": {
      "sign": "Leo",
      "degree": 17.2,
      "longitude": 137.2,
      "house": 10,
      "retrograde": false
    },
    "Moon": {
      "sign": "Cancer", 
      "degree": 5.8,
      "longitude": 95.8,
      "house": 8,
      "retrograde": false
    }
  },
  "lunar_phase": {
    "phase": "Waxing Gibbous",
    "illumination": 0.73,
    "days_to_full": 3
  }
}
```

## Lunar Calendar API

### GET /lunar/calendar
Get lunar calendar information.

**Query Parameters**:
- `month` (optional): Month (1-12), defaults to current
- `year` (optional): Year (YYYY), defaults to current
- `location` (optional): Latitude,Longitude for local calculations

**Response**:
```json
{
  "month": 8,
  "year": 2025,
  "lunar_events": [
    {
      "date": "2025-08-01",
      "event": "New Moon",
      "sign": "Leo",
      "time": "12:30",
      "energy": "New beginnings, creative projects"
    },
    {
      "date": "2025-08-16", 
      "event": "Full Moon",
      "sign": "Aquarius",
      "time": "04:15",
      "energy": "Innovation, community, humanitarian efforts"
    }
  ],
  "void_moon_periods": [
    {
      "start": "2025-08-05T08:30:00Z",
      "end": "2025-08-05T14:20:00Z",
      "advice": "Avoid important decisions"
    }
  ],
  "daily_guidance": {
    "2025-08-09": {
      "moon_sign": "Cancer",
      "energy_level": 85,
      "lucky_colors": ["silver", "white"],
      "lucky_numbers": [2, 7, 11],
      "advice": "Focus on home and family matters"
    }
  }
}
```

## Recommendations API

### GET /api/v1/recommendations
Get personalized recommendations for user.

**Query Parameters**:
- `user_id`: User identifier
- `type` (optional): `content`, `action`, `timing`
- `limit` (optional): Maximum recommendations to return (default: 10)

**Response**:
```json
{
  "recommendations": [
    {
      "id": "rec_123",
      "type": "content",
      "title": "Weekly Love Forecast",
      "description": "Based on your Venus transit...",
      "confidence_score": 85,
      "expires_at": "2025-08-16T00:00:00Z",
      "data": {
        "content_type": "weekly_horoscope",
        "focus_area": "relationships"
      }
    }
  ],
  "user_profile": {
    "interests": {
      "career": 0.8,
      "love": 0.9,
      "health": 0.6
    },
    "preferred_complexity": "intermediate"
  }
}
```

### POST /api/v1/recommendations/feedback
Submit feedback on recommendations.

**Request Body**:
```json
{
  "recommendation_id": "rec_123",
  "user_id": "user_456",
  "feedback_type": "rating",
  "rating": 4,
  "comment": "Very helpful timing advice"
}
```

## Security API

### GET /api/v1/security/user-data
Get user's data summary for GDPR compliance.

**Query Parameters**:
- `user_id`: User identifier
- `verification_code`: GDPR verification code

**Response**:
```json
{
  "user_data": {
    "created_at": "2024-01-15T10:30:00Z",
    "zodiac_sign": "leo",
    "interaction_count": 145,
    "stored_data_types": [
      "zodiac_preferences",
      "session_history",
      "recommendation_feedback"
    ]
  },
  "retention_policy": {
    "data_retention_days": 365,
    "can_request_deletion": true
  }
}
```

### POST /api/v1/security/delete-user-data
Request deletion of user data.

**Request Body**:
```json
{
  "user_id": "user_456",
  "deletion_reason": "No longer using service",
  "verification_code": "verification_123"
}
```

## Error Responses

All endpoints return consistent error structures:

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Invalid zodiac sign provided",
    "details": {
      "field": "zodiac_sign",
      "provided_value": "invalid_sign",
      "allowed_values": ["aries", "taurus", ..., "pisces"]
    },
    "correlation_id": "req_123456"
  }
}
```

**Common Error Codes**:
- `INVALID_REQUEST`: Malformed request data
- `VALIDATION_ERROR`: Invalid parameter values  
- `SERVICE_UNAVAILABLE`: Temporary service issue
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INTERNAL_ERROR`: Unexpected server error

## Rate Limiting

- Default: 100 requests per minute per IP
- Burst: 20 requests per 10 seconds
- Headers returned:
  - `X-RateLimit-Limit`: Request limit
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Reset timestamp

## SDKs and Client Libraries

Currently, the API is REST-based with JSON responses. Community SDKs:
- Python: `astroloh-python-sdk` (unofficial)
- JavaScript: `astroloh-js` (unofficial)

For official SDK development, contact the development team.

## Interactive API Documentation

When running in development mode (`DEBUG=true`):
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

In production, these endpoints are disabled for security.

## WebSocket Support

Real-time updates for:
- Live astrological events
- Session state changes
- Personalized notifications

**Connection**: `ws://localhost:8000/ws/{user_id}`

**Message Format**:
```json
{
  "type": "astrological_event",
  "data": {
    "event": "moon_phase_change", 
    "details": {
      "new_phase": "Full Moon",
      "sign": "Aquarius",
      "timestamp": "2025-08-16T04:15:00Z"
    }
  }
}
```

## Performance Characteristics

- **Response Time**: <500ms for cached requests, <3s for complex calculations
- **Availability**: 99.9% uptime target
- **Caching**: Redis-based intelligent caching with TTL optimization
- **Background Processing**: Async handling for CPU-intensive astrological calculations
- **Rate Limiting**: Configurable per-endpoint limits

