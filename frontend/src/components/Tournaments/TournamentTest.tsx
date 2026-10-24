import { useState } from "react";
import { useAuth } from "../AuthProvider";
import {
    createTournament,
    getTournament,
    joinTournament,
    listTournaments,
    startTournament,
} from "./tournamentApi";

export default function TournamentTest() {
    const [tournamentId, setTournamentId] = useState("");
    const [result, setResult] = useState("");
    const [loading, setLoading] = useState(false);
    const { token } = useAuth();
    async function run(action: () => Promise<unknown>) {
        if (!token.trim()) {
            setResult("Please log in before testing tournaments.");
            return;
        }
        setLoading(true);
        try {
            const data = await action();
            setResult(JSON.stringify(data, null, 2));
        } catch (error) {
            setResult(error instanceof Error ? error.message : String(error));
        } finally {
            setLoading(false);
        }
    }

    function validId(): number | null {
        const id = Number(tournamentId);
        if (!Number.isInteger(id) || id <= 0) {
            setResult("Enter a valid tournament ID.");
            return null;
        }
        return id;
    }

    function handleCreate() {
        void run(async () => {
            const tournament = await createTournament(token);
            setTournamentId(String(tournament.id));
            return tournament;
        });
    }

    function handleJoin() {
        const id = validId();
        if (id !== null) void run(() => joinTournament(id, token));
    }

    function handleStart() {
        const id = validId();
        if (id !== null) void run(() => startTournament(id, token));
    }

    function handleGet() {
        const id = validId();
        if (id !== null) void run(() => getTournament(id, token));
    }

    return (
        <div>
            <h1>Tournament Test</h1>

            <h2>Create Tournament</h2>
            <button disabled={loading} onClick={handleCreate}>Create</button>

            <h2>Join Tournament</h2>
            <input
                type="number"
                placeholder="Tournament ID"
                value={tournamentId}
                onChange={(e) => setTournamentId(e.target.value)}
            />
            <button disabled={loading} onClick={handleJoin}>Join</button>

            <h2>Start Tournament</h2>
            <button disabled={loading} onClick={handleStart}>Start</button>

            <h2>Read Tournament</h2>
            <button disabled={loading} onClick={handleGet}>Get by ID</button>
            <button disabled={loading} onClick={() => void run(() => listTournaments(token))}>
                List Open
            </button>

            <h2>API Result</h2>
            <pre>{loading ? "Loading..." : result}</pre>
        </div>
    );
}
