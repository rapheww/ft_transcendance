                ┌─────────────────────┐
                │      Frontend       │
                └──────────┬──────────┘
                           │
            ┌──────────────┴──────────────┐
            │                             │
        REST API                      WebSocket
            │                             │
            ▼                             ▼
    ┌───────────────┐             ┌───────────────┐
    │    Routers    │             │ Game Manager  │
    └───────┬───────┘             └───────┬───────┘
            │                             │
            └──────────────┬──────────────┘
                           │
                        FastAPI
                           │
                           ▼
                    ┌───────────────┐
                    │   Services    │
                    │               │
                    │ Auth          │
                    │ Games         │
                    │ Users         │
                    │ Tournaments   │
                    └───────┬───────┘
                            │
                        PostgreSQL
                            │
                            ▼
                    ┌───────────────┐
                    │   Database    │
                    └───────────────┘

                 HTTP
                  │
                  ▼
        ┌──────────────────┐
        │      Router      │
        │                  │
        │ HTTP concerns    │
        └────────┬─────────┘
                 │
                 ▼
        ┌──────────────────┐
        │     Service      │
        │                  │
        │ Business rules   │
        └────────┬─────────┘
                 │
                 ▼
        ┌──────────────────┐
        │    Repository    │
        │                  │
        │ Database access  │
        └────────┬─────────┘
                 │
                 ▼
            PostgreSQL

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
find ./backend -type d -name "__pycache__" -exec rm -rf {} \;
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

Connect to PostgreSQL:
```bash
podman exec -it transcendence-db psql -U transcendence -d transcendence
```

PO + PM: Louis
TL + PM: Raph / Vincent
PO + TL: Chikako
Devs: All

https://chatgpt.com/s/t_6aaad58bf994819182752c90a225c6b7
