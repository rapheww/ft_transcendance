import Header from "../Navbar/Header";
import Chart from "./Chart";
import Editor from "./Editor";
import { useState } from "react";
import { UserRoundPen } from 'lucide-react';

const Profil = () => {
  const [open, setOpen] = useState<boolean>(false)
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
                src="https://shorturl.at/Jm5fo" 
                alt="pfp" 
                id="pfp"
                className="h-[60%] rounded-full hover:brightness-50 cursor-pointer"
                onClick={() => setOpen(true)}
              />
            </div>
            <div className=" w-1/3 h-full flex justify-center items-center">
              <p className="text-center">Username</p>
            </div>
            <div className=" w-1/3 h-full flex justify-center items-center">
              <p className="text-center">Guilde</p>
            </div>
              <button onClick={() => setOpen(true)}><UserRoundPen className="mr-5 cursor-pointer hover:bg-gray-400/30 rounded-lg p-1" size={32}/></button>
          </div>
        </div>
        <div id="profil-banner" className="bg-mist-900 rounded-b-md h-100 w-[75%] flex justify-center items-center">
          <Chart />
        </div>
        {<Editor open={open} onClose={() => setOpen(false)}/>}
      </div>
    </div>
  );
};

export default Profil;
