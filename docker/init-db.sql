-- Initialize KASH Platform Database
-- This script runs when PostgreSQL container starts for the first time

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create indexes for full-text search (will be useful for CV analysis)
CREATE INDEX IF NOT EXISTS idx_trgm_search ON pg_trgm;

-- Set default timezone
SET timezone = 'UTC';

-- Create custom types for KASH scoring
CREATE TYPE kash_domain AS ENUM ('knowledge', 'abilities', 'skills', 'intelligence');
CREATE TYPE assessment_status AS ENUM ('pending', 'in_progress', 'completed', 'failed');

-- Create custom functions for scoring calculations
CREATE OR REPLACE FUNCTION calculate_kash_score(
    knowledge_score NUMERIC,
    abilities_score NUMERIC, 
    skills_score NUMERIC,
    intelligence_score NUMERIC,
    knowledge_weight NUMERIC DEFAULT 0.25,
    abilities_weight NUMERIC DEFAULT 0.25,
    skills_weight NUMERIC DEFAULT 0.25,
    intelligence_weight NUMERIC DEFAULT 0.25
) RETURNS NUMERIC AS $$
BEGIN
    RETURN (
        knowledge_score * knowledge_weight +
        abilities_score * abilities_weight +
        skills_score * skills_weight +
        intelligence_score * intelligence_weight
    );
END;
$$ LANGUAGE plpgsql;

-- Create function for similarity search (useful for job matching)
CREATE OR REPLACE FUNCTION text_similarity(text1 TEXT, text2 TEXT) RETURNS NUMERIC AS $$
BEGIN
    RETURN similarity(text1, text2);
END;
$$ LANGUAGE plpgsql;

-- Grant permissions to the application user
GRANT ALL ON SCHEMA public TO kash_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO kash_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO kash_user;

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'KASH Platform database initialized successfully';
END $$;
