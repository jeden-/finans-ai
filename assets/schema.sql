-- Drop existing indices if they exist
DROP INDEX IF EXISTS idx_transactions_created_at;
DROP INDEX IF EXISTS idx_transactions_type;

CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    description TEXT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    type VARCHAR(10) NOT NULL,
    category VARCHAR(50) NOT NULL,
    cycle VARCHAR(10) NOT NULL,
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP NOT NULL,
    transaction_text TEXT,  -- For storing original descriptions
    metadata JSONB         -- For future AI analysis
);

-- Recreate indices
CREATE INDEX idx_transactions_created_at ON transactions(created_at);
CREATE INDEX idx_transactions_type ON transactions(type);
CREATE INDEX idx_transactions_metadata ON transactions USING GIN (metadata);
