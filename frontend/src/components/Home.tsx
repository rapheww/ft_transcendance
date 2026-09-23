import Header from "./Navbar/Header";
import { useNavigate } from "react-router-dom";

const Home = () => {
  const navigate = useNavigate();
  return (
    <div className="flex flex-col items-center h-screen">
      <Header />
      <h1 className="text-6xl mt-20">Chess</h1>
      <div className="flex items-center h-screen">
        <button
        onClick={() => navigate("/chess")}
          className="
            relative overflow-hidden
            rounded-[5px]
            px-8 py-4
            font-bold tracking-[5px] uppercase
            cursor-pointer
            text-[#108ae0] text-[15px]
            border-2 border-[#108ae0]
            transition-all duration-700
            hover:text-white
            hover:scale-110
            hover:outline-[#108ae0]
            hover:shadow-[4px_5px_17px_-4px_#268391]
            before:content-['']
            before:absolute
            before:-left-12.5
            before:top-0
            before:w-0
            before:h-full
            before:bg-[#108ae0]
            before:skew-x-45
            before:-z-10
            before:transition-[width]
            before:duration-700
            hover:before:w-[250%]
          "
        >
          Play
        </button>
      </div>
    </div>
  );
};

export default Home;


<button className="relative inline-flex items-center justify-center px-6 py-3 overflow-hidden font-bold text-white rounded-md shadow-2xl group">
    <span className="absolute inset-0 w-full h-full transition duration-300 ease-out opacity-0 bg-linear-to-br from-pink-600 via-purple-700 to-blue-400 group-hover:opacity-100"></span>
    <span className="absolute top-0 left-0 w-full bg-linear-to-b from-white to-transparent opacity-5 h-1/3"></span>
    <span className="absolute bottom-0 left-0 w-full h-1/3 bg-linear-to-t from-white to-transparent opacity-5"></span>
    <span className="absolute bottom-0 left-0 w-4 h-full bg-linear-to-r from-white to-transparent opacity-5"></span>
    <span className="absolute bottom-0 right-0 w-4 h-full bg-linear-to-l from-white to-transparent opacity-5"></span>
    <span className="absolute inset-0 w-full h-full border border-white rounded-md opacity-10"></span>
    <span className="absolute w-0 h-0 transition-all duration-300 ease-out bg-white rounded-full group-hover:w-56 group-hover:h-56 opacity-5"></span>
    <span className="relative">Button Text</span>
</button>