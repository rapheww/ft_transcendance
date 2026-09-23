import { NavLink } from "react-router-dom";
import Header from "../Navbar/Header";

const Login = () => {
  return (
    <div className="min-h-screen">
      <Header />

      <div className="flex justify-center items-center min-h-[calc(100vh-72px)] px-4 py-8">
        <div className=" flex min-h-100 w-full max-w-xl flex-col justify-center border-2 border-violet-600 bg-gray-500 rounded-md p-6 sm:p-10">
          <div className="flex flex-col items-center mb-8">
            <h1 className="text-3xl sm:text-5xl mb-3">Login</h1>
            <p className="text-center">
              No account ?{" "}
              <NavLink to="/register" className="text-violet-400">
                Register
              </NavLink>
            </p>
          </div>
          <div className="flex flex-col items-center w-full gap-3">
            <input
              type="text"
              className="input input-primary w-full"
              placeholder="Username"
            />
            <input
              type="text"
              className="input input-primary w-full"
              placeholder="Password"
            />
            <button className="relative inline-flex items-center justify-center mt-3 px-6 py-3 overflow-hidden font-bold text-white rounded-md shadow-2xl group">
              <span className="absolute inset-0 w-full h-full transition duration-350 ease-in opacity-0 bg-linear-to-br from-pink-600 via-purple-700 to-blue-400 group-hover:opacity-100"></span>
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
