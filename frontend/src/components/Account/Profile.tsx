import Header from "../Navbar/Header";
import Chart from "./Chart";
import Editor from "./Editor";
import { useEffect, useState } from "react";
import { useAuth } from "../AuthProvider";
import { UserRoundPen } from "lucide-react";

type Profil = {
  username: string;
  email: string;
  pfp: string;
  darkTile: string;
  lightTile: string;
};

const Profil = () => {
  const [open, setOpen] = useState<boolean>(false);
  const { user } = useAuth();
  const [profil, setProfil] = useState<Profil>();

  useEffect(() => {
    if (!user) return;

    const getProfilInfos = async () => {
      try {
        const response = await fetch(`http://127.0.0.1:8000/api/users/${user}`);
        if (!response.ok) return;
        const infos = await response.json();
        setProfil(infos);
      } catch (err) {
        console.error(err);
      }
    };

    getProfilInfos();
  }, [user]);
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
                src={profil?.pfp}
                alt="pfp"
                id="pfp"
                className="h-[60%] rounded-full hover:brightness-50 cursor-pointer"
                onClick={() => setOpen(true)}
              />
            </div>
            <div className=" w-1/3 h-full flex justify-center items-center">
              <p className="text-center">{profil?.username}</p>
            </div>
            <div className=" w-1/3 h-full flex justify-center items-center">
              <p className="text-center">{profil?.email}</p>
            </div>
            <button onClick={() => setOpen(true)}>
              <UserRoundPen
                className="mr-5 cursor-pointer hover:bg-gray-400/30 rounded-lg p-1"
                size={32}
              />
            </button>
          </div>
        </div>
        <div
          id="profil-banner"
          className="bg-mist-900 rounded-b-md h-100 w-[75%] flex justify-center items-center"
        >
          <Chart />
        </div>
        {<Editor open={open} onClose={() => setOpen(false)} />}
      </div>
    </div>
  );
};

export default Profil;
