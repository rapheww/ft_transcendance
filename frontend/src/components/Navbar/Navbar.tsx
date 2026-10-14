import { NavLink } from "react-router-dom";
import { Menu, X } from "lucide-react";
import { useState } from "react";
import { useAuth } from "../AuthProvider";

const NavLinks = () => {
  const { token, logout } = useAuth();
  const isLogged : boolean = token != '' ? true : false;
  return (
    <>
      <NavLink to="/chess" className="hover:text-blue-300">Play</NavLink>
      {
        isLogged ? (
          <div className="flex w-full justify-between">
            <NavLink to="/profile" className="hover:text-blue-300">Profile</NavLink>
            <NavLink onClick={logout} to="/" className="hover:text-blue-300">Logout</NavLink>
          </div>
        ) : (
          <NavLink to="/login" className="hover:text-blue-300">Login</NavLink>
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
        <div className="hidden w-full justify-end gap-60 md:flex lg:mr-15 md:mr-10 sm:mr-5">
          <NavLinks />
        </div>
        <div className="md:hidden">
          <button onClick={toggleNavbar}>{isOpen ? <X /> : <Menu />}</button>
        </div>
      </nav>
      {isOpen && (
        <div className="flex flex-col items-center basis-full">
          <NavLinks />
        </div>
      )}
    </>
  );
};

export default Navbar;
