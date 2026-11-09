import Logo from "./Logo";
import Navbar from "./Navbar";

const Header = () => {
    return (
        <header className="shrink-0 top-0 mx-auto flex flex-wrap min-h-14 w-full items-center justify-between px-8">
            <Logo />
            <Navbar />
        </header>
    );
};

export default Header;
