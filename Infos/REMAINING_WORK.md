# Remaining Work for ft_transcendence

- finir tournaments (backend)
- implementer tournaments sur le frontend -> page tournaments, leaderboards tournaments page d'accueil
- implementer websockets frontend
- mode spectateur
- systeme recommandation machine learning
- sortir du deployement local
- peaufiner ce qui est deja present (front et back)

## Frontend

### Already present

- [x] React application and page routing.
- [x] Login and registration screens call the backend endpoints.
- [x] Chessboard UI and a local chess rules engine.
- [x] Profile, matchmaking, and game screens have initial UI scaffolding.

### To finish

- [ ] **Authentication and user management**
	- [ ] On login, read `access_token` and `token_type` from the API response and store the real token in the auth context; remove the placeholder token and simulated delay.
	- [ ] Restore the session from storage on page reload, clear it on logout, and handle missing/expired/invalid tokens by returning the user to login.
	- [ ] Send `Authorization: Bearer <token>` on every protected request, including profile updates, game actions, stats, tournament actions, and the game WebSocket connection.
	- [ ] Fetch the signed-in user's profile from `/api/users/me` rather than treating a locally entered username as proof of identity.
	- [ ] Show server validation messages for failed login/registration, duplicate accounts, network failures, and pending requests; avoid logging credentials or tokens.
	- [ ] Require authentication for game, profile, matchmaking, and tournament actions; keep public pages such as login and registration accessible.
	- **Done when:** a newly registered user can log in, reload without losing their session, use protected screens, and log out; invalid credentials and expired sessions produce understandable UI feedback.

- [ ] **Complete online chess**
	- [ ] Pass a real `game_id` from game creation/joining into the chess screen; do not start a separate local-only game when opening the route directly.
	- [ ] Open the authenticated WebSocket for that game and handle `game_connected`, `player_joined`, `player_left`, `move`, `game_state`, and `error` events.
	- [ ] Initialize and update the board from the server-provided FEN. Submit moves to the server and treat the server response/state as authoritative instead of finalizing a local move before acceptance.
	- [ ] Keep board position, turn, move list, and game result consistent for both players. Handle rejected moves, reconnects, disconnects, and a game that has already ended.
	- [ ] Display both players and their colors, whose turn it is, whether the opponent is connected, and the current game status.
	- [ ] Add usable game-over/result UI and wire resign and draw offer/accept/decline actions to the existing HTTP endpoints.
	- [ ] If timed games are offered in the UI, display and update both clocks using the backend's timer fields; otherwise do not advertise time controls that are not implemented end to end.
	- **Done when:** two signed-in users on separate browser sessions see the same game, only legal/current-turn moves are accepted, and both clients reach the same final result.

- [ ] **Matchmaking and player interaction**
	- [ ] Replace the generic mode buttons with the actual supported choices (for example, create a game or join an identified game); remove modes that have no backend behavior.
	- [ ] Define how a player finds an opponent. The current game routes create a game and join by ID, but do not expose a matchmaking queue; either add the queue contract on the backend or make the UI a clear invite/join-by-ID flow.
	- [ ] Make the waiting screen reflect the real pending game, show errors and opponent-found state, and let the user cancel without leaving an orphaned game.
	- [ ] Navigate both players into the same game ID after a successful join; remove the current skip action that opens an unrelated local board.
	- [ ] Connect the chat input to WebSocket `chat` events; render incoming messages with sender identity and time/order, clear the input on send, and prevent blank or overlong messages.
	- [ ] Show chat connection/reconnection state and handle a player leaving. Keep chat scoped to the current game unless a separate chat feature is explicitly added.
	- **Done when:** users can start or join a real game, know when an opponent is present, cancel/fail cleanly, and exchange messages during that game.

- [ ] **Statistics and match history**
	- [ ] Fetch the current user's profile and `/api/stats/me`; replace the hard-coded username and other sample profile values with returned data.
	- [ ] Fetch `/api/stats/history` and show each match's opponent, result, date, and other fields provided by the response schema.
	- [ ] Replace the chart's hard-coded sample points with values derived from actual API data. Label only statistics the backend actually provides; do not present sample values as player ratings.
	- [ ] Add loading, empty-history, and request-error states, and refresh the displayed data after a game finishes.
	- [ ] Decide whether the leaderboard is part of the user-facing stats screen; if so, populate it from `/api/stats/leaderboard` rather than duplicating static data.
	- **Done when:** a user's profile and history reflect games stored by the backend, and a new account sees an honest empty state rather than fabricated statistics.

- [ ] **Tournament experience**
	- [ ] Add a tournament view with create and join/register actions and visible registration/in-progress/finished states.
	- [ ] Choose how users find a tournament: the current API fetches a tournament by ID but has no list endpoint, so either add tournament discovery on the backend or provide a shareable tournament ID and a join-by-ID form.
	- [ ] Show participants and validate/communicate registration errors such as already registered or registration closed.
	- [ ] Let an eligible participant start the tournament and show why it cannot start when the participant count is invalid.
	- [ ] Render rounds and matches from the tournament response; link each active match to the corresponding game ID and refresh tournament state as matches finish.
	- [ ] Show the final winner and a completed state; handle a tournament that is cancelled or no longer available.
	- **Done when:** users can create/find, register for, play through, and view the result of a tournament using real backend data.

- [ ] **Game customization**
	- [ ] Load the current username and any saved customization when opening the profile editor; populate its inputs instead of leaving them disconnected from user state.
	- [ ] Validate profile edits and submit supported username/email changes to `/api/users/me`; update the visible profile only after the server accepts the change.
	- [ ] Decide and implement the avatar input behavior (the current UI suggests an image URL): validate the URL and display a fallback if it is missing or cannot load.
	- [ ] Save selected light/dark board colors so they survive reload and apply them consistently to the actual game board and preview.
	- [ ] Add backend fields, migration, schema validation, and update/read behavior for avatar and board colors if those settings are part of the finished feature; they are not currently in the user model/schema.
	- [ ] Show save success/failure and keep unsaved edits separate from persisted values; provide a way to cancel/reset edits.
	- **Done when:** profile edits and board colors persist after logout/reload and appear the same anywhere that user's profile or game board is shown.

- [ ] **End-to-end check**
	- [ ] Test registration, duplicate registration, valid/invalid login, page reload, protected-page access, and logout.
	- [ ] Use two separate signed-in browser sessions to test game creation/joining, opponent waiting/cancellation, legal and rejected moves, chat, disconnect/reconnect, resignation, and draw handling.
	- [ ] Finish a game and confirm profile statistics, match history, and any tournament bracket update from backend data.
	- [ ] Save customization, reload or sign in from another browser, and confirm the settings remain applied.
	- [ ] Check responsive layouts and visible loading, empty, success, and failure states for the main flows.
	- **Done when:** these scenarios pass against the running backend without relying on hard-coded IDs, fake tokens, or sample data.

## Backend

### Already present

- [x] FastAPI application and SQLAlchemy models/repositories, with Alembic migrations.
- [x] User registration, password authentication, access tokens, and protected user/game routes.
- [x] Chess game creation/joining, server-side move validation, game results, resignation, and draw offers.
- [x] Authenticated game WebSocket events for moves and basic in-game chat.
- [x] Stats and match-history endpoints, plus a single-elimination tournament service and API.
- [x] Public API has five routes; each uses API-key authentication and rate limiting.

### To finish

- [x] **Complete the public API requirement**
	- [x] Open `/openapi.json` and `/docs` in the running application and confirm both are available in the expected deployment configuration.
	- [x] Confirm all five public routes appear with correct methods, paths, path/body parameters, response models, and success/error status codes.
	- [x] Document `X-API-Key`: how clients send it, expected missing/invalid-key responses, and how an operator configures `PUBLIC_API_KEY` without committing the secret.
	- [x] Document the rate limit and what response clients receive when it is exceeded; ensure each public route remains rate limited.
	- [x] Add concise project-facing examples for calling the routes, including representative request and response payloads where applicable.
	- **Done when:** a developer can find the docs, understand all five endpoints and their security requirements, and successfully call them with a configured key.

- [ ] **Complete user interaction and customization support**
	- [ ] Confirm the user-facing flows have backend operations: authenticated profile read/update, game creation/joining, and in-game chat through the game WebSocket.
	- [x] Add avatar and board-color fields to the user model/schema and an Alembic migration if these are the selected customization options; define validation and sensible defaults.
	- [x] Extend the authenticated user read/update endpoints to return and persist those fields, and ensure one user's settings cannot be changed by another user.
	- [x] Add/update service and repository tests for valid changes, invalid values, unchanged fields, and unauthorized requests.
	- [x] If the project chooses a different player interaction such as invitations or matchmaking queue, define its API/WebSocket contract and add persistence/authorization as needed; current game APIs only support creating and joining by ID.
	- **Done when:** frontend-required profile settings survive database reloads and user-to-user game/chat flows are authorized and usable.

- [ ] **Harden and complete WebSocket/game behavior**
	- [x] Remove the `/ws/test/games/{game_id}/{user_id}` route from production, or ensure it is only registered in an isolated test configuration and cannot bypass authentication.
	- [x] Test missing, malformed, expired, and wrong-type tokens; reject users who are not players in the requested game before accepting the WebSocket.
	- [x] Validate WebSocket event shape and field types (including chess square syntax and chat length); return consistent errors without crashing the connection.
	- [x] Ensure all move outcomes are computed/persisted by the backend and broadcast from the committed game state; reject moves for finished games or the wrong player/turn.
	- [ ] Handle both players connecting/disconnecting, duplicate connections, abrupt network loss, and reconnection; send the current authoritative state when a player reconnects.
	- [ ] Check that chat and move events do not leak across game IDs, and clean up connection-manager state after either socket closes.
	- [ ] Add focused tests for authorization, legal/illegal moves, chat validation, disconnect cleanup, and finished-game behavior.
	- **Done when:** two remote clients can reconnect and continue from the same persisted state, and invalid or unauthorized clients cannot affect a game.

- [ ] **Configure deployment origins**
	- [ ] Move allowed frontend origins out of the hard-coded local list in `main.py` into environment-backed configuration.
	- [ ] Set separate local and deployed origin values; avoid allowing every origin in production unless there is a deliberate, documented reason.
	- [ ] Configure the frontend API and WebSocket base URLs for local and deployed environments rather than hard-coding `127.0.0.1`.
	- [ ] Use HTTPS/WSS in deployment and keep database credentials, signing secrets, and the public API key in deployment secrets/environment variables.
	- [ ] Document required environment variables and verify startup fails clearly when required secrets/configuration are missing.
	- **Done when:** the deployed frontend can make API and WebSocket connections from its configured origin, while unapproved origins are rejected.

- [ ] **Final backend verification**
	- [ ] Apply all Alembic migrations to a new/empty database and confirm the application starts and can create/read users, games, stats, and tournaments.
	- [ ] Run the backend test suite and address failures related to the mandatory flows; retain tests for the public API, auth, games/WebSocket, stats/history, and tournaments.
	- [ ] Call every public route with no key, a wrong key, and a valid key; confirm the first two are rejected and the valid key gets the documented result.
	- [ ] Exercise each public route past its configured request limit and confirm rate limiting returns the expected response.
	- [ ] Verify registration/login and bearer-token authorization, including invalid/expired tokens and attempts to act as another user.
	- [ ] Run two independent clients through a game, chat, disconnect/reconnect, and game completion; confirm the final state is persisted and reflected in stats/history.
	- [ ] Complete a tournament from registration through final winner, including invalid start conditions and progression after match completion.
	- **Done when:** the clean-database setup, automated tests, and representative real-client scenarios all pass with production-style configuration.