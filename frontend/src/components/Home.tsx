// import ChessPreview from "./Chess/ChessPreview";
// import Header from "./Navbar/Header";
// import { useNavigate } from "react-router-dom";

// const Home = () => {
//   const navigate = useNavigate();
//   return (
//     <div className="flex flex-col items-center h-screen">
//       <Header />
//       <h1 className="text-6xl mt-15 uppercase border-2">Chess</h1>
//       <div className="flex flex-col items-center border justify-center h-screen gap-0">
//         <ChessPreview />
//         <select className="select select-primary w-75 h-10.5">
//         <option disabled selected>
//           Gamemode
//         </option>
//         <option>1</option>
//         <option>2</option>
//         <option>3</option>
//       </select>
//         <button
//           onClick={() => navigate("/mode")}
//           className="
//               relative z-0
//               w-75 h-13.5
//               border-0 outline-none
//               text-black
//               bg-taupe-300
//               cursor-pointer
//               rounded-[10px]

//               before:content-['']
//               before:absolute
//               before:-top-0.5 before:-left-0.5
//               before:-z-10
//               before:w-[calc(100%+4px)]
//               before:h-[calc(100%+4px)]
//               before:rounded-[10px]
//               before:bg-[linear-gradient(45deg,#ff0000,#ff7300,#fffb00,#48ff00,#00ffd5,#002bff,#7a00ff,#ff00c8,#ff0000)]
//               before:bg-size-[400%_400%]
//               before:blur-[10px]
//               before:opacity-0
//               before:transition-opacity
//               before:duration-300
//               hover:before:opacity-100
//               before:animate-[glowing_20s_linear_infinite]

//               after:content-['']
//               after:absolute
//               after:inset-0
//               after:-z-10
//               after:w-full
//               after:h-full
//               after:rounded-[10px]
//               after:bg-taupe-300
//             "
//         >
//           Play
//         </button>
//       </div>
//     </div>
//   );
// };

// export default Home;
import ChessPreview from "./Chess/ChessPreview";
import Header from "./Navbar/Header";
import { useNavigate } from "react-router-dom";

const Home = () => {
  const navigate = useNavigate();
  return (
    <div className="flex flex-col items-center min-h-screen">
      <Header />
      <div className="flex flex-col justify-center items-center flex-1 w-full px-4">
        <h1 className="text-4xl sm:text-6xl md:text-7xl m-6 sm:m-10 uppercase">Chess</h1>
        <div className="flex flex-col items-center justify-start gap-0 w-full">
          <div
          className="
                relative z-0
                border-0 outline-none
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
                before:transition-opacity
                before:duration-300
                before:opacity-100
                before:animate-[glowing_20s_linear_infinite]
                after:content-['']
                after:absolute
                after:inset-0
                after:-z-10
                after:w-full
                after:h-full
                after:rounded-[10px]
              ">
            <ChessPreview />
          </div>
          <div className="flex flex-col items-center m-6 sm:m-9 gap-4 w-full max-w-75">
            <select className="select select-primary w-full h-10.5">
              <option disabled selected>
                Gamemode
              </option>
              <option>1</option>
              <option>2</option>
              <option>3</option>
            </select>
            <button
              onClick={() => navigate("/mode")}
              className="
                relative z-0
                w-full h-13.5
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
      </div>
    </div>
  );
};

export default Home;