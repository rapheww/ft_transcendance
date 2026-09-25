import { useNavigate } from "react-router-dom";
import Header from "../Navbar/Header";
import Chart from "./Chart";
import { useState } from "react";

const Profil = () => {
  const navigate = useNavigate();
    const [pfp, setPfp] = useState<string>(localStorage.getItem("pfp") || "https://shorturl.at/Jm5fo");
  
  return (
    <div>
      <Header />
      <div 
        className="
          w-full 
          min-h-[calc(100vh-72px)] 
          flex 
          flex-col 
          justify-center 
          items-center"
      >
        <div id="profil-banner" className="h-50 w-[75%]">
          <div 
            className="
              w-full 
              h-full
              bg-black
              bg-no-repeat
              bg-cover
              flex
              flex-row
              items-center
              justify-center
              rounded-t-md"
            >
            <div className=" w-1/3 h-full flex justify-center items-center">
              <img 
                src={pfp} 
                alt="pfp" 
                id="pfp"
                className="h-[60%] rounded-full hover:brightness-50 cursor-pointer"
                onClick={() => navigate("/editor")}
              />
            </div>
            <div className=" w-1/3 h-full flex justify-center items-center">
              <p className="text-center">Username</p>
            </div>
            <div className=" w-1/3 h-full flex justify-center items-center">
              <p className="text-center">Guilde</p>
            </div>
          </div>
        </div>
        <div id="profil-banner" className="bg-mist-900 rounded-b-md h-100 w-[75%] flex justify-center items-center">
          <Chart />
        </div>
      </div>
    </div>
  );
};

export default Profil;
