import { Sketch } from "@uiw/react-color";
import { X } from "lucide-react";
import { useEffect, useState } from "react";
import { createPortal } from "react-dom";

interface ColorProps {
  colorOnClose: () => void;
  colorOpen: boolean;
  Color: string
}

const ColorPicker = ({colorOpen , colorOnClose, Color} : ColorProps) => {
    const [hex, setHex] = useState<string>(Color);

    useEffect(() => {
    if (!colorOpen || !Color) return;
    const current = getComputedStyle(document.documentElement)
      .getPropertyValue(Color)
      .trim();
    setHex(current || "#ffffff");
  }, [colorOpen, Color]);

  return createPortal(
    <div
      className={`
            fixed inset-0
            flex justify-center items-center
            bg-black/30 backdrop-blur-sm
            transition-opacity duration-500 ease-out
            ${colorOpen ? "opacity-100" : "opacity-0 pointer-events-none"}
            `}
    >
      <div
        className={`
                    w-[90%] max-w-2xl
                    transition-all duration-500 ease-out
                    ${colorOpen ? "opacity-100 scale-100" : "opacity-0 scale-95"}
                    `}
      >
        <div className="w-full flex justify-center items-center">
          <div className="mt-10 flex flex-col text-white w-full">
            <div className="bg-mist-800 max-h-[90vh] flex justify-center items-center flex-col rounded-lg p-5 gap-5">
              <button
                onClick={colorOnClose}
                className="cursor-pointer place-self-end"
              >
                <X size={30} />
              </button>
              <h1 className="text-xl font-extrabold">Color Editor</h1>
              <div style={{ zoom: 1.3 }}>
                <Sketch 
                  color={hex} 
                  onChange={(color) => setHex(color.hex)} 
                />
              </div>
                
              <button 
                onClick={() => {
                    document.documentElement.style.setProperty(Color, hex);
                    colorOnClose()
                }}
                className="relative inline-flex items-center justify-center mt-3 px-6 py-3 overflow-hidden font-bold text-white hover:text-gray-700 rounded-md shadow-2xl group">
                <span className="absolute inset-0 w-full h-full transition duration-350 ease-in opacity-0 bg-linear-to-br from-white via-gray-200 to-white group-hover:opacity-100"></span>
                <span className="absolute top-0 left-0 w-full bg-linear-to-b from-white to-transparent opacity-5 h-1/3"></span>
                <span className="absolute bottom-0 left-0 w-full h-1/3 bg-linear-to-t from-white to-transparent opacity-5"></span>
                <span className="absolute bottom-0 left-0 w-4 h-full bg-linear-to-r from-white to-transparent opacity-5"></span>
                <span className="absolute bottom-0 right-0 w-4 h-full bg-linear-to-l from-white to-transparent opacity-5"></span>
                <span className="absolute inset-0 w-full h-full border border-white rounded-md opacity-10"></span>
                <span className="absolute w-0 h-0 transition-all duration-350 ease-out bg-white rounded-full group-hover:w-56 group-hover:h-56 opacity-5"></span>
                <span className="relative">Save</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>,
    document.body
  );
};

export default ColorPicker;