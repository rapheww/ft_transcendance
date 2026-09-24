import { useNavigate } from "react-router-dom";
import Header from "../Navbar/Header";
import "/src/index.css";

const Waiting = () => {
  const navigate = useNavigate();
  return (
    <div>
      <Header />
      <div className="w-full min-h-[calc(100vh-72px)] flex flex-col justify-center items-center">
        <p className="uppercase text-3xl">Waiting for opponent</p>
        <div className="loader m-10"
            >
        </div>
        <button
              onClick={() => navigate("/chess")}
              className="btn bg-mist-700 hover:bg-mist-600  transition-colors
                         w-25 sm:w-30 lg:w-30
                         h-15 sm:h-15 lg:h-15
                         text-sm sm:text-base"
            >
            skip
            </button>
      </div>
    </div>
  );
};

export default Waiting;

