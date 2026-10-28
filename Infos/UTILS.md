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
