# PC3 - Phone Validation Worker

PC3 manages phone number validation and analysis.

## Directory Structure

### /src
- `api/` - Phone validation endpoints
  - `phone_api.py` - Phone validation logic
  - `health.py` - Health check endpoints
- `workers/` - Background workers
  - `phone_worker.py` - Phone validation worker

### /config
- `config.py` - Service configuration

### /tests
- Unit and integration tests

## Key Responsibilities
1. Phone Number Validation
2. Phone Data Analysis
3. Phone Information Enrichment 