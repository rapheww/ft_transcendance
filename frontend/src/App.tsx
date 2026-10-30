import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./components/Home";
import Chess from "./components/Chess/Chess";
import Profil from "./components/Account/Profil/Profile";
import Mode from "./components/Matchmaking/Mode";
import Waiting from "./components/Matchmaking/Waiting";
import AuthProvider from "./components/AuthProvider";
import DefaultLayout from "./components/DefaultLayout";
import Login from "./components/Account/login/Login";
import Register from "./components/Account/login/Register";
import Tournaments from "./components/Tournaments/Tournaments";
import Spectator from "./components/Chess/Spectator";
import RecommendationTest from "./components/Recommendations/RecommendationTest";
import TournamentTest from "./components/Tournaments/TournamentTest";
import FriendsList from "./components/Friends/FriendsList";

function App() {

  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
            <Route path="/" element={<Home />}/>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/watch/:gameId" element={<Spectator />} />
            <Route element={<DefaultLayout />}>
              {/* The game ID lets the chess screen load the exact game created or matched by the backend. */}
              <Route path="/chess/:timer/:bonus/:gameId" element={<Chess />} />
              <Route path="/tournaments" element={<Tournaments />} />
              <Route path="/profile" element={<Profil />} />
              <Route path="/mode" element={<Mode />} />
              <Route path="/matchmaking/:timer/:bonus" element={<Waiting />} />
              <Route path="/test-recommendations" element={<RecommendationTest />} />
              <Route path="/tournament-test" element={<TournamentTest />} />
              <Route path="/friendsList" element={<FriendsList/>} />
            </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App;
