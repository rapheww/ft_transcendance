import { useEffect, useState } from "react";
import Header from "../Navbar/Header";
import { Check, Search, UserRoundPlus, X } from "lucide-react";
import { API } from "../Chess/utils/api";
import { useAuth } from "../AuthProvider";
import { useNavigate } from "react-router-dom";

type Friends = {
  id: number;
  username: string;
  avatar: string;
  online: boolean;
};

type Request = {
  id: 0;
  username: string;
  avatar: string;
  requested_at: string;
  status: string;
};

const FriendsList = () => {
  const [friendsList, setFriendsList] = useState<Friends[] | null>(null);
  const [playerSearch, setPlayerSearch] = useState<string>("");
  const [received, setReceived] = useState<boolean>(true);
  const [send, setSend] = useState<boolean>(false);
  const [incomingRequest, setIncomingRequest] = useState<Request[] | null>(
    null,
  );
  const [outgoingRequest, setOutgoingRequest] = useState<Request[] | null>(
    null,
  );
  const [searchList, setSearchList] = useState<Friends[] | null>(null);
  const [addResponse, setAddResponse] = useState<{message: string, id: number} | null>(null);
  const navigate = useNavigate();
  const inputClassname = ` ml-2 outline-0 focus:border-white/15 focus-within:border-white/15 h-full w-full lg:text-lg 2xl:text-base`;

  const { token } = useAuth();

  async function searchUser(username: string) {
    if (!username) {
      setSearchList(null);
      return;
    }
    try {
      const response = await fetch(`${API}/friends/search?query=${username}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (!response.ok) {
        setSearchList(null);
        return;
      }
      const infos = await response.json();
      if (infos) {
        setSearchList(infos);
      }
    } catch {
    }
  }

  async function getFriendsList() {
    try {
      const response = await fetch(`${API}/friends/`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (!response.ok) {
        setFriendsList(null);
        return;
      }
      const infos = await response.json();
      if (infos) {
        setFriendsList(infos);
      }
    } catch {
    }
  }

  async function sendRequest(id: number) {
    try {
      const response = await fetch(`${API}/friends/requests/${id}`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (!response.ok) {
        const infos = await response.json();
        if (!infos) return;
        throw infos.detail;
        return;
      }
      setAddResponse({message:"Request sent", id: id})
    } catch(error) {
      setAddResponse({message: error as string, id: id})
    }
  }

  async function ShowIncomingRequest() {
    try {
      const response = await fetch(`${API}/friends/requests/incoming`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (!response.ok) {
        setIncomingRequest(null);
        return;
      }
      const infos = await response.json();
      if (!infos) {
        setIncomingRequest(null);
        return;
      }
      setIncomingRequest(infos);
    } catch {
    }
  }

  async function ShowOutgoingRequest() {
    try {
      const response = await fetch(`${API}/friends/requests/outgoing`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (!response.ok) {
        setOutgoingRequest(null);
        return;
      }
      const infos = await response.json();
      if (!infos) {
        setOutgoingRequest(null);
        return;
      }
      setOutgoingRequest(infos);
    } catch {
    }
  }

  async function RemoveFriend(id: number) {
    try {
      const response = await fetch(`${API}/friends/${id}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (!response.ok) {
        return;
      }
      getFriendsList();
    } catch {
    }
  }

  async function AcceptRequest(id: number) {
    try {
      const response = await fetch(`${API}/friends/requests/${id}/accept`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (!response.ok) {
        return;
      }
      ShowIncomingRequest();
      ShowOutgoingRequest();
      getFriendsList();
    } catch {
    }
  }

  async function RefuseRequest(id: number) {
    try {
      const response = await fetch(`${API}/friends/requests/${id}/reject`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (!response.ok) {
        return;
      }
      ShowIncomingRequest();
      ShowOutgoingRequest();
      getFriendsList();
    } catch {
    }
  }

  useEffect(() => {
    if (!token) return;

    getFriendsList();
    ShowIncomingRequest();
    ShowOutgoingRequest();
    const interval = setInterval(() => {
      getFriendsList();
      ShowIncomingRequest();
      ShowOutgoingRequest();
      setAddResponse(null);
    }, 3000);

    return () => clearInterval(interval);
  }, [token]);

  function isFriend(id: number){
    return friendsList?.some((friend) => friend.id === id) ?? false;
  }

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
          className={`w-[60%] md:w-[40%] xl:w-[40%] bg-black/20 backdrop-blur-xs rounded-md border border-white/15 mt-10 h-10 flex flex-row items-center`}
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
            }}
            className="w-[70%] md:w-[80%] lg:w-[95%] h-full rounded-md"
          >
            <input
              type="text"
              placeholder="Search player"
              className={inputClassname}
              value={playerSearch}
              onChange={(e) => {
                setPlayerSearch(e.target.value);
                setAddResponse(null);
                searchUser(e.target.value);
              }}
            />
          </form>
          <button className="w-[30%] md:w-[20%] lg:w-[5%] h-full flex justify-end items-center pr-2 rounded-md brightness-50">
            <Search />
          </button>
        </div>
        <div className="w-full flex flex-1 flex-row justify-center items-start gap-5">
          <div className="w-[50%] md:w-[60%] xl:w-[40%] flex flex-col gap-2">
            <h2 className="text-xl md:text-2xl font-semibold">
              {playerSearch ? "Search result" : "Friends"}
            </h2>
            <div className="w-full bg-black/20 backdrop-blur-xs rounded-md border border-white/15">
              {(!friendsList || friendsList.length === 0) && !searchList && (
                <p className="h-20 w-full flex items-center justify-center text-sm md:text-xl">
                  No friends
                </p>
              )}
              {!searchList &&
                friendsList &&
                friendsList.map((friend, i) => (
                  <div
                    className={`w-full flex flex-row items-center h-full p-2 lg:p-4 gap-2 md:gap-4 ${i % 2 === 0 ? "" : "bg-white/3"} hover:bg-white/5 hover:cursor-pointer`}
                    key={i}
                  >
                    <div className={`w-full flex flex-row items-center h-full p-2 lg:p-4 gap-2 md:gap-4`}
                    onClick={() => navigate(`/friend-profil/${friend.username}/${friend.id}`)}
                    >
                      <span className="w-12 md:w-16 shrink-0 flex justify-center">
                        <span
                          className={`h-2.5 w-2.5 rounded-full ${friend.online ? "bg-green-500" : "bg-gray-500"}`}
                          role="img"
                          aria-label={friend.online ? "Online" : "Offline"}
                          title={friend.online ? "Online" : "Offline"}
                        />
                      </span>
                    <img
                      src={friend.avatar}
                      className="object-cover rounded-full w-10 h-10 md:w-12 md:h-12 shrink-0"
                    />
                    <p className="flex-1 min-w-0 truncate text-sm md:text-base lg:text-lg">
                      {friend.username}
                    </p>
                    </div>
                    <button
                      className="shrink-0 hover:cursor-pointer hover:bg-red-500/25 rounded-md p-1"
                      onClick={() => {
                        RemoveFriend(friend.id);
                      }}
                    >
                      <X />
                    </button>
                  </div>
                ))}
              {searchList &&
                searchList.map((s, i) => {
                  const alreadyFriend = isFriend(s.id)
                  return (
                  <div
                    className={`w-full flex flex-row items-center h-full p-2 lg:p-4 gap-2 md:gap-4 ${i % 2 === 0 ? "" : "bg-white/3"}`}
                    key={i}
                  >
                    <div className={`w-full flex flex-row items-center h-full p-2 lg:p-4 gap-2 md:gap-4 ${alreadyFriend && 'hover:cursor-pointer hover:bg-white/5'}`}
                      onClick={() =>{alreadyFriend && navigate(`/friend-profil/${s.username}/${s.id}`)}}
                    >
                      <span className="w-12 md:w-16 shrink-0 flex justify-center">
                        <span
                          className={`h-2.5 w-2.5 rounded-full ${s.online ? "bg-green-500" : "bg-gray-500"}`}
                          role="img"
                          aria-label={s.online ? "Online" : "Offline"}
                          title={s.online ? "Online" : "Offline"}
                        />
                      </span>
                      <img
                        src={s.avatar}
                        className="object-cover rounded-full w-10 h-10 md:w-12 md:h-12 shrink-0"
                      />
                      <p className="flex-1 min-w-0 truncate text-sm md:text-base lg:text-lg">
                        {s.username}
                      </p>
                      {addResponse && (
                        <p className={`text-sm italic ${addResponse.message === "Request sent" ? 'text-lime-600/80' : 'text-red-700/80'}`}>{  s.id === addResponse.id && !alreadyFriend? addResponse.message : ''}</p>
                      )}
                      <button
                        className={`shrink-0 hover:cursor-pointer hover:bg-lime-500/15 rounded-md p-1 ${alreadyFriend && 'hidden'}`}
                        onClick={() => {
                          sendRequest(s.id);
                        }}
                      >
                        <UserRoundPlus />
                      </button>
                    </div>
                  </div>
)})}
            </div>
          </div>

          <div className="w-[30%] md:w-[25%] flex flex-col gap-2">
            <h2 className="text-xl md:text-2xl font-semibold">Requests</h2>
            <div className="w-full bg-black/20 backdrop-blur-xs rounded-md border border-white/15">
              <div className="flex flex-row w-full border-b border-white/20 justify-center">
                <div
                  className={`flex w-[50%] justify-center p-2 ${received ? "bg-white/5" : "hover:bg-white/5"}`}
                  onClick={() => {
                    setReceived(!received);
                    setSend(!send);
                  }}
                >
                  RECEIVED
                </div>
                <div
                  className={`flex w-[50%] justify-center p-2 ${send ? "bg-white/5" : "hover:bg-white/5"}`}
                  onClick={() => {
                    setReceived(!received);
                    setSend(!send);
                  }}
                >
                  SENT
                </div>
              </div>
              {received &&
                incomingRequest &&
                incomingRequest.map((incoming, i) => (
                  <div
                    className={`w-full flex flex-row items-center h-full p-2 lg:p-4 gap-2 md:gap-3 ${i % 2 === 0 ? "" : "bg-white/3"}`}
                    key={i}
                  >
                    <div className="flex-1 min-w-0 flex flex-row gap-2 items-center">
                      <p className="text-sm md:text-base">
                        {incoming.username}
                      </p>
                      <p className=" truncate text-xs text-gray-200/60">
                        {incoming.status}
                      </p>
                    </div>
                    <div className="flex flex-row gap-1 md:gap-2 shrink-0">
                      <button
                        className="p-1 border border-white/35 rounded-md bg-lime-500/50 hover:brightness-130 duration-300 hover:cursor-pointer"
                        onClick={() => AcceptRequest(incoming.id)}
                      >
                        <Check className="w-4 h-4 md:w-5 md:h-5" />
                      </button>
                      <button
                        className="p-1 border border-white/35 rounded-md bg-red-600/50 hover:brightness-130 duration-300 hover:cursor-pointer"
                        onClick={() => RefuseRequest(incoming.id)}
                      >
                        <X className="w-4 h-4 md:w-5 md:h-5" />
                      </button>
                    </div>
                  </div>
                ))}
              {received &&
                (!incomingRequest || incomingRequest.length === 0) && (
                  <p className="p-2 lg:p-4 w-full flex items-center justify-center text-sm md:text-base h-full">
                    No requests received
                  </p>
                )}

              {send &&
                outgoingRequest &&
                outgoingRequest.map((outgoing, i) => (
                  <div
                    className={`w-full flex flex-row h-full p-2 lg:p-4 gap-2 md:gap-3 ${i % 2 === 0 ? "" : "bg-white/3"}`}
                    key={i}
                  >
                    <p className="text-gray-200/60">{outgoing.status}</p>
                    <p>{outgoing.username}</p>
                  </div>
                ))}
              {send && (!outgoingRequest || outgoingRequest.length === 0) && (
                <p className="p-2 lg:p-4 w-full flex items-center justify-center text-sm md:text-base h-full">
                  No requests sent
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FriendsList;
