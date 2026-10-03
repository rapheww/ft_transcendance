import { createContext, useContext, useState } from "react";
import { useNavigate } from "react-router-dom";

type LoginType = {
    username:string;
    password:string;
}

interface ProviderProps{
    user:string | null,
    token: string,
    login(data: LoginType): void,
    logout(): void,
}

const AuthContext = createContext<ProviderProps>({
    user: null,
    token: '',
    login: () => {},
    logout: () => {}
})


const AuthProvider = ({children} : {children : React.ReactNode}) => {
  const storedInfo = localStorage.getItem('user') ? JSON.parse(localStorage.getItem('user') || '{}') : null;
  const [user, setUser] = useState<string | null>(storedInfo?.username);
  const [token, setToken] = useState<string>(storedInfo?.token || '');
  const navigate = useNavigate();
  
  const login = (data:LoginType) => {
    const t = "abc123";
    setTimeout(() => {
        setUser(data.username);
        setToken(t);
        navigate('/');
    }, 1000)
  }

  const logout = () => {
    setUser(null)
    setToken('')
  }

  return (
    <AuthContext.Provider value={{user, token, login, logout}}>
        {children}
    </AuthContext.Provider>
  );


};

export default AuthProvider;

export const useAuth = () => {
    return useContext(AuthContext)
}