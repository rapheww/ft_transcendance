import { X } from "lucide-react";
import ColorPicker from "./ColorPicker";
import { useEffect, useState } from "react";
import Preview from "./Preview";
import { useAuth } from "../../AuthProvider";
import { API } from "../../Chess/utils/api";

interface Props {
  onClose: () => void;
  onSaved: () => void;
  open: boolean;
}

const Editor = ({ open, onClose, onSaved }: Props) => {
  const [darkOpen, setDarkOpen] = useState<boolean>(false);
  const [lightOpen, setLightOpen] = useState<boolean>(false);
  const [color, setColor] = useState<string>("");
  const [previewOpen, setPreviewOpen] = useState<boolean>(false);
  const [newUsername, setNewUsername] = useState<string>("");
  const [newPfp, setNewPfp] = useState<string>("");
  const [dark, setDark] = useState<string>("");
  const [light, setLight] = useState<string>("");

  const {token} = useAuth();

  const inputClassname = "input outline-0 border bg-white/3 border-white/50 focus:border-white/50 focus-within:border-white/50 w-full lg:h-10 lg:text-lg"

  async function ChangeProfil(){
    try{
      const url = `${API}/users/me`

      const body : {username?: string, avatar?: string, board_light_color?: string, board_dark_color?: string} = {}
      if (newUsername) body.username = newUsername;
      if (newPfp) body.avatar = newPfp;
      if (dark) body.board_dark_color = dark;
      if (light) body.board_light_color = light;

      const response = await fetch(
        url,{
          method: 'PATCH',
          headers:{
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(body),
        }
      )

      if (response.status != 200){
          alert("changements error");
          return false;
      }
      setNewUsername("");
      setNewPfp("");
      if (body.board_dark_color)
        document.documentElement.style.setProperty("--dark-tile", body.board_dark_color);
      if(body.board_light_color)
        document.documentElement.style.setProperty("--light-tile", body.board_light_color);
      onSaved();
      return true;
    }
    catch{
    }
  }

  useEffect(() => {
    if (!open) return;

    function escHandler(e: globalThis.KeyboardEvent) {
      if (e.key !== "Escape") return;
      if (darkOpen) setDarkOpen(false);
      else if (lightOpen) setLightOpen(false);
      else if (previewOpen) setPreviewOpen(false);
      else onClose();
    }
    document.addEventListener("keydown", escHandler);
    return () => {
      document.removeEventListener("keydown", escHandler);
    };
  }, [open, darkOpen, lightOpen, previewOpen, onClose]);

  return (
    <div
      className={`
            fixed inset-0
            flex justify-center items-center
            bg-black/30 backdrop-blur-md
            transition-opacity duration-500 ease-out
            ${open ? "opacity-100" : "opacity-0 pointer-events-none"}
            `}
    >
      <div
        className={`
                    w-[90%] max-w-xl lg:max-w-2xl
                    transition-all duration-500 ease-out
                    ${open ? "opacity-100 scale-100" : "opacity-0 scale-95"}
                    `}
      >
        <div className="w-full flex justify-center items-center">
          <div className="mt-10 flex flex-col text-white w-full">
            <div className={`bg-black/30 border border-white/30 backdrop:blur-xs max-h-[90vh] ${darkOpen || lightOpen || previewOpen ? 'overflow-hidden' : 'overflow-y-auto'} flex items-center flex-col rounded-lg p-4 sm:p-5 lg:p-8`}>
              <button
                onClick={onClose}
                className="cursor-pointer place-self-end rounded-lg hover:bg-gray-400/30"
              >
                <X size={30} />
              </button>
              <h1 className="text-xl sm:text-2xl lg:text-3xl font-extrabold">Profile Editor</h1>
              <div
                id="pfp-editor"
                className="h-1/2 max-h-70 border-b border-white/30 rounded-sm p-2 flex flex-col justify-center items-center gap-4 lg:gap-5 w-full sm:w-[80%] min-h-32 sm:min-h-40 lg:min-h-44"
              >
                <h2 className="text-lg sm:text-xl lg:text-2xl">Edit Pfp</h2>
                <input value={newPfp} onChange={(event) => {setNewPfp(event.target.value)}} className={inputClassname} placeholder="New pfp link"></input>
              </div>
              <div
                id="username-editor"
                className="h-1/2 max-h-70 rounded-sm w-full sm:w-[80%] border-b border-white/30 p-2 pt-0 flex flex-col justify-center items-center gap-4 lg:gap-5 min-h-32 sm:min-h-40 lg:min-h-44"
              >
                <h2 className="text-lg sm:text-xl lg:text-2xl">Edit Username</h2>
                <input value={newUsername} onChange={(event) => setNewUsername(event.target.value)} className={inputClassname} placeholder="New username"></input>
              </div>
              <div
                id="color-editor"
                className="h-1/2 max-h-70 rounded-sm w-full sm:w-[80%] mb-2 p-2 pt-0 flex flex-col justify-center items-center gap-4 lg:gap-5 min-h-32 sm:min-h-40 lg:min-h-44"
              >
                <h2 className="text-lg sm:text-xl lg:text-2xl">ChessBoard Color</h2>
                <div className="flex w-full h-full justify-center items-center gap-5">
                  <div onClick={() => {
                        setLightOpen(true);
                        setColor("--light-tile");
                      }}
                      className="cursor-pointer w-1/3 bg-white hover:scale-105 duration-400 text-black rounded-md p-2 lg:p-3 lg:text-lg text-center">
                    <p>
                      Light Tile
                    </p>
                </div>
                <div onClick={() => {
                      setDarkOpen(true);
                      setColor("--dark-tile");
                    }}
                    className="cursor-pointer w-1/3 bg-gray-500 hover:scale-105 duration-400 text-black rounded-md p-2 lg:p-3 lg:text-lg text-center"
                >
                    <p>Dark Tile</p>
                 </div>
                      
                </div>
                <div>
                  <p onClick={() => setPreviewOpen(true)} className="text-md p-1 hover:bg-gray-400/20 rounded-md cursor-pointer">View ChessBoard</p>
                </div>
              </div>
              <button 
                onClick={async () => {
                  if (await ChangeProfil())
                    onClose()
                }}
                className="relative inline-flex items-center justify-center mt-3 px-6 py-3 lg:px-8 lg:py-3 lg:text-lg overflow-hidden font-bold text-white hover:text-gray-700 rounded-md shadow-2xl group"
              >
                <span className="absolute inset-0 w-full h-full transition duration-350 ease-in opacity-0 bg-linear-to-br from-white via-gray-200 to-white group-hover:opacity-100"></span>
                <span className="absolute top-0 left-0 w-full bg-linear-to-b from-white to-transparent opacity-5 h-1/3"></span>
                <span className="absolute bottom-0 left-0 w-full h-1/3 bg-linear-to-t from-white to-transparent opacity-5"></span>
                <span className="absolute bottom-0 left-0 w-4 h-full bg-linear-to-r from-white to-transparent opacity-5"></span>
                <span className="absolute bottom-0 right-0 w-4 h-full bg-linear-to-l from-white to-transparent opacity-5"></span>
                <span className="absolute inset-0 w-full h-full border border-white rounded-md opacity-10"></span>
                <span className="absolute w-0 h-0 transition-all duration-350 ease-out bg-white rounded-full group-hover:w-56 group-hover:h-56 opacity-5"></span>
                <span className="relative">Save</span>
              </button>
              <ColorPicker
                colorOpen={darkOpen}
                Color={color}
                colorOnClose={() => setDarkOpen(false)}
                setter={setDark}
              />
              <ColorPicker
                colorOpen={lightOpen}
                Color={color}
                colorOnClose={() => setLightOpen(false)}
                setter={setLight}
              />
              <Preview 
                previewOpen={previewOpen}
                previewOnClose={() => setPreviewOpen(false)}
                dark={dark}
                light={light}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Editor;
