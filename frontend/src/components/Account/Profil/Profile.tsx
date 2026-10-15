import Header from "../../Navbar/Header";
import Editor from "./Editor";
import { useCallback, useEffect, useState } from "react";
import { useAuth, type ProfilType } from "../../AuthProvider";
import { UserRoundPen } from "lucide-react";
import Chart from "./Chart";
import { API } from "../../Chess/utils/api";

interface MatchHistory {
    opponent: string,
    outcome: string,
    moves_played: number,
    played_at: string
}

const Profil = () => {
  const [open, setOpen] = useState<boolean>(false);
  const [profil, setProfil] = useState<ProfilType>();
  const [history, setHistory] = useState<MatchHistory[] | null>(null);

  const { token } = useAuth();

  async function showHistory(){
    try{
      const response = await fetch(`${API}/stats/history`, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`
        },
      })
      if(!response.ok) return;
      const infos = await response.json();
      const tmp: MatchHistory[] = infos.map((s : MatchHistory) => {
        const date = new Date(s.played_at)
        return {
          ...s,
          played_at: date.toLocaleDateString("fr-FR")
        }
      })
      setHistory(tmp);
    }
    catch{}
  }

  const getProfilInfos = useCallback(async () => {
    if (!token) return;
    try {
      const response = await fetch("http://127.0.0.1:8000/api/users/me", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) return;
      let infos = await response.json();
      setProfil(infos);
    } catch (err) {
      console.error(err);
    }
  }, [token]);

  useEffect(() => {
    getProfilInfos();
    showHistory();
  }, [getProfilInfos]);

  return (
    <div>
      <Header />
      <div
        className="
          w-full 
          min-h-[calc(100vh-56px)] 
          flex 
          flex-col 
          justify-center 
          items-center"
      >
        <div className="w-[75%] bg-black/20 backdrop-blur-xs rounded-md border border-white/50 overflow-hidden">
          <div id="profil-banner" className="h-50 w-full p-4">
          <div className="w-full h-full bg-white/3 rounded-md flex flex-row items-center justify-center">
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
              <div className={`w-1/3 h-full flex justify-center items-center`}>
                <img
                  src={profil?.avatar}
                  alt="pfp"
                  id="pfp"
                  className="h-[65%] aspect-square rounded-full hover:brightness-50 cursor-pointer object-cover"
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
            
          </div>
          <div className="h-100 w-full flex justify-center items-center">
            <div className="w-1/2 h-full p-4">
              <div className="w-full h-full bg-white/3 flex justify-center items-center rounded-md p-20">
                <Chart username={profil ? profil.username : ""} />
              </div>
            </div>
            <div className="w-1/2 h-full p-4">
              <div className="w-full h-full bg-white/3 flex flex-col justify-center items-center rounded-md ">
                <div className="p-2 border-b w-full text-center font-bold">
                  <h1>HISTORY</h1>
                </div>
                {
                  history 
                  ?(<div className="w-full min-h-0 flex-1 flex-col justify-center items-center overflow-scroll scroll-smooth">
                    {
                      history.map((match, i) => (
                      <div className={`w-full flex items-center justify-center`}>
                        <div className={`w-full h-full flex flex-row justify-center items-center p-2 md:p-5 sm:p-3 gap-2 md:gap-5 lg:gap-7 ${i % 2 === 0 ? "bg-gray-50/5" : ''} text-justify`}>
                          <p className={`${match.outcome === "win" ? "text-green-800": match.outcome === "draw" ? "text-orange-800" : "text-red-800"} text-center`}>{`${match.outcome.toUpperCase()}`}</p>
                          <p className="text-center">{`Opponent: ${match.opponent}`}</p>
                          <p className="text-center">{`Moves: ${match.moves_played}`}</p>
                          <p className="text-center">{
                            `${match.played_at}`
                          }</p>
                        </div>
                      </div>
                      ))
                    }
                  </div> 
                  )
                  : (<p>No match found ...</p>)
                }
              </div>
            </div>
          </div>
        </div>

        {
          <Editor
            open={open}
            onClose={() => setOpen(false)}
            onSaved={getProfilInfos}
          />
        }
      </div>
    </div>
  );
};

export default Profil;
