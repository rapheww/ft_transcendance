*This project has been created as part of the 42 curriculum by chitoupa, vgodoy, rchaumei, lchambos*

# ft_transcendence

## Instructions

### Requirements

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


