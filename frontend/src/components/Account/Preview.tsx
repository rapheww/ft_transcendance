import { X } from "lucide-react";
import { createPortal } from "react-dom";
import ChessPreview from "../Chess/ChessPreview";

interface PreviewProps {
  previewOnClose: () => void;
  previewOpen: boolean;
}

const Preview = ({ previewOpen, previewOnClose }: PreviewProps) => {
  return createPortal(
    <div
      className={`
            fixed inset-0
            flex justify-center items-center
            bg-black/30 backdrop-blur-sm
            transition-opacity duration-500 ease-out
            ${previewOpen ? "opacity-100" : "opacity-0 pointer-events-none"}
            `}
    >
      <div
        className={`
                    w-[90%] max-w-2xl
                    transition-all duration-500 ease-out
                    ${previewOpen ? "opacity-100 scale-100" : "opacity-0 scale-95"}
                    `}
      >
        <div className="w-full flex justify-center items-center">
          <div className="mt-10 flex flex-col text-white w-full">
            <div className="bg-mist-800 max-h-[90vh] flex justify-center items-center flex-col rounded-lg p-5 gap-5">
              <button
                onClick={previewOnClose}
                className="cursor-pointer place-self-end"
              >
                <X size={30} />
              </button>
              <h1 className="text-xl font-extrabold">ChessBoard Preview</h1>
              <ChessPreview />
            </div>
          </div>
        </div>
      </div>
    </div>,
    document.body,
  );
};

export default Preview;
