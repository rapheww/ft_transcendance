import { NavLink } from "react-router-dom";

const Logo = () => {
  return (
    <div className="logo w-14 h-14">
      <NavLink to="/"><img src="/src/assets/king_w.png" alt="logo"></img></NavLink>
    </div>
  );
};

export default Logo;