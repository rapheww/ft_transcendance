import Logo from "./Logo";
import Navbar from "./Navbar";

const Header = () => {
    return (
        <header className="sticky shrink-0 top-0 mx-auto flex h-18 w-full items-center justify-between bg-[rgb(29, 28, 28)] px-8">
            <Logo />
            <Navbar />
        </header>
    );
};

export default Header;
