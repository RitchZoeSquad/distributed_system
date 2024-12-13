# PC1 - Central Service Coordinator

PC1 serves as the central coordinator for the entire system, managing core services and routing.

## Directory Structure

### /src
- `api/` - Core API endpoints
  - `business_search_api.py` - Handles business search requests using Outscraper API
  - `health.py` - Health check endpoints
- `service_registry.py` - Service discovery and registration system
- `outscraper/` - Business search functionality
  - `client.py` - Outscraper API client
  - `models.py` - Data models for business search

### /config
- `rabbitmq.conf` - RabbitMQ message broker configuration
- `redis.conf` - Redis cache configuration
- `postgres.conf` - PostgreSQL database configuration
- `.env` - Environment variables including:
  ```env
  OUTSCRAPER_API_KEY=Z29vZ2xlLW9hdXRoMnwxMTc4...
  PC1_IP=185.249.196.192
  ```

### /init-scripts
- `init-postgres.sql` - Database schema and initial setup
- `init-rabbitmq.sh` - RabbitMQ queues and exchanges setup
- `init-redis.sh` - Redis initialization

### /monitoring
- `prometheus.yml` - Prometheus monitoring configuration
- `grafana/` - Grafana dashboards and configuration

## Key Responsibilities
1. Service Discovery
2. Message Routing
3. Database Management
4. Cache Coordination
5. System Monitoring
6. Business Search via Outscraper API

## API Keys and Services
- Outscraper API for business search
- RabbitMQ for message queuing
- Redis for caching
- PostgreSQL for data storage

## Database Tables
- `businesses` - Store business search results
- `api_usage` - Track API usage and limits