import { useNavigate } from "react-router-dom";
import Header from "../Navbar/Header";

const Editor = () => {
    const navigate = useNavigate();
  return (
    <div className="h-screen w-full">
        <Header />
        <div className="min-h-[calc(100vh-72px)] w-full flex flex-col justify-center items-center gap-10">
            <input type="text" id="new-pfp" placeholder="paste pfp link here" className="input input-primary"/>
            <button className="btn btn-primary"
            onClick={() => {
                const inputElement = document.getElementById("new-pfp") as HTMLInputElement;
                const newPfp = inputElement.value;
                localStorage.setItem("pfp", newPfp);
                navigate("/profile");
            }}
            >save</button>
        </div>
    </div>
  );
};

export default Editor;