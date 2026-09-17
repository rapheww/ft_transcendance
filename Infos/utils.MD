                         ┌──────────────────────┐
                         │       CLIENT         │
                         │                      │
                         │ Browser / Frontend   │
                         │ Swagger / API client │
                         └──────────┬───────────┘
                                    │
                              HTTP request
                                    │
                                    ▼
                    ┌───────────────────────────┐
                    │         FASTAPI           │
                    │                           │
                    │ • routes                  │
                    │ • HTTP status codes       │
                    │ • HTTPException           │
                    │ • dependency injection    │
                    └─────────────┬─────────────┘
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │         SERVICE           │
                    │                           │
                    │ • business rules          │
                    │ • application logic       │
                    │ • transaction boundary    │
                    └─────────────┬─────────────┘
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │        REPOSITORY         │
                    │                           │
                    │ • database queries        │
                    │ • persistence operations  │
                    │ • SQLAlchemy statements   │
                    └─────────────┬─────────────┘
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │        SQLALCHEMY         │
                    │                           │
                    │ Session → Engine          │
                    │                           │
                    │ Models → Tables           │
                    └─────────────┬─────────────┘
                                  │ PostgreSQL connection
                                  ▼
                    ┌───────────────────────────┐
                    │        POSTGRESQL         │
                    │                           │
                    │   Podman container        │
                    │   transcendence-db        │
                    │                           │
                    │   users                   │
                    │   ...                     │
                    └───────────────────────────┘

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
find ./backend ./tests -type d -name "__pycache__" -exec rm -rf {} \;
```

Pull the image for the database:
```bash
podman pull docker.io/library/postgres:17
```

Create the container:
```bash
podman run --name transcendence-db \ -e POSTGRES_USER=transcendence \ -e POSTGRES_PASSWORD=transcendence_dev \ -e POSTGRES_DB=transcendence \ -p 5432:5432 \ -d docker.io/library/postgres:17
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

PO + PM: Louis
TL + PM: Raph / Vincent
PO + TL: Chikako
Devs: All

https://chatgpt.com/s/t_6aac4a83aeac8191bc55017ddbf9a219
