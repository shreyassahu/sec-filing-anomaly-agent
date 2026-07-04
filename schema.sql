CREATE TABLE companies (
    cik VARCHAR(10) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    ticker VARCHAR(10),
    sector VARCHAR(100),
    sic_code VARCHAR(10)
);

CREATE TABLE filings (
    id SERIAL PRIMARY KEY,
    cik VARCHAR(10) REFERENCES companies(cik),
    accession_number VARCHAR(25) NOT NULL UNIQUE,
    filing_type VARCHAR(10) NOT NULL,
    filed_date DATE,
    period_of_report DATE,
    raw_url TEXT
);

CREATE TABLE financial_metrics (
    id SERIAL PRIMARY KEY,
    filing_id INTEGER REFERENCES filings(id),
    metric_name VARCHAR(50) NOT NULL,
    metric_value NUMERIC,
    unit VARCHAR(10) DEFAULT 'USD',
    fiscal_year INTEGER,
    fiscal_quarter INTEGER
);

CREATE TABLE anomalies (
    id SERIAL PRIMARY KEY,
    filing_id INTEGER REFERENCES filings(id),
    metric_name VARCHAR(50) NOT NULL,
    current_value NUMERIC,
    previous_value NUMERIC,
    pct_change NUMERIC,
    severity VARCHAR(20),
    explanation TEXT
);