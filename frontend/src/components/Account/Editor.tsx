import { X } from "lucide-react";
import ColorPicker from "./ColorPicker";
import { useState } from "react";
import Preview from "./Preview";
import { useAuth } from "../AuthProvider";

interface Props {
  onClose: () => void;
  onSaved: () => void;
  open: boolean;
}

const Editor = ({ open, onClose, onSaved }: Props) => {
  const [colorOpen, setColorOpen] = useState<boolean>(false);
  const [color, setColor] = useState<string>("");
  const [previewOpen, setPreviewOpen] = useState<boolean>(false);
  const [newUsername, setNewUsername] = useState<string>("");
  const [newPfp, setNewPfp] = useState<string>("");

  const {token} = useAuth();

  async function ChangeProfil(){
    try{
      const url = 'http://127.0.0.1:8000/api/users/me'

      const body : {username?: string, avatar?: string} = {}
      if (newUsername) body.username = newUsername;
      if (newPfp) body.avatar = newPfp;

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
      console.log('changements success')
      setNewUsername("");
      setNewPfp("");
      onSaved();
      return true;
    }
    catch{
      console.log('error changes');
    }
  }

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
                    w-[90%] max-w-2xl
                    transition-all duration-500 ease-out
                    ${open ? "opacity-100 scale-100" : "opacity-0 scale-95"}
                    `}
      >
        <div className="w-full flex justify-center items-center">
          <div className="mt-10 flex flex-col text-white w-full">
            <div className="bg-mist-800 max-h-[90vh] flex justify-center items-center flex-col rounded-lg p-5 ">
              <button
                onClick={onClose}
                className="cursor-pointer place-self-end"
              >
                <X size={30} />
              </button>
              <h1 className="text-2xl font-extrabold">Profile Editor</h1>
              <div
                id="pfp-editor"
                className=" h-1/2 max-h-70 border-b border-mist-700 rounded-sm p-2 flex flex-col justify-center items-center gap-4 w-[80%] min-h-32 sm:min-h-40"
              >
                <h2 className="text-xl">Edit Pfp</h2>
                <input value={newPfp} onChange={(event) => {setNewPfp(event.target.value)}} className="input" placeholder="New pfp link"></input>
              </div>
              <div
                id="username-editor"
                className="h-1/2 max-h-70 rounded-sm w-[80%] border-b border-mist-700 p-2 pt-0 flex flex-col justify-center items-center gap-4 min-h-32 sm:min-h-40"
              >
                <h2 className="text-xl">Edit Username</h2>
                <input value={newUsername} onChange={(event) => setNewUsername(event.target.value)} className="input" placeholder="New username"></input>
              </div>
              <div
                id="color-editor"
                className="h-1/2 max-h-70 rounded-sm w-[80%] mb-2 p-2 pt-0 flex flex-col justify-center items-center gap-4 min-h-32 sm:min-h-40"
              >
                <h2 className="text-xl">ChessBoard Color</h2>
                <div className="flex w-full h-full justify-center items-center gap-5">
                  <div onClick={() => {
                        setColorOpen(true);
                        setColor("--light-tile");
                      }}
                      className="cursor-pointer w-1/3 bg-white hover:scale-105 duration-400 text-black rounded-md p-2 text-center">
                    <p>
                      Light Tile
                    </p>
                </div>
                <div onClick={() => {
                      setColorOpen(true);
                      setColor("--dark-tile");
                    }}
                    className="cursor-pointer w-1/3 bg-gray-500 hover:scale-105 duration-400 text-black rounded-md p-2 text-center"
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
                className="relative inline-flex items-center justify-center mt-3 px-6 py-3 overflow-hidden font-bold text-white hover:text-gray-700 rounded-md shadow-2xl group"
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
                colorOpen={colorOpen}
                Color={color}
                colorOnClose={() => setColorOpen(false)}
              />
              <Preview 
                previewOpen={previewOpen}
                previewOnClose={() => setPreviewOpen(false)}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Editor;
