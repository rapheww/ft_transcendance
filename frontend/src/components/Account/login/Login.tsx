import { NavLink } from "react-router-dom";
import { useState } from "react";
import { useAuth } from "../../AuthProvider";
import Header from "../../Navbar/Header";

const Login = () => {
  const [username, setUsername] = useState<string>("");
  const [password, setPassword] = useState<string>("");
  const [invalid, setInvalid] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const inputClassname = `input outline-0 border bg-white/3 border-white/50 focus:border-white-50 focus-within:border-white/50 w-full lg:h-12 lg:text-lg 2xl:text-base`;

  const { login } = useAuth();
  //login handling
  async function handleLogin(event: any) {
    if (event) event.preventDefault();
    try {
      const url = "http://127.0.0.1:8000/api/auth/login";
      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: username, password: password }),
      });

      //MORE STATUS CODE TO HANDLE
      if (response.status != 200) {
        const infos = await response.json()
        if(!infos) return;
        throw infos.detail
      }
      else {
        const accessData = await response.json();
          login({
            username: username,
            token: accessData.access_token,
            refreshToken: accessData.refresh_token,
          });
      }
    } catch (error) {
      setInvalid(true);
      setErrorMessage(error as string);
      return;
    }
  }

  return (
    <div className="min-h-screen">
      <Header />

      <div className="flex justify-center items-center min-h-[calc(100vh-56px)] px-4 py-8">
        <div
          id="login"
          className={`
            flex
            min-h-100 lg:min-h-110 2xl:min-h-125
            w-full
            max-w-xl 2xl:max-w-2xl
            flex-col
            justify-center
            border-2
            ${invalid ? "border-red-500/60" : "border-white/50"}
            bg-black/20 backdrop-blur-xs
            rounded-md
            p-6
            sm:p-10 lg:p-12 2xl:p-14
          `}
        >
          <div className="flex flex-col items-center mb-8 lg:mb-10">
            <h1 className="text-2xl sm:text-3xl 2xl:text-4xl mb-3">Login</h1>
            <p className="text-center text-base lg:text-lg">
              No account ?{" "}
              <NavLink to="/register" className="text-white/60 hover:text-gray-300">
                Register
              </NavLink>
            </p>
          </div>
          <form
            onSubmit={handleLogin}
            className="flex flex-col items-center w-full gap-3 lg:gap-4"
          >
            <input
              type="text"
              className={inputClassname}
              placeholder="Username"
              value={username}
              onChange={(event) => {
                setUsername(event.target.value);
              }}
            />
            <input
              type="password"
              className={inputClassname}
              placeholder="Password"
              value={password}
              onChange={(event) => {
                setPassword(event.target.value);
              }}
            />
            <p className={`text-md sm:text-lg 2xl:text-lg text-red-500/60 ${errorMessage === null ? 'hidden' : ''}`}>{errorMessage}</p>
            <button
              type="submit"
              id="log-btn"
              className="relative inline-flex items-center justify-center mt-3 px-6 py-3 lg:px-8 lg:py-3 lg:text-lg overflow-hidden font-bold text-white hover:text-gray-700 rounded-md shadow-2xl group"
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
          </form>
        </div>
      </div>
    </div>
  );
};

export default Login;