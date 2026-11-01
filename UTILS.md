## Global commands

Launch and stop the virtual environment:
```bash
source .venv/bin/activate
deactivate
```

Tests:

```bash
pytest -q
```

## Podman commands

Connect to PostgreSQL:
```bash
podman exec -it transcendence-db psql -U transcendence -d transcendence
```

## Alembic commands

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
