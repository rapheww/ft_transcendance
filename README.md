*This project has been created as part of the 42 curriculum by chitoupa, vgodoy, rchaumei, lchambos*

# ft_transcendence

## Description

**ft_transcendence** is a web-based chess platform for playing, following, and tracking chess matches. It brings the features of an online chess service together in one application: players can create an account, choose how they want to play, take part in live games, and review their progress afterward.

The project has a React and TypeScript frontend and a Python backend built with FastAPI. The frontend provides the pages for profiles, match setup, the chessboard, and tournaments. The backend manages accounts, games, matchmaking, statistics, and other application data in PostgreSQL. The two parts communicate through an HTTP API, with WebSockets supporting live game updates.

### Playing and following games

Players can find an opponent through matchmaking or play against an AI opponent. Match setup includes a clock setting, including an increment, and players can follow a match as spectators. Real-time updates let the players see the game as it progresses without refreshing the page.

### Accounts and progress

Registered players have profiles and can look back at their match history and statistics. A leaderboard provides a view of player results, while the recommendation feature suggests potential opponents based on game-related data.

### Tournaments and integrations

The application includes tournament functionality alongside individual matches. It also exposes a public API for selected data and tournament actions. The public endpoints require an API key and are rate limited; examples and endpoint details are in the [public API documentation](backend/api/PUBLIC_API.md).

In short, ft_transcendence combines a playable chess experience with the supporting features around it: finding opponents, following live games, managing a player profile, and exploring results and tournaments.

## Instructions

### Prerequisites

The provided `Makefile` workflow is intended for Linux. Install:

- Python **3.14** and `venv`.
- Node.js and npm (Node.js **20.19+** or **22.12+**).
- Podman, for the PostgreSQL 17 database.
- GNU Make, `curl`, and an internet connection to install dependencies and download `cloudflared`.

### Environment configuration

The backend reads its configuration from `.env`. From the repository root, create it using the provided example:

```bash
cp .env.example .env
```

The example configures the local database used by `make db`. Keep `DATABASE_URL` and `TEST_DATABASE_URL` pointed at the local PostgreSQL instance; the test URL should use the `transcendence_test` database.

Replace the placeholder secrets with locally generated values. `JWT_SECRET_KEY` must be at least 32 characters, and `PUBLIC_API_KEY` must be a separate secret:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Run the command twice and use one value for each key. Keep `.env` private and never commit it to Git.

### Installing and running the application

After configuring `.env`, you can run the complete workflow in one command:

```bash
make setup
```

This installs dependencies, starts PostgreSQL, applies migrations, and launches the application. Alternatively, run the steps below individually:

From the repository root, install the dependencies, start PostgreSQL, and apply the database migrations:

```bash
make install
make db
make migrate
```

Start the backend and frontend together:

```bash
make dev
```

The frontend is available at <http://localhost:5173> and the backend API at <http://127.0.0.1:8000>. `make dev` also starts a temporary Cloudflare tunnel for the frontend; anyone with its generated URL may be able to access the development site. Stop the processes with **Ctrl+C**.

To run locally without the tunnel, start the services in separate terminals instead:

```bash
make backend
```

```bash
make frontend
```

### Useful commands

```bash
make help       # List available Make targets
make db-stop    # Stop PostgreSQL
make test       # Run backend tests
make lint       # Lint the frontend
make build      # Build the frontend
```

The backend tests require a `transcendence_test` database. Create it once after starting PostgreSQL:

```bash
podman exec transcendence-db createdb -U transcendence transcendence_test
```

## Resources

The following documentation introduces the main technologies used in ft_transcendence and provides useful references for understanding how the application is built.

### Frontend

- [React: Learn React](https://react.dev/learn) — components, state, and event handling used to build the interactive interface.
- [TypeScript documentation](https://www.typescriptlang.org/docs/) — the typed JavaScript language used by the frontend.
- [Vite guide](https://vite.dev/guide/) — frontend development server, build, and configuration.
- [React Router documentation](https://reactrouter.com/) — navigation between the app's pages.

### Backend and data

- [FastAPI tutorial](https://fastapi.tiangolo.com/tutorial/) — building HTTP endpoints, handling requests, and generating API documentation.
- [Pydantic documentation](https://docs.pydantic.dev/) — validation and schemas for configuration and API data.
- [SQLAlchemy ORM tutorial](https://docs.sqlalchemy.org/en/20/orm/quickstart.html) — mapping Python models to database tables and querying data.
- [Alembic tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html) — managing database schema changes with migrations.
- [PostgreSQL 17 documentation](https://www.postgresql.org/docs/17/) — reference for the relational database used by the backend.
- [Scikit-learn user guide](https://scikit-learn.org/stable/user_guide.html) — machine-learning concepts and tools used by the opponent recommendation feature.

### Chess and real-time play

- [chess.js](https://github.com/jhlywa/chess.js) — JavaScript chess rules and move handling used in the frontend.
- [python-chess documentation](https://python-chess.readthedocs.io/en/latest/) — Python chess rules, board representation, and game handling used by the backend.
- [FastAPI WebSockets guide](https://fastapi.tiangolo.com/advanced/websockets/) — the backend's approach to real-time communication for live games.
- [MDN WebSocket API guide](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API) — browser-side reference for WebSocket connections.

### API and development tools

- [Project public API guide](backend/api/PUBLIC_API.md) — available public endpoints, API key authentication, rate limiting, and request examples.
- [Podman documentation](https://docs.podman.io/en/latest/) — running the local PostgreSQL database in a container.
