-- Enable PostgreSQL extensions for similarity search
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS uuid-ossp;

-- Create cybersecurity database schema
CREATE SCHEMA IF NOT EXISTS cybersecurity;

-- Create table for storing security incidents
CREATE TABLE IF NOT EXISTS cybersecurity.security_incidents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    payload TEXT NOT NULL,
    attack_type VARCHAR(100),
    severity VARCHAR(20),
    mitre_id VARCHAR(20),
    source_ip INET,
    user_agent TEXT,
    blocked BOOLEAN DEFAULT FALSE,
    risk_score FLOAT,
    metadata JSONB
);

-- Create table for payload analysis results
CREATE TABLE IF NOT EXISTS cybersecurity.payload_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    payload_hash VARCHAR(64) UNIQUE NOT NULL,
    payload TEXT NOT NULL,
    analysis_result JSONB,
    confidence_score FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_security_incidents_timestamp ON cybersecurity.security_incidents(timestamp);
CREATE INDEX IF NOT EXISTS idx_security_incidents_attack_type ON cybersecurity.security_incidents(attack_type);
CREATE INDEX IF NOT EXISTS idx_security_incidents_severity ON cybersecurity.security_incidents(severity);
CREATE INDEX IF NOT EXISTS idx_security_incidents_blocked ON cybersecurity.security_incidents(blocked);
CREATE INDEX IF NOT EXISTS idx_payload_analysis_hash ON cybersecurity.payload_analysis(payload_hash);
CREATE INDEX IF NOT EXISTS idx_payload_analysis_confidence ON cybersecurity.payload_analysis(confidence_score);

-- Create triggers for updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_payload_analysis_updated_at 
    BEFORE UPDATE ON cybersecurity.payload_analysis 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions
GRANT USAGE ON SCHEMA cybersecurity TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA cybersecurity TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA cybersecurity TO postgres;