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

interface ProviderProps {
  user: string | null;
  token: string;
  login(data: LoginType): void;
  logout(): void;
}

const AuthContext = createContext<ProviderProps>({
  user: null,
  token: "",
  login: () => {},
  logout: () => {},
});

const AuthProvider = ({ children }: { children: React.ReactNode }) => {
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
    localStorage.removeItem("user");
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
      } catch {
        console.log("error");
      }
    };
    checker();
  }, [token, logout]);

  return (
    <AuthContext.Provider value={{ user, token, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthProvider;

export const useAuth = () => {
  return useContext(AuthContext);
};
