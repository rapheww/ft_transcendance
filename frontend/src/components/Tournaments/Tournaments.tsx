import Header from "../Navbar/Header";

const Tournaments = () => {
  return (
    <div className="w-full min-h-screen">
      <Header />
      <div className="min-h-[calc(100dvh-72px)] flex items-center justify-center px-2 md:px-4">
        <p className="text-5xl">Tournaments</p>
      </div>
    </div>
  );
};

export default Tournaments;