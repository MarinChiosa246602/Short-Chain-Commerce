"""
Database Integration for logistics data extraction.

Provides:
- SQLite/PostgreSQL database storage for extraction results
- Result querying and retrieval
- Data persistence and history tracking
"""

import json
import sqlite3
import functools
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Simple in-memory cache for frequent queries
_cache: Dict[str, Any] = {}
_CACHE_TTL_SECONDS = 300


def cached(ttl: int = 300):
    """Simple decorator for caching function results."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{args}:{kwargs}"
            if cache_key in _cache:
                result, timestamp = _cache[cache_key]
                if datetime.now().timestamp() - timestamp < ttl:
                    return result
            result = func(*args, **kwargs)
            _cache[cache_key] = (result, datetime.now().timestamp())
            return result

        return wrapper

    return decorator


class DatabaseManager:
    """
    Database manager for extraction results.

    Supports SQLite (default) and PostgreSQL.
    """

    def __init__(
        self,
        db_path: str = "data/extractions.db",
        db_type: str = "sqlite",
        postgres_url: Optional[str] = None,
    ):
        """
        Initialize database manager.

        Args:
            db_path: Path to SQLite database or data directory
            db_type: Database type ('sqlite' or 'postgresql')
            postgres_url: PostgreSQL connection string (required for PostgreSQL)
        """
        self.db_type = db_type
        self.db_path = db_path

        if db_type == "postgresql":
            if not postgres_url:
                raise ValueError("PostgreSQL connection string required")
            self.postgres_url = postgres_url
        else:
            # Ensure data directory exists
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def get_connection(self):
        """Get database connection context manager."""
        if self.db_type == "postgresql":
            import psycopg2

            conn = psycopg2.connect(self.postgres_url)
        else:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row

        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialize(self):
        """Initialize database schema."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Extractions table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS extractions (
                    id TEXT PRIMARY KEY,
                    image_id TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    source_farm TEXT,
                    destination TEXT,
                    status TEXT NOT NULL,
                    is_valid BOOLEAN,
                    processing_time_ms REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Products table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    extraction_id TEXT NOT NULL,
                    product_id TEXT NOT NULL,
                    product_name TEXT,
                    quantity INTEGER,
                    unit TEXT,
                    expiry_date DATETIME,
                    storage_location TEXT,
                    condition TEXT,
                    FOREIGN KEY (extraction_id) REFERENCES extractions(id)
                )
            """
            )

            # Create index for faster queries
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_extractions_timestamp
                ON extractions(timestamp)
            """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_extractions_source_farm
                ON extractions(source_farm)
            """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_products_product_id
                ON products(product_id)
            """
            )

            # Anomalies table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS anomalies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    extraction_id TEXT,
                    batch_id TEXT,
                    anomaly_type TEXT NOT NULL,
                    severity TEXT,
                    details TEXT,
                    detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (extraction_id) REFERENCES extractions(id)
                )
            """
            )

    def save_extraction(
        self,
        extraction_id: str,
        image_id: str,
        timestamp: datetime,
        source_farm: Optional[str],
        destination: Optional[str],
        status: str,
        is_valid: bool,
        processing_time_ms: float,
        products: List[Dict[str, Any]],
        missing_fields: Optional[List[str]] = None,
        low_confidence_fields: Optional[List[str]] = None,
    ):
        """
        Save an extraction result to the database.

        Args:
            extraction_id: Unique extraction identifier
            image_id: Source image identifier
            timestamp: Processing timestamp
            source_farm: Source farm identifier
            destination: Destination identifier
            status: Extraction status (success/partial/error)
            is_valid: Whether extraction is valid
            processing_time_ms: Processing time in milliseconds
            products: List of extracted products
            missing_fields: Fields that could not be extracted
            low_confidence_fields: Fields with low confidence
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Insert extraction record
            cursor.execute(
                """
                INSERT OR REPLACE INTO extractions
                (id, image_id, timestamp, source_farm, destination,
                 status, is_valid, processing_time_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    extraction_id,
                    image_id,
                    timestamp.isoformat(),
                    source_farm,
                    destination,
                    status,
                    is_valid,
                    processing_time_ms,
                ),
            )

            # Insert products
            for product in products:
                cursor.execute(
                    """
                    INSERT INTO products
                    (extraction_id, product_id, product_name, quantity,
                     unit, expiry_date, storage_location, condition)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        extraction_id,
                        product.get("product_id"),
                        product.get("product_name"),
                        product.get("quantity"),
                        product.get("unit"),
                        product.get("expiry_date").isoformat() if product.get("expiry_date") else None,
                        product.get("storage_location"),
                        product.get("condition"),
                    ),
                )

            # Store metadata as JSON
            if missing_fields or low_confidence_fields:
                metadata = {
                    "missing_fields": missing_fields or [],
                    "low_confidence_fields": low_confidence_fields or [],
                }
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO extraction_metadata
                    (extraction_id, metadata)
                    VALUES (?, ?)
                """,
                    (extraction_id, json.dumps(metadata)),
                )

    def save_anomaly(
        self,
        anomaly_type: str,
        severity: str,
        details: Dict[str, Any],
        extraction_id: Optional[str] = None,
        batch_id: Optional[str] = None,
    ):
        """Save an anomaly record."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO anomalies (extraction_id, batch_id, anomaly_type, severity, details)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    extraction_id,
                    batch_id,
                    anomaly_type,
                    severity,
                    json.dumps(details),
                ),
            )

    def get_extraction(self, extraction_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific extraction by ID.

        Args:
            extraction_id: Extraction identifier

        Returns:
            Extraction record or None
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get extraction record
            cursor.execute("SELECT * FROM extractions WHERE id = ?", (extraction_id,))
            row = cursor.fetchone()

            if not row:
                return None

            extraction = dict(row)

            # Get products
            cursor.execute("SELECT * FROM products WHERE extraction_id = ?", (extraction_id,))
            extraction["products"] = [dict(p) for p in cursor.fetchall()]

            return extraction

    def query_extractions(
        self,
        source_farm: Optional[str] = None,
        destination: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Query extractions with filters.

        Args:
            source_farm: Filter by source farm
            destination: Filter by destination
            start_date: Filter by start date
            end_date: Filter by end date
            status: Filter by status
            limit: Maximum results
            offset: Result offset for pagination

        Returns:
            List of extraction records
        """
        query = "SELECT * FROM extractions WHERE 1=1"
        params = []

        if source_farm:
            query += " AND source_farm = ?"
            params.append(source_farm)

        if destination:
            query += " AND destination = ?"
            params.append(destination)

        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.isoformat())

        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.isoformat())

        if status:
            query += " AND status = ?"
            params.append(status)

        query += f" ORDER BY timestamp DESC LIMIT {limit} OFFSET {offset}"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get extraction statistics.

        Args:
            start_date: Start date for statistics
            end_date: End date for statistics

        Returns:
            Statistics dictionary
        """
        query = """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful,
                SUM(CASE WHEN status = 'partial' THEN 1 ELSE 0 END) as partial,
                SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as failed,
                AVG(processing_time_ms) as avg_processing_time,
                MIN(timestamp) as first_extraction,
                MAX(timestamp) as last_extraction
            FROM extractions
        """
        params = []

        if start_date:
            query += " WHERE timestamp >= ?"
            params.append(start_date.isoformat())

        if end_date:
            if "WHERE" in query:
                query += " AND timestamp <= ?"
            else:
                query += " WHERE timestamp <= ?"
            params.append(end_date.isoformat())

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()

            return {
                "total": row["total"] or 0,
                "successful": row["successful"] or 0,
                "partial": row["partial"] or 0,
                "failed": row["failed"] or 0,
                "avg_processing_time_ms": row["avg_processing_time"] or 0,
                "first_extraction": row["first_extraction"],
                "last_extraction": row["last_extraction"],
            }

    def get_product_inventory(self) -> List[Dict[str, Any]]:
        """
        Get aggregated product inventory.

        Returns:
            List of products with total quantities
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    product_id,
                    product_name,
                    SUM(quantity) as total_quantity,
                    COUNT(*) as extraction_count,
                    AVG(CASE WHEN expiry_date IS NOT NULL THEN
                        julianday(expiry_date) - julianday('now')
                    END) as avg_days_until_expiry
                FROM products
                GROUP BY product_id, product_name
                ORDER BY total_quantity DESC
            """
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_recent_anomalies(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent anomalies.

        Args:
            limit: Maximum anomalies to return

        Returns:
            List of anomaly records
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM anomalies
                ORDER BY detected_at DESC
                LIMIT ?
            """,
                (limit,),
            )
            anomalies = []
            for row in cursor.fetchall():
                anomaly = dict(row)
                anomaly["details"] = json.loads(anomaly["details"] or "{}")
                anomalies.append(anomaly)
            return anomalies


# Convenience function
def get_database_manager(
    db_path: str = "data/extractions.db",
) -> DatabaseManager:
    """Get or create database manager instance."""
    return DatabaseManager(db_path=db_path)


if __name__ == "__main__":
    # Example usage
    db = get_database_manager()
    db.initialize()

    # Save a sample extraction
    db.save_extraction(
        extraction_id="test-001",
        image_id="img-001",
        timestamp=datetime.utcnow(),
        source_farm="Farm-001",
        destination="Warehouse-A",
        status="success",
        is_valid=True,
        processing_time_ms=250.5,
        products=[
            {
                "product_id": "TOM-001",
                "product_name": "Tomato",
                "quantity": 24,
                "unit": "crate",
                "expiry_date": datetime(2026, 12, 25),
                "storage_location": "Fridge-A",
                "condition": "excellent",
            }
        ],
        missing_fields=[],
        low_confidence_fields=[],
    )

    # Query extractions
    extractions = db.query_extractions(source_farm="Farm-001")
    print(f"Found {len(extractions)} extractions")

    # Get statistics
    stats = db.get_statistics()
    print(f"Statistics: {json.dumps(stats, indent=2, default=str)}")

    # Get inventory
    inventory = db.get_product_inventory()
    print(f"Inventory: {json.dumps(inventory, indent=2, default=str)}")
