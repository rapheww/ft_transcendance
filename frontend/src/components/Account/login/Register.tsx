import { NavLink } from "react-router-dom";
import { useState } from "react";
import { useAuth } from "../../AuthProvider";
import Header from "../../Navbar/Header";
import { API } from "../../Chess/utils/api";

type ValidationIssue = {
  loc?: unknown;
  msg: string;
};

function isValidationIssue(value: unknown): value is ValidationIssue {
  return (
    typeof value === "object" &&
    value !== null &&
    "msg" in value &&
    typeof value.msg === "string"
  );
}

function formatApiError(detail: unknown): string {
  if (typeof detail === "string") return detail;

  if (Array.isArray(detail)) {
    const issue = detail.find(isValidationIssue);
    if (!issue) return "Request failed.";

    const field = Array.isArray(issue.loc)
      ? issue.loc[issue.loc.length - 1]
      : undefined;
    const label =
      typeof field === "string"
        ? { username: "Username", password: "Password", email: "Email" }[
            field
          ]
        : undefined;

    if (label && issue.msg.startsWith("String ")) {
      return `${label} ${issue.msg.slice("String ".length)}`;
    }

    return label ? `${label}: ${issue.msg}` : issue.msg;
  }

  return "Request failed.";
}

const Register = () => {
  const [username, setUsername] = useState<string>("");
  const [password, setPassword] = useState<string>("");
  const [confirmPassword, setConfirmPassword] = useState<string>("");
  const [email, setEmail] = useState<string>("");
  const [invalid, setInvalid] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [logging, setLogging] = useState<boolean>(false);
  const inputClassname = `input outline-0 border bg-white/3 border-white-50 focus:border-white-50 focus-within:border-white/50 w-full lg:h-12 lg:text-lg 2xl:text-base`;
  const { login } = useAuth();

  //register handling
  async function handleRegister(event : any) {
    if (event) event.preventDefault();

    

    if (confirmPassword != password) {
      const bd = document.getElementById("confirm-password");
      if (bd) {
        bd.className = "input outline-0 border bg-white/3 border-red-500 w-full";
      }
      return;
    }

    try {
      setLogging(true);
      if(!username || !password || !email) throw (["Empty field/s"])
      const url = `${API}/users/`;
      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: username,
          email: email,
          password: password,
        }),
      });

      //MORE STATUS CODE TO HANDLE
      if (response.status != 201) {
        const infos = await response.json()
        throw formatApiError(infos?.detail);
      }

      //Login time
      const urlLog = `${API}/auth/login`;
      const LogResponse = await fetch(urlLog, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: username, password: password }),
      });

      if (LogResponse.status != 200) {
        const infos = await LogResponse.json()
        throw formatApiError(infos?.detail);
      } else {
        const accessData = await LogResponse.json();
        login({
          username: username,
          token: accessData.access_token,
        });
      }
    } catch (error) {
      setLogging(false)
      setInvalid(true);
      setErrorMessage(error instanceof Error ? error.message : String(error))
      return;
    }
  }

  return (
    <div className="min-h-screen">
      <Header />

      <div className="flex justify-center items-center min-h-[calc(100vh-56px)] px-4 py-8">
        <div
          id="register"
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
            <h1 className="text-2xl sm:text-3xl 2xl:text-4xl mb-3">Register</h1>
            <p className="text-center text-base lg:text-lg">
              Already have an account ?{" "}
              <NavLink to="/login" className="text-gray-400 hover:text-gray-300">
                Login
              </NavLink>
            </p>
          </div>
          <form 
            onSubmit={handleRegister}
            className="flex flex-col items-center w-full gap-3 lg:gap-4"
          >
            <input
              type="text"
              className={inputClassname}
              placeholder="Username"
              autoComplete="username"
              maxLength={15}
              value={username}
              onChange={(event) => {
                setUsername(event.target.value);
              }}
            />
            <input
              type="text"
              className={inputClassname}
              placeholder="Email"
              value={email}
              onChange={(event) => {
                setEmail(event.target.value);
              }}
            />
            <input
              type="password"
              className={inputClassname}
              placeholder="Password"
              autoComplete="current-password"
              maxLength={128}
              value={password}
              onChange={(event) => {
                setPassword(event.target.value);
              }}
            />
            <input
              id="confirm-password"
              type="password"
              className={inputClassname}
              placeholder="Confirm password"
              value={confirmPassword}
              onChange={(event) => {
                setConfirmPassword(event.target.value);
              }}
            />
            <p className={`text-md sm:text-lg 2xl:text-lg text-red-500/60 ${errorMessage === null ? 'hidden' : ''}`}>{errorMessage}</p>
            <button
              type="submit"
              className="relative inline-flex items-center justify-center mt-3 px-6 py-3 lg:px-8 lg:py-3 lg:text-lg overflow-hidden font-bold text-white hover:text-gray-700 rounded-md shadow-2xl group"
            >
              <svg className={`mr-3 size-5 animate-spin ${logging ? 'flex' : 'hidden'}`} viewBox="0 0 100 100">
                <circle
                  cx="50"
                  cy="50"
                  r="42"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="10"
                  opacity="0.2"
                />
                <circle
                  cx="50"
                  cy="50"
                  r="42"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="10"
                  strokeLinecap="round"
                  strokeDasharray="66 264"
                />
              </svg>
              <span className="absolute inset-0 w-full h-full transition duration-350 ease-in opacity-0 bg-linear-to-br from-white via-gray-200 to-white group-hover:opacity-100"></span>
              <span className="absolute top-0 left-0 w-full bg-linear-to-b from-white to-transparent opacity-5 h-1/3"></span>
              <span className="absolute bottom-0 left-0 w-full h-1/3 bg-linear-to-t from-white to-transparent opacity-5"></span>
              <span className="absolute bottom-0 left-0 w-4 h-full bg-linear-to-r from-white to-transparent opacity-5"></span>
              <span className="absolute bottom-0 right-0 w-4 h-full bg-linear-to-l from-white to-transparent opacity-5"></span>
              <span className="absolute inset-0 w-full h-full border border-white rounded-md opacity-10"></span>
              <span className="absolute w-0 h-0 transition-all duration-350 ease-out bg-white rounded-full group-hover:w-56 group-hover:h-56 opacity-5"></span>
              <span className="relative">Register</span>
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Register;