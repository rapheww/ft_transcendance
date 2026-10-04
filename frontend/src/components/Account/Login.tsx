import { NavLink } from "react-router-dom";
import Header from "../Navbar/Header";
import { useState } from "react";
import { useAuth } from "../AuthProvider";

const Login = () => {
  const [username, setUsername] = useState<string>("");
  const [password, setPassword] = useState<string>("");

  const { login } = useAuth();
  //login handling
  async function handleLogin() {
    console.log("login ... wait...");
    try {
      const url = "http://127.0.0.1:8000/api/auth/login";
      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: username, password: password }),
      });

      //MORE STATUS CODE TO HANDLE
      if (response.status != 200) {
        console.log("CANT LOGIN");
        return;
      } else {
        console.log("login success");
        const accessData = await response.json();
        login({
          username: username,
          token: accessData.access_token,
        });
        
        //set css color
        const token = accessData.access_token;
        const profilResponse = await fetch("http://127.0.0.1:8000/api/users/me", {
          headers: { Authorization: `Bearer ${token}` },
        });
        if(profilResponse.status == 200){
          const profil = await profilResponse.json();
          document.documentElement.style.setProperty("--dark-tile", profil.board_dark_color);
          document.documentElement.style.setProperty("--light-tile", profil.board_light_color);
          console.log('color saved');
        }
      }
    } catch {
      console.log("error fetch");
    }
  }

  return (
    <div className="min-h-screen">
      <Header />

      <div className="flex justify-center items-center min-h-[calc(100vh-72px)] px-4 py-8">
        <div
          className="
            flex
            min-h-100
            w-full
            max-w-xl
            flex-col
            justify-center
            border-2
            border-white
            bg-mist-800/75
            rounded-md
            p-6
            sm:p-10"
        >
          <div className="flex flex-col items-center mb-8">
            <h1 className="text-3xl sm:text-5xl mb-3">Login</h1>
            <p className="text-center text-lg">
              No account ?{" "}
              <NavLink to="/register" className="text-gray-400 underline">
                Register
              </NavLink>
            </p>
          </div>
          <div className="flex flex-col items-center w-full gap-3">
            <input
              type="password"
              className="input border border-gray-300 w-full"
              placeholder="Username"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
            />
            <input
              type="password"
              className="input border border-gray-300 w-full"
              placeholder="Password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
            <button
              onClick={() => {
                handleLogin();
              }}
              className="relative inline-flex items-center justify-center mt-3 px-6 py-3 overflow-hidden font-bold text-white hover:text-gray-700 rounded-md shadow-2xl group"
            >
              <span className="absolute inset-0 w-full h-full transition duration-350 ease-in opacity-0 bg-linear-to-br from-white via-gray-200 to-white group-hover:opacity-100"></span>
              <span className="absolute top-0 left-0 w-full bg-linear-to-b from-white to-transparent opacity-5 h-1/3"></span>
              <span className="absolute bottom-0 left-0 w-full h-1/3 bg-linear-to-t from-white to-transparent opacity-5"></span>
              <span className="absolute bottom-0 left-0 w-4 h-full bg-linear-to-r from-white to-transparent opacity-5"></span>
              <span className="absolute bottom-0 right-0 w-4 h-full bg-linear-to-l from-white to-transparent opacity-5"></span>
              <span className="absolute inset-0 w-full h-full border border-white rounded-md opacity-10"></span>
              <span className="absolute w-0 h-0 transition-all duration-350 ease-out bg-white rounded-full group-hover:w-56 group-hover:h-56 opacity-5"></span>
              <span className="relative">Login</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
