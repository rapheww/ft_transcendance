import { useNavigate } from "react-router-dom";
import Header from "../Navbar/Header";

const Mode = () => {
  const navigate = useNavigate();

  const modes = ["Mode 1", "Mode 2", "Mode 3"];

  return (
    <div>
      <Header />
      <div className="w-full min-h-[calc(100vh-72px)] flex flex-col justify-center items-center px-4">
        <p className="uppercase m-6 sm:m-10 text-sm sm:text-base tracking-wide">
          Select a mode :
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center w-full max-w-4xl gap-7 sm:gap-7">
          {modes.map((mode) => (
            <button
              key={mode}
              onClick={() => navigate("/matchmaking")}
              className="btn bg-mist-700 hover:bg-mist-600 md:hover:shadow-[0px_0px_15px_#fff] transition-colors
                         w-full sm:w-60 lg:w-100
                         h-28 sm:h-40 lg:h-50
                         text-sm sm:text-base border-none"
            >
              {mode}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Mode;