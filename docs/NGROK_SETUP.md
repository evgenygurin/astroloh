# Ngrok Setup for Astroloh

This guide explains how to set up ngrok tunnels for the Astroloh application to expose both backend and frontend services to the internet.

## Prerequisites

1. **Ngrok Account**: Sign up at [ngrok.com](https://ngrok.com) and get your auth token
2. **Docker & Docker Compose**: Ensure you have Docker installed

## Setup Instructions

### 1. Configure Environment Variables

Copy `.env.example` to `.env` and update the ngrok configuration:

```bash
cp .env.example .env
```

Edit `.env` file and set:

```env
# Ngrok Configuration
NGROK_AUTHTOKEN=your-ngrok-auth-token-here
NGROK_BACKEND_HOSTNAME=your-backend-subdomain.ngrok.io
NGROK_FRONTEND_HOSTNAME=your-frontend-subdomain.ngrok.io
```

### 2. Running with Ngrok

#### Option 1: Built-in Ngrok Services (Recommended)

Run the main application with ngrok tunnels:

```bash
docker-compose up -d
```

This will start:

- Backend service on port 8000
- Frontend service on port 80
- Ngrok tunnel for backend (web interface on port 4040)
- Ngrok tunnel for frontend (web interface on port 4041)

#### Option 2: Separate Ngrok Compose File

Alternatively, use the dedicated ngrok compose file:

```bash
# Start main services first
docker-compose up -d backend frontend db

# Start ngrok tunnels
docker-compose -f docker-compose.ngrok.yml up -d
```

### 3. Access Your Services

Once running, you can access:

- **Backend Tunnel**: Your backend will be available at `https://your-backend-subdomain.ngrok.io`
- **Frontend Tunnel**: Your frontend will be available at `https://your-frontend-subdomain.ngrok.io`
- **Ngrok Web Interface**:
  - Backend: <http://localhost:4040>
  - Frontend: <http://localhost:4041>

### 4. Configuration

The ngrok tunnels are configured directly in the Docker Compose files using simple HTTP tunnel commands. The setup no longer requires separate ngrok configuration files.

**Docker Compose Configuration:**

- Backend tunnel: Exposes `backend:8000` via ngrok
- Frontend tunnel: Exposes `frontend:80` via ngrok
- Auth token: Provided via `NGROK_AUTHTOKEN` environment variable

The tunnels will generate random URLs unless you have a paid ngrok plan that supports custom domains.

## Useful Commands

```bash
# View ngrok logs
docker-compose logs ngrok-backend
docker-compose logs ngrok-frontend

# Stop ngrok tunnels only
docker-compose stop ngrok-backend ngrok-frontend

# Restart ngrok tunnels
docker-compose restart ngrok-backend ngrok-frontend

# View tunnel status
curl http://localhost:4040/api/tunnels  # Backend tunnels
curl http://localhost:4041/api/tunnels  # Frontend tunnels
```

## Troubleshooting

1. **Authentication Error**:
   - Ensure your `NGROK_AUTHTOKEN` is set correctly in your `.env` file
   - Check that the `.env` file is in the same directory as your `docker-compose.yml`
   - Verify the token is not wrapped in quotes in the `.env` file
   - Make sure you're not seeing `${NGROK_AUTHTOKEN}` literally - this means the environment variable isn't being substituted

2. **Environment Variable Issues**:
   - If you see `${NGROK_AUTHTOKEN}` in error messages, the environment variable isn't being loaded
   - Ensure your `.env` file exists and contains: `NGROK_AUTHTOKEN=your-actual-token`
   - Try running with explicit env file: `docker-compose --env-file .env up`

3. **Hostname Issues**: Make sure your hostname is available or remove the hostname parameter for random URLs
4. **Port Conflicts**: Check if ports 4040/4041 are already in use
5. **Network Issues**: Ensure all services are on the same Docker network

## Security Notes

- Never commit your ngrok auth token to version control
- Use ngrok's built-in authentication features for production
- Consider IP whitelisting for sensitive endpoints
- Monitor tunnel usage through ngrok dashboard

## Integration with Yandex Alice

For Yandex Alice integration, use the backend ngrok URL as your webhook endpoint:

```
https://your-backend-subdomain.ngrok.io/api/v1/yandex/webhook
```

## Bypassing Ngrok Warning Page

When accessing ngrok URLs in a browser, you'll see a warning page. To bypass it:

### For API/Webhook Access (Recommended for Yandex Alice)

Add the `ngrok-skip-browser-warning` header to your requests:

```bash
curl -H "ngrok-skip-browser-warning: true" https://your-subdomain.ngrok-io/api/endpoint
```

### For Browser Access

1. Click "Visit Site" on the warning page (visitors only see it once)
2. Or use a browser extension to add custom headers
3. Or upgrade to a paid ngrok plan to remove the warning

### For Development Testing

The warning doesn't affect API calls from services like Yandex Alice - they automatically bypass it.
