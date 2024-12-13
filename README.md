# Distributed Business Data Enrichment System

A scalable, distributed system for enriching business data using multiple APIs and services. The system is designed to handle business searches, domain/email validation, and SERP (Search Engine Results Page) data collection in a distributed manner.

## System Architecture

The system consists of 5 distributed nodes (PC1-PC5), each handling specific tasks:

### PC1 (Central Coordinator)
- Central PostgreSQL database
- RabbitMQ message broker
- Redis cache
- API endpoints for initiating searches
- Load balancing and request distribution

### PC2 & PC3 (Business Search Workers)
- Handle business search requests using Outscraper API
- Process up to 166 requests per day (83 each)
- Implement rate limiting and error handling

### PC4 (Domain & Email Validation)
- Domain search using Tomba.io API
- Email enrichment and validation
- Handles up to 333 validations per day

### PC5 (SERP Worker)
- Processes SERP requests using SpaceSerp API
- Caches results for optimization
- Implements advanced rate limiting

## Prerequisites

- Docker and Docker Compose
- PostgreSQL 13+
- Redis 6.2+
- RabbitMQ 3+
- Python 3.9+

## Configuration

Each PC requires specific environment variables. Example `.env` file:
