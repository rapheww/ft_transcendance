import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./components/Home";
import Chess from "./components/Chess/Chess";
import Login from "./components/Account/Login";
import Register from "./components/Account/Register";
import Profil from "./components/Account/Profile";
import Mode from "./components/Matchmaking/Mode";
import Waiting from "./components/Matchmaking/Waiting";
import Editor from "./components/Account/Editor";

export const darkTile = "#8A663E";
export const lightTile = "#E3DDC5";
export const selectTile = "#508a52";
function App() {

  return (
    <BrowserRouter>
      <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/chess" element={<Chess />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/profile" element={<Profil />} />
          <Route path="/mode" element={<Mode />} />
          <Route path="/matchmaking" element={<Waiting />} />
          <Route path="/editor" element={<Editor />} />

      </Routes>
    </BrowserRouter>
  )
}

export default App;
