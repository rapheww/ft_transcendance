import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { useNavigate } from "react-router-dom";
import { API } from "./Chess/utils/api";

type LoginType = {
  username: string;
  token: string;
  refreshToken?: string;
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
  refreshToken?: string;
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
  const [refreshToken, setRefreshToken] = useState<string | undefined>(
    storedInfo?.refresh_token,
  );
  const [refreshTimerId, setRefreshTimerId] = useState<number | null>(null);
  const navigate = useNavigate();

  const login = (data: LoginType) => {
    setTimeout(() => {
      setUser(data.username);
      setToken(data.token);
      setRefreshToken(data.refreshToken);
      const obj: any = { username: data.username, token: data.token };
      if (data.refreshToken) obj.refresh_token = data.refreshToken;
      localStorage.setItem("user", JSON.stringify(obj));
      navigate("/");
    }, 1000);
  };

  const logout = useCallback(() => {
    setUser(null);
    setToken("");
    setProfil(emptyProfil);
    localStorage.removeItem("user");
    navigate("/login");
  }, [navigate]);

  useEffect(() => {
    if (!token) return;

    async function refreshAccessToken(): Promise<boolean> {
      if (!refreshToken) return false;
      try {
        const resp = await fetch(`${API}/auth/refresh`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
        if (!resp.ok) throw new Error("refresh failed");
        const data = await resp.json();
        setToken(data.access_token);
        setRefreshToken(data.refresh_token);
        const obj: any = { username: user, token: data.access_token };
        if (data.refresh_token) obj.refresh_token = data.refresh_token;
        localStorage.setItem("user", JSON.stringify(obj));
        return true;
      } catch {
        logout();
        return false;
      }
    }

    const checker = async () => {
      try {
        const response = await fetch(`${API}/users/me`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!response.ok) {
          logout();
        }
        if(response.ok) setProfil(await response.json());
      } catch {
      }
    };
    // parse expiry and schedule refresh
    function parseExpFromToken(t: string): number | null {
      try {
        const payload = t.split(".")[1];
        if (!payload) return null;
        const base64 = payload.replace(/-/g, "+").replace(/_/g, "/");
        const decoded = JSON.parse(atob(base64.padEnd(Math.ceil(base64.length / 4) * 4, "=")));
        const exp = Number(decoded.exp);
        return Number.isFinite(exp) ? exp * 1000 : null;
      } catch {
        return null;
      }
    }
    const expMs = parseExpFromToken(token);
    if (expMs) {
      const now = Date.now();
      const refreshAt = Math.max( Math.min(expMs - 60000, expMs - 5000), now + 5000 );
      const delay = refreshAt - now;
      if (refreshTimerId) {
        window.clearTimeout(refreshTimerId);
        setRefreshTimerId(null);
      }
      const id = window.setTimeout(() => {
        void refreshAccessToken();
      }, delay);
      setRefreshTimerId(id);
    }
    checker();
  }, [token, logout]);

  useEffect(() => {
    return () => {
      if (refreshTimerId) window.clearTimeout(refreshTimerId);
    };
  }, [refreshTimerId]);

  return (
    <AuthContext.Provider value={{ user, token, login, logout, profil, refreshToken }}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthProvider;

export const useAuth = () => {
  return useContext(AuthContext);
};
