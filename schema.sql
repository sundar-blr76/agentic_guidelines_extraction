-- schema.sql

-- Enable the pgvector extension for embedding storage and search
CREATE EXTENSION IF NOT EXISTS vector;

-- Drop existing tables to ensure a clean slate
DROP TABLE IF EXISTS guideline CASCADE;
DROP TABLE IF EXISTS document CASCADE;
DROP TABLE IF EXISTS portfolio CASCADE;

-- Create the portfolio table
CREATE TABLE portfolio (
    portfolio_id VARCHAR(255) PRIMARY KEY,
    portfolio_name TEXT NOT NULL
);

-- Create the document table
CREATE TABLE document (
    doc_id VARCHAR(255) PRIMARY KEY,
    portfolio_id VARCHAR(255) REFERENCES portfolio(portfolio_id) ON DELETE CASCADE,
    doc_name TEXT NOT NULL,
    doc_date DATE,
    human_readable_digest TEXT
);

-- Create the guideline table
CREATE TABLE guideline (
    portfolio_id VARCHAR(255) REFERENCES portfolio(portfolio_id) ON DELETE CASCADE,
    rule_id VARCHAR(255),
    doc_id VARCHAR(255) NOT NULL, -- Keep track of the source document for reference
    part TEXT,
    section TEXT,
    subsection TEXT,
    text TEXT NOT NULL,
    page INTEGER,
    provenance TEXT,
    structured_data JSONB,
    embedding vector(768), -- For 'models/embedding-001'
    PRIMARY KEY (portfolio_id, rule_id)
);