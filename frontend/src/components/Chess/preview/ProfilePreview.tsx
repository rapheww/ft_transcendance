import { X } from "lucide-react";
import { useEffect, useState } from "react";
import type { ProfilType } from "../../AuthProvider";
import Chart from "../../Account/Profil/Chart";

interface Props {
  onClose: () => void;
  open: boolean;
  username: string;
}

const ProfilePreview = ({ onClose, open, username }: Props) => {
  const [profil, setProfil] = useState<ProfilType | null>();
  const defaultPfp = 'frontend/src/assets/pfp.png';
  useEffect(() => {
    if (!open || !username) return;
    setProfil(undefined);
    (async () => {
      try {
        const response = await fetch(
          `http://127.0.0.1:8000/api/users/${username}`,
        );
        if (!response.ok) return;
        const infos = await response.json();
        setProfil(infos);
      } catch (err) {
        console.error(err);
      }
    })();
  }, [open, username]);

  return (
    <div
      className={`
            fixed inset-0
            flex justify-center items-center
            bg-black/30 backdrop-blur-sm
            transition-opacity duration-500 ease-out
            ${open ? "opacity-100" : "opacity-0 pointer-events-none"}
            `}
    >
      <div
        className={`
                    w-[90%] max-w-6xl
                    transition-all duration-500 ease-out
                    ${open ? "opacity-100 scale-100" : "opacity-0 scale-95"}
                    `}
      >
        <div
          className="
          w-full 
          min-h-[calc(100vh-56px)] 
          flex 
          flex-col 
          justify-center 
          items-center"
        >
          <div id="profil-banner" className="h-50 w-[75%]">
            <div
              className="
              relative
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
              <button
                onClick={() => {
                  setProfil(null);  
                  onClose();
                }}
                className="absolute top-2 right-2 z-10 cursor-pointer p-1 rounded-lg hover:bg-gray-400/30"
              >
                <X size={30} />
              </button>
              <div className={`w-1/3 h-full flex justify-center items-center`}>
                <img
                  src={profil ? profil.avatar : defaultPfp}
                  id="pfp"
                  fetchPriority="high"
                  className="h-[65%] aspect-square rounded-full object-cover"
                />
              </div>
              <div className=" w-1/3 h-full flex justify-center items-center">
                <p className="text-center">{profil ? profil.username : 'unknown'}</p>
              </div>
              <div className=" w-1/3 h-full flex justify-center items-center">
                <p className="text-center">{profil ? profil.email : 'unknown'}</p>
              </div>
            </div>
          </div>
          <div
            id="profil-banner"
            className="bg-mist-900 rounded-b-md h-100 w-[75%] flex justify-center items-center"
          >
            <Chart username={profil ? profil.username : 'unknown'}/>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePreview;
