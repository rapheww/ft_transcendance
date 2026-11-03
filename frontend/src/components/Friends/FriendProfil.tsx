import { useCallback, useEffect, useRef, useState } from "react";
import Chart from "../Account/Profil/Chart";
import Header from "../Navbar/Header";
import { useAuth, type ProfilType } from "../AuthProvider";
import { API } from "../Chess/utils/api";
import { useParams } from "react-router-dom";
import { usePrivateChat } from "./PrivateChat";

export type Message = {
  id: number;
  sender_id: number;
  sender_username: string;
  message: string;
  created_at: string;
};

const FriendProfil = () => {
  const [profil, setProfil] = useState<ProfilType>();
  const [chat, setChat] = useState<Message[] | null>(null);
  const [chatId, setChatId] = useState<number | null>(null);
  const [message, setMessage] = useState<string>("");
  const chatRef = useRef<HTMLDivElement>(null);

  const { token, user } = useAuth();
  const { friendName, friendId } = useParams<{
    friendName: string;
    friendId: string;
  }>();

  const { live, send } = usePrivateChat(chatId, token);

  const messages = [...(chat ?? []), ...live].filter(
    (m, i, arr) => arr.findIndex((x) => x.id === m.id) === i,
  );

  async function StartChat() {
    try {
      const response = await fetch(
        `${API}/private-chat/conversations/${friendId}`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      );
      if (!response.ok) return;
      const infos = await response.json();
      if (!infos) return;
      setChatId(infos.id);
    } catch {}
  }

  async function ResumeChat() {
    if (!chatId) return;
    try {
      const response = await fetch(
        `${API}/private-chat/conversations/${chatId}/messages?offset=0&limit=100`,
        {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      );
      if (!response.ok) return;
      const infos = await response.json();
      if (!infos) return;
      setChat(infos.items);
    } catch {}
  }

  const getProfilInfos = useCallback(async () => {
    if (!token) return;
    try {
      const response = await fetch(`${API}/users/${friendName}`, {
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
  }, [getProfilInfos]);

  useEffect(() => {
    if (token && friendId) StartChat();
  }, [token, friendId]);

  useEffect(() => {
    if (chatId) ResumeChat();
  }, [chatId]);

  useEffect(() => {
    // Faire défiler la liste jusqu'aux nouveaux coups reçus sans demander au joueur de le faire.
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }
  }, [messages.length]);

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
          items-center
          py-6"
      >
        <div
          className={`w-[92%] md:w-[85%] xl:w-[75%] bg-black/20 backdrop-blur-xs rounded-md border border-white/15`}
        >
          <div id="profil-banner" className="sm:h-60 lg:h-64 w-full p-4">
            <div className="w-full h-full bg-white/3 rounded-md flex flex-row items-center justify-center">
              <div
                className="
                w-full
                h-full
                bg-no-repeat
                bg-cover
                flex
                flex-col
                sm:flex-row
                gap-3
                py-4
                sm:gap-0
                sm:py-0
                items-center
                justify-center
                rounded-t-md"
              >
                <div className="w-full sm:w-1/3 sm:h-full flex justify-center items-center">
                  <img
                    src={profil?.avatar}
                    alt="pfp"
                    id="pfp"
                    className="h-24 sm:h-[65%] aspect-square rounded-full object-cover"
                  />
                </div>
                <div className="w-full sm:w-1/3 sm:h-full flex justify-center items-center px-2">
                  <p className="text-center wrap-break-word">
                    {profil?.username}
                  </p>
                </div>
                <div className="w-full sm:w-1/3 sm:h-full flex justify-center items-center px-2">
                  <p className="text-center break-all">{profil?.email}</p>
                </div>
              </div>
            </div>
          </div>
          <div className="w-full flex flex-col lg:flex-row justify-center items-center lg:items-stretch lg:h-100">
            <div className="w-full lg:w-1/2 lg:h-full p-4">
              <div className="w-full h-full lg:h-full bg-white/3 flex justify-center items-center rounded-md p-2 sm:p-4 lg:p-5">
                <Chart username={friendName ? friendName : ""} />
              </div>
            </div>
            <div className="w-full lg:w-1/2 lg:h-full p-4">
              <div className="w-full h-80 lg:h-full bg-white/3 flex flex-col rounded-md">
                <div className="flex items-center gap-2 p-2 px-4 border-b w-full font-bold shrink-0">
                  <h1>CHAT</h1>
                </div>

                <div className="w-full min-h-0 flex-1 overflow-y-auto scroll-smooth" ref={chatRef}>
                  {messages &&
                    messages.map((c) => (
                      <div
                        key={c.id}
                        className={`flex flex-row items-center gap-2 w-full p-2 ${c.sender_username != user ? "bg-white/5" : ""} hover:bg-white/10`}
                      >
                        <p className="shrink-0 text-sm">
                          {c.sender_username}:{" "}
                        </p>
                        <p className="min-w-0 wrap-break-word">{c.message}</p>
                      </div>
                    ))}
                  {(!messages || messages.length === 0) && (
                    <div className="w-full h-full p-3 flex justify-center items-center">
                      "No chat"
                    </div>
                  )}
                </div>

                <form
                  className="shrink-0 flex flex-row gap-2 p-2 border-t border-white/15"
                  onSubmit={(e) => {
                    e.preventDefault();
                    if (!message.trim()) return;
                    if (send(message)) setMessage("");
                  }}
                >
                  <input
                    type="text"
                    placeholder="Message..."
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    className="flex-1 min-w-0 outline-0 px-2 h-9 rounded-md bg-white/5"
                  />
                  <button
                    type="submit"
                    className="relative inline-flex items-center justify-center h-9 px-4 text-sm font-bold text-white hover:text-gray-700 overflow-hidden rounded-md shadow-2xl group shrink-0"
                  >
                    <span className="absolute inset-0 w-full h-full transition duration-350 ease-in opacity-0 bg-linear-to-br from-white via-gray-200 to-white group-hover:opacity-100"></span>
                    <span className="absolute top-0 left-0 w-full bg-linear-to-b from-white to-transparent opacity-5 h-1/3"></span>
                    <span className="absolute bottom-0 left-0 w-full h-1/3 bg-linear-to-t from-white to-transparent opacity-5"></span>
                    <span className="absolute bottom-0 left-0 w-4 h-full bg-linear-to-r from-white to-transparent opacity-5"></span>
                    <span className="absolute bottom-0 right-0 w-4 h-full bg-linear-to-l from-white to-transparent opacity-5"></span>
                    <span className="absolute inset-0 w-full h-full border border-white rounded-md opacity-10"></span>
                    <span className="absolute w-0 h-0 transition-all duration-350 ease-out bg-white rounded-full group-hover:w-56 group-hover:h-56 opacity-5"></span>
                    <span className="relative">Send</span>
                  </button>
                </form>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FriendProfil;
