import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { useNavigate } from "react-router-dom";

type LoginType = {
  username: string;
  token: string;
};

export type ProfilType = {
  username: string;
  email: string;
  avatar: string;
  board_light_color: string;
  board_dark_color: string;
};

const emptyProfil: ProfilType = {
  username: "",
  email: "",
  avatar: "",
  board_light_color: "",
  board_dark_color: "",
};

interface ProviderProps {
  user: string | null;
  token: string;
  profil: ProfilType;
  login(data: LoginType): void;
  logout(): void;
}

const AuthContext = createContext<ProviderProps>({
  user: null,
  token: "",
  profil: emptyProfil,
  login: () => {},
  logout: () => {},
});

const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [profil, setProfil] = useState<ProfilType>(emptyProfil);
  const storedInfo = localStorage.getItem("user")
    ? JSON.parse(localStorage.getItem("user") || "{}")
    : null;
  const [user, setUser] = useState<string | null>(storedInfo?.username);
  const [token, setToken] = useState<string>(storedInfo?.token || "");
  const navigate = useNavigate();

  const login = (data: LoginType) => {
    setTimeout(() => {
      setUser(data.username);
      setToken(data.token);
      const obj = { username: data.username, token: data.token };
      localStorage.setItem("user", JSON.stringify(obj));
      navigate("/");
    }, 1000);
  };

  const logout = useCallback(() => {
    setUser(null);
    setToken("");
    setProfil(emptyProfil);
    localStorage.removeItem("user");
    console.log("logout appelé");
    navigate("/login");
  }, [navigate]);

  useEffect(() => {
    if (!token) return;

    const checker = async () => {
      try {
        const response = await fetch("http://127.0.0.1:8000/api/users/me", {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!response.ok) {
          logout();
        }
        if(response.ok) setProfil(await response.json());
      } catch {
        console.log("error");
      }
    };
    checker();
  }, [token, logout]);

  return (
    <AuthContext.Provider value={{ user, token, login, logout, profil}}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthProvider;

export const useAuth = () => {
  return useContext(AuthContext);
};
