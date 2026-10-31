import { useState } from "react";
import Header from "../Navbar/Header";
import { Search, X } from "lucide-react";

const FriendsList = () => {
  const [friendsList, setFriendsList] = useState<string[]>(["arthur", "jb", "beuteuduphoenix"])
  const [playerSearch, setPlayerSearch] = useState<string>("")
  const [del, setDel] = useState<string>("")
  const inputClassname = ` ml-2 outline-0 focus:border-white/50 focus-within:border-white/50 h-full w-full lg:text-lg 2xl:text-base`;

  return (
    <div>
      <Header />
      <div
        className="
          w-full
          min-h-[calc(100vh-56px)]
          flex
          flex-col
          items-center
          py-6
          gap-5"
      >
        <div
            className={`w-[92%] md:w-[85%] xl:w-[65%] bg-black/20 backdrop-blur-xs rounded-md border border-white/50 mt-10 h-10 flex flex-row items-center`}
        >
          <form onSubmit={() => {setPlayerSearch("")}} className="w-[95%] h-full rounded-md">
            <input type="text" placeholder="Search player" className={inputClassname} value={playerSearch} onChange={(e) => setPlayerSearch(e.target.value)}/>
          </form>
          <button className="w-[5%] h-full flex justify-end items-center pr-2 rounded-md brightness-50">
            <Search />
          </button>
        </div>
        <div className="w-full flex flex-1 flex-col justify-center items-center">
          
          <div
            className={`w-[92%] md:w-[85%] xl:w-[75%] bg-black/20 backdrop-blur-xs rounded-md border border-white/50`}
            >
            {friendsList.length === 0 && (
              <p className="h-20 w-full flex items-center justify-center text-sm md:text-xl">No friends, add other players to text us</p>
            )}
            { friendsList.map((friend, i) => (
              <div className={`w-full flex flex-row h-full p-2 lg:p-4 gap-2 ${i % 2 === 0 ? '' : 'bg-white/3'}`} key={i}>
                <p className="w-[20%]">online</p>
                <p className="w-[76%]">{friend}</p>
                <button className="flex flex-row">
                  <X className={`hover:cursor-pointer hover:bg-white/15 rounded-md`}/>
                </button>
              </div>
            ))
            }
          </div>
        </div>
      </div>
    </div>
  );
};

export default FriendsList;