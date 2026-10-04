*This project has been created as part of the 42 curriculum by chitoupa, vgodoy, rchaumei, lchambos*

# ft_transcendence

## Instructions

### Requirements

- Python 3
- Node.js / npm
- PostgreSQL
- Podman

### Environment configuration

The backend reads its configuration from `.env`.

Create your local environment file from the provided example:

```bash
cp .env.example .env
```

Then replace the placeholder secrets with locally generated values.

The `.env` file must never be committed to Git.

Generate secure secrets with:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Use different values for `JWT_SECRET_KEY` and `PUBLIC_API_KEY`.

### Installing and running the application

For automatic installation and to run everything at once:

```bash
make setup
```

Else install the backend and frontend dependencies:

```bash
make install
```

Start the PostgreSQL database:

```bash
make db
```

Run database migrations:

```bash
make migrate
```

Start the backend and frontend:

```bash
make dev
```

---

# Public API

The project provides a public API under:

```text
/api/public
```

All public API endpoints require authentication using the `X-API-Key` HTTP header.

The API key is configured through the `PUBLIC_API_KEY` environment variable.

Example:

```bash
curl \
  -H "X-API-Key: $PUBLIC_API_KEY" \
  http://127.0.0.1:8000/api/public/leaderboard
```

The public API is rate limited to **30 requests per minute per client IP address**.

Requests exceeding the limit receive:

```text
429 Too Many Requests
```

---

## GET `/api/public/leaderboard`

Returns the current leaderboard.

### Request

```bash
curl -H "X-API-Key: $PUBLIC_API_KEY" http://127.0.0.1:8000/api/public/leaderboard
```

### Example response

```JSON
[
  {
    "username": "alice",
    "wins": 10,
    "games_played": 15
  },
  {
    "username": "bob",
    "wins": 7,
    "games_played": 12
  }
]
```

### Status codes

- `200 OK` — leaderboard successfully returned
- `401 Unauthorized` — missing or invalid API key
- `429 Too Many Requests` — rate limit exceeded

---

## GET `/api/public/tournaments/{tournament_id}`

Returns information about a tournament.

### Request

```bash
curl -H "X-API-Key: $PUBLIC_API_KEY" http://127.0.0.1:8000/api/public/tournaments/1
```

### Example response

```JSON
{
  "id": 1,
  "status": "waiting",
  "winner_id": null,
  "participants": [
    "alice",
    "bob"
  ],
  "matches": []
}
```

### Status codes

- `200 OK` — tournament successfully returned
- `401 Unauthorized` — missing or invalid API key
- `404 Not Found` — tournament does not exist
- `429 Too Many Requests` — rate limit exceeded

---

## POST `/api/public/tournaments`

Creates a new tournament.
The creator is automatically registered as the first participant.

### Request

```bash
curl -X POST -H "Content-Type: application/json" -H "X-API-Key: $PUBLIC_API_KEY" -d '{"creator_id": 1}' http://127.0.0.1:8000/api/public/tournaments
```

### Example response

```JSON
{
  "id": 1,
  "status": "waiting",
  "winner_id": null,
  "participants": [
    "alice"
  ],
  "matches": []
}
```

### Status codes

- `201 Created` — tournament successfully created
- `401 Unauthorized` — missing or invalid API key
- `404 Not Found` — creator does not exist
- `429 Too Many Requests` — rate limit exceeded

---

## PUT `/api/public/tournaments/{tournament_id}/participants/{user_id}`

Adds a user to an existing tournament.

### Request

```bash
curl -X PUT -H "X-API-Key: $PUBLIC_API_KEY" http://127.0.0.1:8000/api/public/tournaments/1/participants/2
```

### Example response

```JSON
{
  "id": 1,
  "status": "waiting",
  "winner_id": null,
  "participants": [
    "alice",
    "bob"
  ],
  "matches": []
}
```

### Status codes

- `200 OK` — participant successfully added
- `401 Unauthorized` — missing or invalid API key
- `404 Not Found` — tournament or user does not exist
- `409 Conflict` — tournament has already started or user is already registered
- `429 Too Many Requests` — rate limit exceeded

---

## DELETE `/api/public/tournaments/{tournament_id}`

Cancels a tournament.

### Request

```bash
curl -X DELETE -H "X-API-Key: $PUBLIC_API_KEY" http://127.0.0.1:8000/api/public/tournaments/1
```

### Response

A successful cancellation returns:

```text
204 No Content
```

### Status codes

- `204 No Content` — tournament successfully cancelled
- `401 Unauthorized` — missing or invalid API key
- `404 Not Found` — tournament does not exist
- `409 Conflict` — tournament has already started
- `429 Too Many Requests` — rate limit exceeded

---

# API documentation

The complete API specification is generated automatically by FastAPI.

Interactive Swagger UI:

```text
http://127.0.0.1:8000/docs
```

OpenAPI specification:

```text
http://127.0.0.1:8000/openapi.json
```

The public API endpoints are documented with the `X-API-Key` security scheme.

---
