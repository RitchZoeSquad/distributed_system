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
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    leak_data JSONB
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

CREATE TABLE IF NOT EXISTS email_leak_data (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255),
    total_leaks INTEGER,
    has_password_leak BOOLEAN,
    dehashed_results JSONB,
    leakcheck_results JSONB,
    processed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add Shodan-related tables
CREATE TABLE IF NOT EXISTS shodan_searches (
    id SERIAL PRIMARY KEY,
    search_query VARCHAR(255),
    ip_address VARCHAR(45),
    port INTEGER,
    organization VARCHAR(255),
    hostnames JSONB,
    additional_info JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS shodan_host_info (
    id SERIAL PRIMARY KEY,
    ip_address VARCHAR(45) UNIQUE,
    host_data JSONB,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    vulnerabilities JSONB,
    ports JSONB,
    tags TEXT[]
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
CREATE INDEX IF NOT EXISTS idx_email_leak_email ON email_leak_data(email);
CREATE INDEX IF NOT EXISTS idx_email_leak_has_password ON email_leak_data(has_password_leak);
CREATE INDEX IF NOT EXISTS idx_domain_email_leak_data ON domain_email_data USING gin (leak_data);

-- Add indexes
CREATE INDEX idx_shodan_searches_ip ON shodan_searches(ip_address);
CREATE INDEX idx_shodan_searches_org ON shodan_searches(organization);
CREATE INDEX idx_shodan_host_info_ip ON shodan_host_info(ip_address);