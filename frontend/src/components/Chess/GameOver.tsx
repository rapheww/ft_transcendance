import { X } from "lucide-react";

interface Props {
  onClose: () => void;
  open: boolean;
  result: string,
}

const GameOver = ({open, onClose, result}: Props) => {
  return (
    <div
      className={`
            fixed inset-0
            flex justify-center items-center
            transition-opacity duration-500 ease-out
            ${open ? "opacity-100" : "opacity-0 pointer-events-none"}
            `}
    >
      <div
        className={`
                    w-[90%] max-w-2xl
                    transition-all duration-500 ease-out
                    ${open ? "opacity-100 scale-100" : "opacity-0 scale-95"}
                    `}
      >
        <div className="w-full flex justify-center items-center">
          <div className="mt-10 flex flex-col text-white w-full">
            <div className="bg-mist-800 max-h-[90vh] flex justify-center items-center flex-col rounded-lg p-5 ">
              <button
                onClick={onClose}
                className="cursor-pointer place-self-end"
              >
                <X size={30} />
              </button>
              <h1 className="text-2xl font-extrabold">{result}</h1>
              
              </div>
            </div>
          </div>
        </div>
      </div>
  );
};

export default GameOver;