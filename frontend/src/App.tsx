import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./components/Home";
import Chess from "./components/Chess/Chess";
import Login from "./components/Account/Login";
import Register from "./components/Account/Register";
import Profil from "./components/Account/Profile";

export const darkTile = "#9c7446";
export const lightTile = "#F5F0D3";
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
      </Routes>
    </BrowserRouter>
  )
}

export default App;
