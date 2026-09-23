import { NavLink } from "react-router-dom";

const Logo = () => {
  return (
    <div className="logo w-16 h-16">
      <NavLink to="/"><img src="src/assets/king_b.png" alt="logo"></img></NavLink>
    </div>
  );
};

export default Logo;