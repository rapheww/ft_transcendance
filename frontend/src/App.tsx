import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./components/Home";
import Chess from "./components/Chess/Chess";
import Login from "./components/Account/Login";
import Register from "./components/Account/Register";
import Profil from "./components/Account/Profile";
import Mode from "./components/Matchmaking/Mode";
import Waiting from "./components/Matchmaking/Waiting";
import AuthProvider from "./components/AuthProvider";
import DefaultLayout from "./components/DefaultLayout";
import RecommendationTest from "./components/Recommendations/RecommendationTest";
import TournamentTest from "./components/Tournaments/TournamentTest";
import NotificationTest from "./components/Notifications/NotificationTest";

function App() {

  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
            <Route path="/" element={<Home />}/>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route element={<DefaultLayout />}>
              <Route path="/chess/:timer/:bonus" element={<Chess />} />
              <Route path="/profile" element={<Profil />} />
              <Route path="/mode" element={<Mode />} />
              <Route path="/matchmaking/:timer/:bonus" element={<Waiting />} />
              <Route path="/test-recommendations" element={<RecommendationTest />} />
              <Route path="/tournament-test" element={<TournamentTest />} />
              <Route path="/notification-test" element={<NotificationTest />} />
            </Route>

        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App;
