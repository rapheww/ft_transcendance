import { NavLink } from "react-router-dom";
import Header from "../Navbar/Header";

const Register = () => {
  return (
    <div className="min-h-screen">
      <Header />

      <div className="flex justify-center items-center min-h-[calc(100vh-72px)] px-4 py-8">
        <div className=" flex min-h-100 w-full max-w-xl flex-col justify-center border-2 border-violet-600 bg-gray-500 rounded-md p-6 sm:p-10">
          <div className="flex flex-col items-center mb-8">
            <h1 className="text-3xl sm:text-5xl mb-3">Register</h1>
            <p className="text-center">
              Already have an account ?{" "}
              <NavLink to="/login" className="text-violet-400">
                Login
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
              placeholder="Email"
            />
            <input
              type="text"
              className="input input-primary w-[75%] m-1"
              placeholder="Password"
            />
            <button className="btn btn-primary mt-2">Login</button>
          </div>
        </div>
      </div>
    </div>
  );
};


export default Register;
