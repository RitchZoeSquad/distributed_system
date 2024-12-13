# PC2 - SERP (Search Engine Results Page) Worker

PC2 handles search engine result processing and analysis.

## Directory Structure

### /src
- `api/` - SERP API endpoints
  - `serp_api.py` - Search engine results processing
  - `health.py` - Health check endpoints
- `workers/` - Background workers
  - `serp_worker.py` - SERP processing worker

### /config
- `config.py` - Service configuration

### /tests
- Unit and integration tests

## Key Responsibilities
1. Search Engine Results Processing
2. Result Analysis
3. Data Enrichment 