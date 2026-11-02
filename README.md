*This project has been created as part of the 42 curriculum by chitoupa, vgodoy, rchaumei, lchambos*

# ft_transcendence

## Description

**ft_transcendence** is a web-based chess platform for playing, following, and tracking chess matches. It brings the features of an online chess service together in one application | players can create an account, choose how they want to play, take part in live games, and review their progress afterward.

The project has a React and TypeScript frontend and a Python backend built with FastAPI. The frontend provides the pages for profiles, match setup, the chessboard, and tournaments. The backend manages accounts, games, matchmaking, statistics, and other application data in PostgreSQL. The two parts communicate through an HTTP API, with WebSockets supporting live game updates.

### Playing and following games

Players can find an opponent through matchmaking or play against an AI opponent. Match setup includes a clock setting, including an increment, and players can follow a match as spectators. Real-time updates let the players see the game as it progresses without refreshing the page.

### Accounts and progress

Registered players have profiles and can look back at their match history and statistics. A leaderboard provides a view of player results, while the recommendation feature suggests potential opponents based on game-related data.

### Tournaments and integrations

The application includes tournament functionality alongside individual matches. It also exposes a public API for selected data and tournament actions. The public endpoints require an API key and are rate limited; examples and endpoint details are in the [public API documentation](backend/api/PUBLIC_API.md).

In short, ft_transcendence combines a playable chess experience with the supporting features around it | finding opponents, following live games, managing a player profile, and exploring results and tournaments.

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
cp.env.example.env
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

`make db` creates both the usual `transcendence` database and the `transcendence_test` database used by backend tests. It also ensures the test database exists when starting an existing PostgreSQL container.

## Resources

The following documentation introduces the main technologies used in ft_transcendence and provides useful references for understanding how the application is built.

### Frontend

- [React | Learn React](https://react.dev/learn) — components, state, and event handling used to build the interactive interface.
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

## Team Information

| Team member | Roles                       | Description                                                                                                                                       |
|             |                             |                                                                                                                                                   |
| chitoupa    | Technical Lead - Developer  | Made technical decisions regarding architecture and tool usage for backend, ensured stack decisions and critical code changes for AI/ML.          |
|             |                             |                                                                                                                                                   |
| vgodoy      | Project Manager - Developer | Swiss knife that ensured team coordination and communication, managed different sides of the project to accomodate everyone and planned meetings. |
|             |                             |                                                                                                                                                   |
| rchaumei    | Technical Lead - Developer  | Made most technical decisions regarding architecture and stack usage for fronted, ensured decisions and best practices for the UI/UX.             |
|             |                             |                                                                                                                                                   |
| lchambos    | Product Owner - Developer   | Defined the global vision and made decisions regarding features, ensured priorities and product backlog with validation of work completion.       |

## Project Management

The team organized itself pretty simply | at first, chitoupa, vgodoy and lchambos worked on the backend while rchaumei focused on the frontend. When the backend started getting clearer and websockets were introduced, only vgodoy remained focused solely on the backend while chitoupa and lchambos started being hybrids for both depending on the current tasks. Then it was more according to the current workload and while rchaumei stayed mostly on the frontend, everyone got involved with most parts of the project to lend a hand.
Regular meetings were held at school to discuss about the implementation of the game, the different features that would be included, the workload and current tasks of everyone, the planning of each member or finally what was liked or not in the current implementation of the project. Then a lot was talked about via Discord, either with the group or directly with individual members depending on the task at hand.
Most of the work was shared/done via GitHub and different branches so that everyone would be able to continue working independently if needed or with the advancements of the group. It worked great overall and not much conflicts have risen during the project as we had clear directions and limits on what to do. 

## Technical Stack

### Frontend

- **React 19** structures the interface as reusable components, such as the chessboard, profile, and match views. Its state model lets the UI update as players navigate or receive game events. **TypeScript** adds static types to the frontend code, helping catch incompatible data and interface errors during development.
- **Vite** provides the frontend development server and production build. Its development server proxies API and WebSocket requests to FastAPI, so the browser can use the same local origin while developing. **React Router** maps URLs to screens, including game, tournament, profile, and authentication pages.
- **Tailwind CSS** provides utility classes for styling, while **DaisyUI** adds reusable interface patterns. **chess.js** handles chess rules and move state in the browser, allowing the board to respond immediately to user input. The backend still validates and stores the authoritative game state.
- **Recharts** is used to present statistics visually, and **Lucide React** supplies interface icons.

### Backend

- **Python 3.14 and FastAPI** implement the API used by the frontend, plus WebSocket routes for live game communication. FastAPI's typed request and response models help define and validate the API contract, and its OpenAPI integration generates interactive API documentation automatically.
- **Pydantic** validates incoming and outgoing API data and loads settings from `.env`. **Uvicorn** runs the application as an ASGI server, supporting both HTTP requests and persistent WebSocket connections.
- **SQLAlchemy** maps Python classes to PostgreSQL tables and provides database queries through the ORM. **Alembic** versions schema changes as migrations, so a database can be upgraded consistently as the project evolves.
- **python-chess** provides server-side board and rules logic. This lets the backend verify moves, maintain game records, and work with chess formats such as FEN and PGN independently of the browser. **scikit-learn**, with NumPy, supports the data-driven opponent recommendation feature.
- Authentication uses signed **JWT** access tokens, while **Argon2** stores password hashes rather than plaintext passwords. **SlowAPI** applies rate limits to public API requests to help prevent excessive use.

### Database and development

- **PostgreSQL 17** stores accounts, games, tournament brackets, social relationships, and messages. These records have explicit relationships—for example, a game references its players, and a tournament match references its tournament and game—so a relational database is a good fit. Foreign keys, unique constraints, and transactions help prevent invalid references and keep related updates consistent.
- **Podman** runs PostgreSQL in a local container. The Makefile creates and starts the same database image and configuration for each developer, without requiring PostgreSQL to be installed directly on the host.
- **HTTP/JSON** is used for standard operations such as authentication, profiles, and tournament requests. **WebSockets** are used when the connection needs to remain open for live game events, avoiding repeated polling for each update.
- **pytest** and **pytest-asyncio** support backend testing, while **ESLint** checks frontend code. The Makefile provides common setup, migration, test, lint, and build commands.

The frontend and backend are separate applications with a clear API boundary | the browser focuses on interaction and presentation, while the backend owns authentication, persistence, and game coordination. Using chess libraries on both sides keeps move feedback responsive in the UI while preserving server-side validation and a consistent saved game record.

## Database Schema

The schema is managed with SQLAlchemy models and Alembic migrations.

| Table                     | Purpose and key fields                                                                                                                                              |
|                           |                                                                                                                                                                     |
| `users`                   | Player accounts and preferences. `id`, `username` and `email`, `password_hash` and `avatar`, board colors, `elo`, `is_bot`, and optional AI/profile preferences.    |
|                           |                                                                                                                                                                     |
| `games`                   | Match state and result. `id` and player IDs, `status`, `result`, and opponent/AI fields, `current_fen` and `pgn`, clock values and ELO snapshots, and creation/move/finish times. A  black player may be absent while a game is waiting; `draw_offer_by` optionally references a user.                                                                                                 |
|                           |                                                                                                                                                                     |
| `matchmaking_queue`       | Players waiting for a match. Integer `id` and unique `user_id`, optional initial clock and increment, and `created_at`.                                             |
|                           |                                                                                                                                                                     |
| `tournaments`             | Tournament lifecycle and schedule. Integer `id`, status and organizer type, optional creator and winner IDs, current round, registration/next-round/creation times. |
|                           |                                                                                                                                                                     |
| `tournament_participants` | Many-to-many link between tournaments and users, with integer IDs and a `joined_at` timestamp. A tournament/user pair is unique.                                    |
|                           |                                                                                                                                                                     |
| `tournament_matches`      | Bracket slots and outcomes. Integer tournament, round, slot, player, game, and winner IDs; `is_bye`. A tournament/round/slot is unique;                             |
|                           |                                                                                                                                                                     |
| `chat_messages`           | In-game messages, linked to a game and sender. Integer `id`, `game_id`, and `user_id`; `username`  and `message`.                                                   |
|                           |                                                                                                                                                                     |
| `friendships`             | Accepted user pairs. The two user IDs form a composite primary key and reference `users`.                                                                           |
|                           |                                                                                                                                                                     |
| `friend_requests`         | Request state for a user pair. Composite user-pair key, requester ID, status, and requested/responded timestamps; requester and both users reference `users`.       |
|                           |                                                                                                                                                                     |
| `private_conversations`   | One conversation per friendship, with integer IDs for the conversation and the two participants, plus `created_at`. The participant pair references `friendships`.  |
|                           |                                                                                                                                                                     |
| `private_messages`        | Private conversation messages. Integer IDs for message, conversation, and sender; `message`  and `created_at`.                                                      |
|                           |                                                                                                                                                                     |
| `notifications`           | Per-user notification text and state. Integer `id` and `user_id`, `action`, `entity_type`, and `message`, `is_read`, and `created_at`.                              |

Player profiles, match history, statistics, and leaderboard values are assembled from user and game records; they are not stored in separate statistics tables.

## Modules

| Type  | Module name                                                                                                                | Points | Implemented/Used by          |
|       |                                                                                                                            |        |                              |
| Major | Use a framework for both the frontend and backend.                                                                         | 2      | Everyone                     |
|       |                                                                                                                            |        |                              |
| Minor | Use a frontend framework (React).                                                                                          | 1      | Everyone                     |
|       |                                                                                                                            |        |                              |
| Minor | Use a backend framework (FastAPI).                                                                                         | 1      | Everyone                     |
|       |                                                                                                                            |        |                              |
| Major | Implement real-time features using WebSockets or similar technology.                                                       | 2      | chitoupa, rchaumei, lchambos |
|       |                                                                                                                            |        |                              |
| Major | Allow users to interact with other users.                                                                                  | 2      | chitoupa, rchaumei, lchambos |
|       |                                                                                                                            |        |                              |
| Major | A public API to interact with the database with a secured API key, rate limiting, documentation, and at least 5 endpoints. | 2      | vgodoy                       |
|       |                                                                                                                            |        |                              |
| Minor | Use an ORM for the database.                                                                                               | 1      | chitoupa, vgodoy, lchambos   |
|       |                                                                                                                            |        |                              |
| Major | Standard user management and authentication.                                                                               | 2      | chitoupa, rchaumei, lchambos |
|       |                                                                                                                            |        |                              |
| Minor | Game statistics and match history.                                                                                         | 1      | vgodoy, rchaumei             |
|       |                                                                                                                            |        |                              |
| Major | Introduce an AI Opponent for games.                                                                                        | 2      | chitoupa                     |
|       |                                                                                                                            |        |                              |
| Major | Recommandation system using machine learning.                                                                              | 2      | chitoupa                     |
|       |                                                                                                                            |        |                              |
| Major | Implement a complete web-based game where users can play against each other.                                               | 2      | Everyone                     |
|       |                                                                                                                            |        |                              |
| Major | Remote players — Enable two players on separate computers to play the same game in real-time.                              | 2      | chitoupa, rchaumei, lchambos |
|       |                                                                                                                            |        |                              |
| Minor | Implement a tournament system.                                                                                             | 1      | chitoupa, vgodoy             |
|       |                                                                                                                            |        |                              |
| Minor | Game customization options.                                                                                                | 1      | rchaumei, lchambos           |
|       |                                                                                                                            |        |                              |
| Minor | Implement spectator mode for games.                                                                                        | 1      | lchambos                     |

Total score: **25**

