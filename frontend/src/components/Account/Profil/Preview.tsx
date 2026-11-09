import { X } from "lucide-react";
import { createPortal } from "react-dom";
import ChessPreview from "../../Chess/preview/ChessPreview";

interface PreviewProps {
  previewOnClose: () => void;
  previewOpen: boolean;
  dark: string | null;
  light: string | null;
}

const Preview = ({
  previewOpen,
  previewOnClose,
  dark,
  light,
}: PreviewProps) => {
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
                    w-[90%] max-w-xl lg:max-w-2xl
                    transition-all duration-500 ease-out
                    ${previewOpen ? "opacity-100 scale-100" : "opacity-0 scale-95"}
                    `}
      >
        <div className="w-full flex justify-center items-center">
          <div className="mt-10 flex flex-col text-white w-full">
            <div className="bg-black/30 border border-white/30 backdrop:blur-lg max-h-[90vh] overflow-y-auto overscroll-contain flex items-center flex-col rounded-lg p-2 sm:p-3 lg:p-4 gap-2 sm:gap-3 lg:gap-5">
              <button
                onClick={previewOnClose}
                className="cursor-pointer place-self-end rounded-lg hover:bg-gray-400/30"
              >
                <X size={30} />
              </button>
              <div className="w-[min(100%,70vh)]">
                <ChessPreview dark={dark} light={light} />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>,
    document.body,
  );
};

export default Preview;
