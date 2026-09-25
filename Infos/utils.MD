## Global commands

When you clone the project, launch the following:
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
```

Launch and stop the virtual environment:
```bash
source .venv/bin/activate
deactivate
```

Launch the API:
```bash
python -m uvicorn backend.app.main:app --reload
```

Clean the '__pycache__' folders:
```bash
find . -type d -name "__pycache__" -exec rm -rf {} \; && rm -rf .pytest_cache
```

Tests:

```bash
pytest -v
```

## Podman commands

Pull the image for the database:
```bash
podman pull docker.io/library/postgres:17
```

Create the container and database:
```bash
podman run --name transcendence-db -e POSTGRES_USER=transcendence -e POSTGRES_PASSWORD=transcendence_dev -e POSTGRES_DB=transcendence -p 5432:5432 -d docker.io/library/postgres:17
```

Create the test database:
```bash
podman exec -it transcendence-db psql -U transcendence -d transcendence -c "CREATE DATABASE transcendence_test;"
  ```

Start and stop the container:
```bash
podman start transcendence-db
podman stop transcendence-db
```

Clean the database:
```bash
podman exec -it transcendence-db psql -U transcendence -d transcendence -c 'TRUNCATE TABLE users RESTART IDENTITY CASCADE;'
```

Connect to PostgreSQL:
```bash
podman exec -it transcendence-db psql -U transcendence -d transcendence
```

## Alembic commands

Apply everything up to latest:
```bash
alembic -c backend/alembic.ini upgrade head
```

See current database revision:
```bash
alembic -c backend/alembic.ini current
```

See migration history:
```bash
alembic -c backend/alembic.ini history
```

Create a new migration:
```bash
alembic -c backend/alembic.ini revision --autogenerate -m "description"
```

Roll back one migration:
```bash
alembic -c backend/alembic.ini downgrade -1
```

Roll back everything:
```bash
alembic -c backend/alembic.ini downgrade base
```

PO + PM: Louis
TL + PM: Raph / Vincent
PO + TL: Chikako
Devs: All


## Backend Architecture & Implementation Overview

### 1. Technology Stack

The backend currently uses:

| Technology             | Purpose                                 |
| ---------------------- | --------------------------------------- |
| **Python**             | Backend programming language            |
| **FastAPI**            | HTTP API framework                      |
| **Pydantic**           | Request/response schemas and validation |
| **SQLAlchemy**         | ORM and database access                 |
| **PostgreSQL**         | Relational database                     |
| **Alembic**            | Database migrations                     |
| **Argon2**             | Password hashing                        |
| **PyJWT**              | JWT creation and validation             |
| **pytest**             | Automated testing                       |
| **FastAPI TestClient** | API endpoint testing                    |
| **Podman**             | Local PostgreSQL container              |
| **python-dotenv**      | Environment variable loading            |
| **python-chess**       | Planned chess rules/game logic          |

The backend is designed around a layered architecture.

---

### 2. Overall Architecture

The current backend follows this structure:

```text
                         CLIENT
                           │
                           │ HTTP
                           ▼
┌───────────────────────────────────────────┐
│                   FASTAPI                 │
│                                           │
│  API routes / HTTP concerns               │
│  Authentication dependencies              │
│  Status codes                             │
└─────────────────────┬─────────────────────┘
                      │
                      ▼
┌───────────────────────────────────────────┐
│                  SCHEMAS                  │
│                                           │
│  Pydantic models                          │
│  Input validation                         │
│  Output serialization                     │
└─────────────────────┬─────────────────────┘
                      │
                      ▼
┌───────────────────────────────────────────┐
│                  SERVICE                  │
│                                           │
│  Business logic                           │
│  Authentication                           │
│  Password verification                    │
│  Duplicate checks                         │
│  Transactions                             │
└─────────────────────┬─────────────────────┘
                      │
                      ▼
┌───────────────────────────────────────────┐
│                REPOSITORY                 │
│                                           │
│  Database queries                         │
│  SQLAlchemy operations                    │
└─────────────────────┬─────────────────────┘
                      │
                      ▼
┌───────────────────────────────────────────┐
│                   MODEL                   │
│                                           │
│  SQLAlchemy database representation       │
└─────────────────────┬─────────────────────┘
                      │
                      ▼
┌───────────────────────────────────────────┐
│                PostgreSQL                 │
└───────────────────────────────────────────┘
```

The main principle is:

> **Routes handle HTTP. Services handle business logic. Repositories handle database access. Models represent database tables. Schemas represent API input/output.**

---

### 3. Database

#### PostgreSQL

PostgreSQL is the project's relational database.

It currently runs locally through **Podman**.

The development database is:

```text
Database: transcendence
User:     transcendence
```

A separate test database is used:

```text
transcendence_test
```

This keeps automated tests separate from development data.

---

### 4. SQLAlchemy

SQLAlchemy is used as the ORM.

The `User` Python class represents the `users` database table.

```text
Python                         PostgreSQL

User                           users
 │                               │
 ├── id          ───────────────►│ id
 ├── username    ───────────────►│ username
 ├── email       ───────────────►│ email
 └── password_hash ─────────────►│ password_hash
```

The model currently contains:

```text
User
├── id
├── username
├── email
└── password_hash
```

Constraints currently include:

```text
id             PRIMARY KEY
username       UNIQUE + NOT NULL
email          UNIQUE + NOT NULL
password_hash  NOT NULL
```

---

### 5. Alembic

Alembic manages database schema migrations.

Current migrations:

```text
16718a34410f_create_users_table.py
        │
        ▼
006390af9cda_add_password_hash_to_users.py
```

Typical commands:

```bash
alembic upgrade head
alembic current
alembic history
alembic revision --autogenerate -m "description"
alembic downgrade -1
alembic downgrade base
```

The database schema should be changed through migrations rather than manually modifying the PostgreSQL tables.

---

### 6. User Management

User management is the first completed backend domain.

The implemented operations are:

```text
POST   /api/users/
GET    /api/users/{username}
GET    /api/users/me
PATCH  /api/users/me
POST   /api/auth/login
```

---

### 7. User Registration

Flow:

```text
Client
  │
  │ POST /api/users/
  ▼
FastAPI
  │
  ▼
UserCreate schema
  │
  ▼
UserService
  │
  ├── check username
  ├── check email
  ├── hash password
  │
  ▼
UserRepository
  │
  ▼
SQLAlchemy
  │
  ▼
PostgreSQL
```

Passwords are **never stored in plaintext**.

The password is processed with:

```text
Argon2
```

The database stores only:

```text
password_hash
```

---

### 8. Password Security

The project uses Argon2 through:

```text
argon2-cffi
```

Password creation:

```text
plaintext password
       │
       ▼
     Argon2
       │
       ▼
password_hash
       │
       ▼
PostgreSQL
```

Authentication:

```text
login password
       │
       ▼
Argon2 verification
       │
       ├── incorrect → InvalidCredentials
       │
       └── correct
```

This means the original password cannot be recovered from the database.

---

### 9. Authentication

Authentication uses:

```text
JWT
```

through PyJWT.

The login flow is:

```text
POST /api/auth/login
        │
        ▼
UserLogin
        │
        ▼
authenticate_user()
        │
        ├── find user
        ├── verify password
        │
        ▼
create_access_token()
        │
        ▼
JWT
```

The client receives:

```json
{
    "access_token": "...",
    "token_type": "bearer"
}
```

---

### 10. JWT Structure

The access token contains:

```text
sub
exp
type
```

Conceptually:

```json
{
    "sub": "42",
    "exp": "...",
    "type": "access"
}
```

Where:

```text
sub  = user ID
exp  = expiration time
type = access token
```

The JWT is signed with the configured secret key.

---

### 11. Protected Endpoints

FastAPI's dependency injection is used for authentication.

The important dependency is:

```text
get_current_user()
```

Flow:

```text
HTTP request
     │
     ▼
Authorization: Bearer <JWT>
     │
     ▼
HTTPBearer
     │
     ▼
decode_access_token()
     │
     ▼
validate:
    ├── signature
    ├── expiration
    ├── subject
    └── token type
     │
     ▼
user ID
     │
     ▼
UserRepository
     │
     ▼
User
     │
     ▼
FastAPI endpoint
```

Endpoints can then use:

```python
current_user: User = Depends(get_current_user)
```

instead of manually processing JWTs.

---

### 12. Current User Endpoint

The endpoint:

```text
GET /api/users/me
```

returns the currently authenticated user.

Example:

```text
Client
  │
  │ Bearer JWT
  ▼
get_current_user()
  │
  ▼
User
  │
  ▼
UserResponse
```

The password hash is never returned because `UserResponse` only exposes:

```text
username
email
```

---

### 13. Profile Update

The endpoint:

```text
PATCH /api/users/me
```

allows an authenticated user to modify:

```text
username
email
```

The password is deliberately separate.

Flow:

```text
PATCH /api/users/me
        │
        ▼
JWT authentication
        │
        ▼
current_user
        │
        ▼
UserUpdate schema
        │
        ▼
UserService.update_user()
        │
        ├── username conflict check
        ├── email conflict check
        ├── update supplied fields
        │
        ▼
UserRepository.update()
        │
        ▼
PostgreSQL
```

Partial updates are supported.

For example:

```json
{
    "email": "new@example.com"
}
```

does not modify the username.

---

### 14. Exception Handling

Business-level exceptions are separated from HTTP concerns.

For example:

```text
UserAlreadyExists
UserNotFound
InvalidCredentials
```

The service raises these exceptions.

The API layer converts them into HTTP responses.

Example:

```text
Service
   │
   │ UserAlreadyExists
   ▼
API
   │
   │ HTTP 409
   ▼
Client
```

This keeps HTTP-specific behavior out of the service layer.

---

### 15. Repository Layer

The repository contains database access functions.

Current user repository operations:

```text
get_by_username()
get_by_email()
get_by_id()
create()
update()
```

The repository knows about:

```text
SQLAlchemy
SQL queries
User model
Session
```

It does not decide:

```text
HTTP status codes
authentication rules
business policies
```

---

### 16. Service Layer

The user service currently handles:

```text
create_user()
verify_password()
authenticate_user()
get_user_by_id()
get_user()
update_user()
```

The service is responsible for business rules such as:

```text
Username must be unique
Email must be unique
Passwords must be hashed
Passwords must be verified
Invalid login must be rejected
User must exist before update
```

---

### 17. API Layer

The API layer currently contains:

```text
backend/api/auth.py
backend/api/users.py
```

##### Authentication

```text
POST /api/auth/login
```

##### Users

```text
POST  /api/users/
GET   /api/users/{username}
GET   /api/users/me
PATCH /api/users/me
```

The API layer is responsible for:

```text
HTTP requests
HTTP responses
HTTP status codes
FastAPI dependencies
Schema handling
```

It should delegate business logic to services.

---

### 18. Testing Architecture

The project uses:

```text
pytest
```

Tests are organized by architectural layer:

```text
tests/
├── test_api/
│   ├── test_auth.py
│   └── test_users.py
│
├── test_core/
│   └── test_security.py
│
├── test_repositories/
│   └── test_user_repository.py
│
└── test_services/
    └── test_user_service.py
```

---

### 19. Repository Tests

Repository tests verify database behavior.

Examples:

```text
create user
get by username
get by email
get by ID
missing user
update user
```

They use the test PostgreSQL database.

---

### 20. Service Tests

Service tests verify business logic.

Examples:

```text
successful registration
duplicate username
duplicate email
password verification
wrong password
unknown user
get user
get user by ID
update user
partial update
duplicate username during update
duplicate email during update
transaction rollback
```

These tests verify business behavior without requiring an HTTP request.

---

### 21. API Tests

API tests use:

```text
FastAPI TestClient
```

They verify complete HTTP behavior.

Examples:

```text
registration → 201
login → 200
wrong password → 401
unknown user → 401
missing user → 404
duplicate username → 409
duplicate email → 409
valid JWT → 200
invalid JWT → 401
wrong token type → 401
profile update → 200
```

---

### 22. Test Database

Tests use a separate PostgreSQL database:

```text
transcendence_test
```

The pytest fixtures:

```text
create database schema
       │
       ▼
run test
       │
       ▼
drop database schema
```

This prevents tests from modifying the development database.

---

### 23. Authentication Security Tests

The JWT implementation has dedicated tests for:

```text
token creation
token decoding
invalid token
expired token
malformed subject
nonexistent user
wrong token type
```

This is important because authentication failures should be explicitly tested rather than assumed.

---

### 24. Current Backend Status

The following major pieces are currently implemented:

```text
┌────────────────────────────────────────────┐
│ BACKEND FOUNDATION                         │
├────────────────────────────────────────────┤
│ FastAPI                        ✅          │
│ SQLAlchemy ORM                 ✅          │
│ PostgreSQL                     ✅          │
│ Alembic migrations             ✅          │
│ Layered architecture           ✅          │
│                                            │
│ USER MANAGEMENT                            │
│ Registration                   ✅          │
│ Login                          ✅          │
│ Argon2 password hashing        ✅          │
│ JWT authentication             ✅          │
│ Protected endpoints            ✅          │
│ Current-user endpoint          ✅          │
│ Profile updates                ✅          │
│                                            │
│ TESTING                                    │
│ Repository tests               ✅          │
│ Service tests                  ✅          │
│ API tests                      ✅          │
│ Security tests                 ✅          │
└────────────────────────────────────────────┘
```

---

### 25. What Has NOT Been Implemented Yet

The following are planned:

```text
Chess game domain
Game database model
Game service
python-chess integration
Match history
Game statistics
WebSocket communication
Remote multiplayer
Tournament system
Game customization
Public API
API keys
Rate limiting
Public API documentation
Frontend integration
```

---

### 26. Planned Game Architecture

The game should follow the same architecture already established for users.

```text
GAME DOMAIN

Client
  │
  ├──────── HTTP ────────────────┐
  │                              │
  └────── WebSocket ─────────────┤
                                 ▼
                           Game Service
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
               Validation    Game state   Match result
                    │
                    ▼
               python-chess
                    │
                    ▼
              Game Repository
                    │
                    ▼
                PostgreSQL
```

The important principle is:

> **WebSockets should transport game events. They should not contain the chess rules.**

The game service should own the game rules/application logic, while `python-chess` handles chess-rule validation.

---

### 27. Planned Chess Flow

A simplified game will eventually look like:

```text
Player A
   │
   │ move
   ▼
WebSocket
   │
   ▼
Game Service
   │
   ▼
python-chess
   │
   ├── illegal move
   │       │
   │       ▼
   │     reject
   │
   └── legal move
           │
           ▼
       update game
           │
           ▼
      save state
           │
           ▼
     broadcast event
           │
           ▼
       Player B
```

This allows the game logic to be tested independently from WebSockets.

---

### 28. Team Development Rule

New backend features should generally follow:

```text
1. Model
2. Migration
3. Schema
4. Repository
5. Service
6. API / WebSocket
7. Tests
```

Not every feature requires every layer, but this should be the default architecture.

For example:

```text
User
 │
 ├── User model
 ├── User schema
 ├── User repository
 ├── User service
 ├── User API
 └── User tests
```

The future game domain should follow the same principle:

```text
Game
 │
 ├── Game model
 ├── Game schema
 ├── Game repository
 ├── Game service
 ├── Game API
 ├── WebSocket
 └── Game tests
```

---

### 29. Delegation Strategy

The current architecture makes it possible to split development by domain.

Possible responsibilities:

```text
                BACKEND
                   │
       ┌───────────┼────────────┐
       │           │            │
       ▼           ▼            ▼
     USERS       CHESS       WEBSOCKET
       │           │            │
       │      python-chess      │
       │           │            │
       └───────────┼────────────┘
                   │
                   ▼
              INTEGRATION
```

A developer working on WebSockets should not need to implement chess rules.

A developer working on chess logic should not need to implement JWT handling.

A developer working on the public API should be able to consume existing services rather than directly modifying database internals.

This separation reduces conflicts between team members.

---

### 30. Development Environment

The main tools currently used during development are:

```text
Python virtual environment
        │
        ▼
Python dependencies
        │
        ├── FastAPI
        ├── SQLAlchemy
        ├── Pydantic
        ├── PyJWT
        ├── Argon2
        └── pytest
        │
        ▼
Podman
        │
        ▼
PostgreSQL
```

---

### 31. Core Architectural Principle

The backend should remain understandable by following one central rule:

```text
API
 ↓
Schema
 ↓
Service
 ↓
Repository
 ↓
Model
 ↓
Database
```

Authentication is a cross-cutting concern:

```text
Request
   │
   ▼
JWT
   │
   ▼
get_current_user()
   │
   ▼
User
   │
   ▼
Protected endpoint
```

Future features should fit into this architecture instead of bypassing it.

This gives the project a consistent structure that multiple developers can work on simultaneously.
