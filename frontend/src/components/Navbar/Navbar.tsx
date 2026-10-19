import { NavLink } from "react-router-dom";
import { Menu, X } from "lucide-react";
import { useState } from "react";
import { useAuth } from "../AuthProvider";

const NavLinks = () => {
  const { token, logout } = useAuth();
  const isLogged : boolean = token != '' ? true : false;
  return (
    <>
      {
        isLogged ? (
          <>
            <NavLink to="/tournaments" className="hover:bg-white/10 p-2 rounded-sm">Tournaments</NavLink>
            <NavLink to="/profile" className="hover:bg-white/10 p-2 rounded-sm">Profile</NavLink>
            <NavLink onClick={logout} to="/" className="hover:bg-white/10 p-2 rounded-sm">Logout</NavLink>
          </>
        ) : (
          <NavLink to="/login" className="hover:bg-white/10 p-2 rounded-sm">Login</NavLink>
        )
      }
    </>
  );
};

const Navbar = () => {
  const [isOpen, setIsOpen] = useState(false);
  const toggleNavbar = () => {
    setIsOpen(!isOpen);
  };
  return (
    <>
      <nav className="flex justify-end w-1/3">
        <div className="hidden w-full justify-end gap-30 md:flex lg:mr-15 md:mr-10 sm:mr-5">
          <NavLinks />
        </div>
        <div className="md:hidden">
          <button onClick={toggleNavbar}>{isOpen ? <X /> : <Menu />}</button>
        </div>
      </nav>
      {isOpen && (
        <div className="flex flex-col items-center basis-full gap-4 py-2">
          <NavLinks />
        </div>
      )}
    </>
  );
};

export default Navbar;
