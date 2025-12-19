-- Companies master table
CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    sector VARCHAR(100),
    industry VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Financial statements metadata
CREATE TABLE IF NOT EXISTS financial_statements (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    statement_type VARCHAR(50) NOT NULL, -- 'balance_sheet' or 'income_statement'
    period_type VARCHAR(20) NOT NULL,    -- 'quarterly' or 'annual'
    period_date DATE NOT NULL,
    fiscal_year INTEGER,
    fiscal_quarter INTEGER,
    source VARCHAR(50),                  -- 'yfinance', 'nse', 'bse'
    raw_data JSONB,                      -- Store original API response
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, statement_type, period_type, period_date)
);

-- Line items (normalized financial data)
CREATE TABLE IF NOT EXISTS financial_line_items (
    id SERIAL PRIMARY KEY,
    statement_id INTEGER REFERENCES financial_statements(id) ON DELETE CASCADE,
    line_item_name VARCHAR(255) NOT NULL,
    line_item_value NUMERIC(20, 2),
    currency VARCHAR(10) DEFAULT 'INR',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(statement_id, line_item_name)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_companies_ticker ON companies(ticker);
CREATE INDEX IF NOT EXISTS idx_statements_company_period ON financial_statements(company_id, period_date DESC);
CREATE INDEX IF NOT EXISTS idx_line_items_statement ON financial_line_items(statement_id);
CREATE INDEX IF NOT EXISTS idx_line_items_name ON financial_line_items(line_item_name);
