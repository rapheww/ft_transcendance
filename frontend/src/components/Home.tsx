import Header from "./Navbar/Header";
import { useNavigate } from "react-router-dom";

const Home = () => {
  const navigate = useNavigate();
  return (
    <div className="flex flex-col items-center h-screen">
      <Header />
      <h1 className="text-6xl mt-20 uppercase">Chess</h1>
      <div className="flex flex-col items-center justify-center h-screen">
        <button
          onClick={() => navigate("/mode")}
          className="
              relative z-0
              w-75 h-13.5
              border-0 outline-none
              text-black
              bg-taupe-300
              cursor-pointer
              rounded-[10px]

              before:content-['']
              before:absolute
              before:-top-0.5 before:-left-0.5
              before:-z-10
              before:w-[calc(100%+4px)]
              before:h-[calc(100%+4px)]
              before:rounded-[10px]
              before:bg-[linear-gradient(45deg,#ff0000,#ff7300,#fffb00,#48ff00,#00ffd5,#002bff,#7a00ff,#ff00c8,#ff0000)]
              before:bg-size-[400%_400%]
              before:blur-[10px]
              before:opacity-0
              before:transition-opacity
              before:duration-300
              hover:before:opacity-100
              before:animate-[glowing_20s_linear_infinite]

              after:content-['']
              after:absolute
              after:inset-0
              after:-z-10
              after:w-full
              after:h-full
              after:rounded-[10px]
              after:bg-taupe-300
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
</button>;
