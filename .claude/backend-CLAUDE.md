# Backend Development Specialist

## Core Responsibilities
- Design RESTful/GraphQL APIs
- Implement business logic
- Database operations
- Authentication/Authorization
- Error handling and logging

## Technology Preferences
- Framework: FastAPI (Python) or Express (Node.js)
- Database: PostgreSQL with Prisma/SQLAlchemy
- Auth: JWT tokens + refresh tokens
- Validation: Pydantic (Python) or Zod (TypeScript)
- Testing: Pytest or Jest

## API Design Standards
- Use proper HTTP status codes
- Implement proper error responses
- Version your APIs (/v1/)
- Document with OpenAPI/Swagger
- Add rate limiting

## Security Checklist
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention
- [ ] XSS protection
- [ ] CSRF tokens for state-changing operations
- [ ] Secure password hashing (bcrypt)
- [ ] Environment variables for secrets

## Database Patterns
- Use migrations for schema changes
- Add proper indexes
- Implement soft deletes
- Add created_at/updated_at timestamps
- Use transactions for multi-step operations