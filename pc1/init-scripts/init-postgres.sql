-- Create necessary tables
CREATE TABLE IF NOT EXISTS businesses (
    id SERIAL PRIMARY KEY,
    business_id VARCHAR(100) UNIQUE,
    name VARCHAR(255),
    address TEXT,
    phone VARCHAR(50),
    processed_date DATE,
    processed_by VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS domain_email_data (
    id SERIAL PRIMARY KEY,
    business_id VARCHAR(100) REFERENCES businesses(business_id),
    domain VARCHAR(255),
    organization_info JSONB,
    emails JSONB,
    validation_status VARCHAR(50),
    processed_date TIMESTAMP,
    processed_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS phone_validation (
    id SERIAL PRIMARY KEY,
    business_id VARCHAR(100) REFERENCES businesses(business_id),
    phone VARCHAR(50),
    validation_status VARCHAR(50),
    validation_details JSONB,
    processed_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS serp_results (
    id SERIAL PRIMARY KEY,
    business_id VARCHAR(100) REFERENCES businesses(business_id),
    query TEXT,
    results JSONB,
    processed_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS api_usage (
    id SERIAL PRIMARY KEY,
    api_type VARCHAR(50),
    usage_date DATE,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_business_id ON businesses(business_id);
CREATE INDEX IF NOT EXISTS idx_business_status ON businesses(status);
CREATE INDEX IF NOT EXISTS idx_domain ON domain_email_data(domain);
CREATE INDEX IF NOT EXISTS idx_phone ON phone_validation(phone);
CREATE INDEX IF NOT EXISTS idx_api_usage_date ON api_usage(usage_date, api_type);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_domain_email_business_id ON domain_email_data(business_id);
CREATE INDEX IF NOT EXISTS idx_domain_email_domain ON domain_email_data(domain);
CREATE INDEX IF NOT EXISTS idx_domain_email_processed_date ON domain_email_data(processed_date);
CREATE INDEX IF NOT EXISTS idx_domain_email_validation_status ON domain_email_data(validation_status);
CREATE INDEX IF NOT EXISTS idx_domain_email_org_info ON domain_email_data USING gin (organization_info);
CREATE INDEX IF NOT EXISTS idx_domain_email_emails ON domain_email_data USING gin (emails);