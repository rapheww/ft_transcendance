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

function App() {

  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
            <Route path="/" element={<Home />}/>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route element={<DefaultLayout />}>
              <Route path="/chess/:timer/:bonus/:gameId" element={<Chess />} />
              <Route path="/profile" element={<Profil />} />
              <Route path="/mode" element={<Mode />} />
              <Route path="/matchmaking/:timer/:bonus" element={<Waiting />} />
            </Route>

        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App;
