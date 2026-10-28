import { X } from "lucide-react";
import { useEffect, useState } from "react";
import type { ProfilType } from "../../AuthProvider";
import Chart from "../../Account/Profil/Chart";
import { API } from "../utils/api";

interface Props {
  onClose: () => void;
  open: boolean;
  username: string;
}

const ProfilePreview = ({ onClose, open, username }: Props) => {
  const [profil, setProfil] = useState<ProfilType | null>();
  useEffect(() => {
    if (!open || !username) return;
    (async () => {
      try {
        const response = await fetch(
          `${API}/users/${username}`,
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
          <div className="w-[75%] bg-black/70 backdrop-blur-sm rounded-md border border-white/50 overflow-hidden">
            <div id="profil-banner" className="h-50 w-full p-4">
              <button
                onClick={() => {
                  setProfil(null);
                  onClose();
                }}
                className="absolute top-2 right-2 z-10 cursor-pointer p-1 rounded-lg hover:bg-gray-400/30"
              >
                <X size={30} />
              </button>
              <div className="w-full h-full bg-white/15 rounded-md flex flex-row items-center justify-center">
                <div
                  className="
              w-full
              h-full
              bg-no-repeat
              bg-cover
              flex
              flex-row
              items-center
              justify-center
              rounded-t-md"
                >
                  <div
                    className={`w-1/3 h-full flex justify-center items-center`}
                  >
                    <img
                      src={profil?.avatar}
                      alt="pfp"
                      id="pfp"
                      className="h-[65%] aspect-square rounded-full hover:brightness-50 cursor-pointer object-cover"
                    />
                  </div>
                  <div className=" w-1/3 h-full flex justify-center items-center">
                    <p className="text-center">{profil?.username}</p>
                  </div>
                  <div className=" w-1/3 h-full flex justify-center items-center">
                    <p className="text-center">{profil?.email}</p>
                  </div>
                </div>
              </div>
            </div>
            <div className="h-100 w-full flex justify-center items-center">
              <div className="w-full h-full p-4">
                <div className="w-full h-full bg-white/15 flex justify-center items-center rounded-md p-20">
                  <Chart username={profil ? profil.username : ""} />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePreview;