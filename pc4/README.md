# PC4 - Domain, Email, and Security Analysis

PC4 handles domain validation, email verification, security analysis, and data leak detection.

## Directory Structure

### /src
- `api/` - API endpoints
  - `domain_email_api.py` - Domain and email validation
  - `shodan_api.py` - Shodan integration
  - `leak_check_api.py` - Data leak checking (LeakCheck)
  - `checkleak_api.py` - CheckLeak integration (Dehashed)
  - `health.py` - Health check endpoints
- `workers/` - Background workers
  - `domain_email_worker.py` - Domain/email processing
  - `shodan_worker.py` - Shodan data processing
  - `leak_check_worker.py` - Leak checking worker
- `cache/` - Caching implementations
  - `shodan_cache.py` - Shodan data caching
  - `leak_cache.py` - Leak check results caching
- `db/` - Database interactions
  - `postgres.py` - PostgreSQL connection pool

### /config
- `config.py` - Service configuration
- `.env` - Environment variables including:  ```env
  DOMAIN_API_KEY=ta_5xbwm66o5844vy6mqdpecnplz83wyhcq6uwaz
  EMAIL_API_KEY=ts_27bd86ee-7947-46f5-b695-5f32a217be2e
  LEAKCHECK_API_KEY=ca2d7495ae969ec724f5e8219d546b297967bf30
  DEHASHED_API_KEY=AC4AB35B-63E1-4C33-BA5C-54D037BF7656
  SHODAN_API_KEY=your_shodan_api_key  ```

### /tests
- Unit and integration tests

## Key Responsibilities
1. Domain Validation
2. Email Verification
3. Security Analysis via Shodan
4. Data Leak Detection using:
   - LeakCheck API
   - CheckLeak API (Dehashed)
5. Cache Management

## API Services Integration
- Tomba API for email validation
- Shodan API for security analysis
- LeakCheck API for data breach detection
- Dehashed API (via CheckLeak) for comprehensive leak checking

## Database Tables
- `domain_email_data` - Domain and email validation results
- `email_leak_data` - Data leak check results
- `shodan_searches` - Shodan search results
- `api_usage` - Track API usage and limits

## Rate Limits
- LeakCheck: 200 checks per day
- Dehashed: Based on subscription
- Shodan: Configurable in settings
- Domain/Email: 333 combined checks per day