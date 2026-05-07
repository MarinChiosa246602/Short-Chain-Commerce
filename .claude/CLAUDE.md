 Code Quality Assessment Report

  🔴 Critical Issues (Must Fix)

  1. Duplicate logging setup in main.py (lines
  37-42)

  setup_logging(level=os.getenv("LOG_LEVEL",
  "INFO"))  # line 38
  setup_logging(level=os.getenv("LOG_LEVEL",
  "INFO"))  # line 41 - DUPLICATE
  Impact: Redundant initialization, potential
  conflicts

  2. Inconsistent datetime handling

  - save_extraction() expects datetime object but
  passes timestamp.isoformat() (string)
  - query_extractions() now checks isinstance(ts,
  datetime) but this creates inconsistency
  - get_expiring_products() joins with extractions
  but expiry_date comparison may fail with string
  dates

  Impact: Potential crashes, incorrect date
  comparisons

  3. Insecure password comparison in login endpoint
  (lines 212-217)

  if request.username == "admin" and
  request.password == admin_password:
  Impact: Timing attack vulnerability, passwords
  stored in plain text

  4. Hash function non-determinism in deliveries
  endpoint (line 780)

  dest_hash = hash(ext.get("destination", "")) %
  10000
  Python's hash() is randomized between sessions,
  causing inconsistent location generation

  Impact: Unreliable delivery locations

  5. Missing authentication on several endpoints:

  - /api/v1/extractions (line 557)
  - /api/v1/extractions/{id} (line 615)
  - /api/v1/analytics/summary (line 648)
  - /api/v1/health/detailed (line 482)

  Impact: Unprotected data access

  ---
  🟠 High Priority Issues

  6. login_attempts dictionary never cleaned (line
  175)

  Memory leak - old IP entries are never removed

  7. Inconsistent product data structure between
  endpoints

  - /api/v1/extract returns nested data.products
  - /api/v1/inventory returns flat products array
  - Frontend components expect different structures

  8. SQL injection vulnerability in
  query_extractions (line 375)

  query += f" ORDER BY timestamp DESC LIMIT {limit}
  OFFSET {offset}"
  User-controlled limit and offset are interpolated
  directly

  9. Missing error handling for missing product
  expiry_date

  Multiple places assume product["expiry_date"]
  exists without null checks

  10. Frontend: Unused import in
  ProductDashboard.jsx (line 7)

  import api, { getInventory } from
  '../services/api'
  api is imported but never used (only getInventory
  is called)

  ---
  🟡 Medium Priority Issues

  11. Code duplication in extract_data response
  (lines 315-366)

  Nearly identical product mapping code for success
  and partial responses

  12. Magic numbers throughout the codebase

  - 50 files limit in batch (line 400)
  - 100 limit in deliveries query (line 775)
  - 14 days default for expiring products
  - Should be constants/config

  13. Missing input validation

  - No validation for days parameter in
  /api/v1/alerts/expiring
  - No validation for limit parameter (could be
  abused with large values)

  14. Inconsistent response format from
  query_extractions

  The new format wraps data but the API endpoint
  /api/v1/extractions (lines 578-595) transforms it
  back, creating confusion

  15. Environment variable .env.example incomplete

  Missing: JWT_SECRET_KEY,
  ACCESS_TOKEN_EXPIRE_MINUTES, RATE_LIMIT_REQUESTS,
  RATE_LIMIT_WINDOW_SECONDS

  ---
  🟢 Low Priority / Best Practices

  16. Import statement organization

  Mixed order in several files (e.g., main.py has
  local imports after stdlib)

  17. Type hints inconsistent

  Some functions have complete type hints, others
  are missing them

  18. Duplicate datetime imports

  Lines 10 and 557 both import datetime

  19. Hardcoded values in .env.example

  Should use placeholder values like
  your_password_here instead of empty values

  20. Frontend: Mock data fallback masks real issues

  Every API call falls back to mock data on error,
  making debugging difficult

  ---
  Summary Table

  ┌──────────┬─────────────┬──────────────────┐
  │ Priority │ Issue Count │ Estimated Effort │
  ├──────────┼─────────────┼──────────────────┤
  │ Critical │ 5           │ 4-6 hours        │
  ├──────────┼─────────────┼──────────────────┤
  │ High     │ 5           │ 3-4 hours        │
  ├──────────┼─────────────┼──────────────────┤
  │ Medium   │ 5           │ 2-3 hours        │
  ├──────────┼─────────────┼──────────────────┤
  │ Low      │ 5           │ 1-2 hours        │
  └──────────┴─────────────┴──────────────────┘

  Total estimated remediation: 10-15 hours

  ---
  Would you like me to fix any of these issues? I'd
  recommend starting with:
  1. The duplicate logging setup (quick fix)
  Would you like me to fix any of these issues? I'd recommend starting with:

  15. Environment variable .env.example incomplete

  Missing: JWT_SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES, RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW_SECONDS

  ---
  🟢 Low Priority / Best Practices

  16. Import statement organization

  Mixed order in several files (e.g., main.py has local imports after stdlib)

  17. Type hints inconsistent

  Some functions have complete type hints, others are missing them

  18. Duplicate datetime imports

  Lines 10 and 557 both import datetime

  19. Hardcoded values in .env.example

  Should use placeholder values like your_password_here instead of empty values

  20. Frontend: Mock data fallback masks real issues

  Every API call falls back to mock data on error, making debugging difficult

  ---
  Summary Table

  ┌──────────┬─────────────┬──────────────────┐
  │ Priority │ Issue Count │ Estimated Effort │
  ├──────────┼─────────────┼──────────────────┤
  │ Critical │ 5           │ 4-6 hours        │
  ├──────────┼─────────────┼──────────────────┤
  │ High     │ 5           │ 3-4 hours        │
  ├──────────┼─────────────┼──────────────────┤
  │ Medium   │ 5           │ 2-3 hours        │
  ├──────────┼─────────────┼──────────────────┤
  │ Low      │ 5           │ 1-2 hours        │
  └──────────┴─────────────┴──────────────────┘

  Total estimated remediation: 10-15 hours

  ---
  Would you like me to fix any of these issues? I'd recommend starting with:
  1. The duplicate logging setup (quick fix)
  2. Adding authentication to the missing endpoints
  3. Fixing the hash() non-determinism issue
  4. Adding input validation