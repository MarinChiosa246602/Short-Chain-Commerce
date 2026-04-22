-- Initialize database schema for Short Chain Commerce
-- This script runs automatically on PostgreSQL container startup

-- Create extension for UUID support
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_extractions_timestamp ON extractions(timestamp);
CREATE INDEX IF NOT EXISTS idx_extractions_source_farm ON extractions(source_farm);
CREATE INDEX IF NOT EXISTS idx_extractions_destination ON extractions(destination);
CREATE INDEX IF NOT EXISTS idx_products_extraction_id ON products(extraction_id);
CREATE INDEX IF NOT EXISTS idx_products_product_id ON products(product_id);
CREATE INDEX IF NOT EXISTS idx_anomalies_detected_at ON anomalies(detected_at);

-- Create view for recent extractions summary
CREATE OR REPLACE VIEW recent_extractions_summary AS
SELECT
    DATE(timestamp) as date,
    COUNT(*) as total_extractions,
    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful,
    SUM(CASE WHEN status = 'partial' THEN 1 ELSE 0 END) as partial,
    SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as failed,
    AVG(processing_time_ms) as avg_processing_time
FROM extractions
WHERE timestamp >= NOW() - INTERVAL '30 days'
GROUP BY DATE(timestamp)
ORDER BY date DESC;

-- Grant permissions if needed
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO staging_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO staging_user;
