import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "./AuthProvider";

const DefaultLayout = () => {

    const auth = useAuth();

    if (auth.token === "")
        return <Navigate to="/login" />;

    return <Outlet />;
}
export default DefaultLayout;