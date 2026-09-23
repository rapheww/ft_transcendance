import Header from "../Navbar/Header";

const Profil = () => {
  return (
    <div>
      <Header />
      <div className="border-2 border-amber-200 w-full min-h-[calc(100vh-72px)] flex flex-col justify-center items-center">
        <div id="profil-banner" className="border-2 border-red-500 h-50 w-[75%]">
          <p className="text-center">Banner</p>
        </div>
        <div id="profil-banner" className="border-2 border-blue-500 h-100 w-[75%]">
          <p className="text-center">Description</p>
        </div>
      </div>
    </div>
  );
};

export default Profil;
