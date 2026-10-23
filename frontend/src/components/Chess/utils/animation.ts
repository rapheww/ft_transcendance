import { useEffect, useLayoutEffect, type RefObject } from "react";
import { getTileElement, squareToPos } from "./utils";
import { getResult } from "./api";

export function moveAnimation(
  fen: string,
  lastMove: RefObject<{ from: string; to: string } | null>,
) {
  useLayoutEffect(() => {
    const m = lastMove.current; //tmp to get the lastmove
    if (!m) return;
    lastMove.current = null; //set the value to null

    const from = squareToPos(m.from); //getting the from pos
    const to = squareToPos(m.to); // getting the to pos
    const tf = getTileElement(from.x, from.y); //getting the element from
    const tt = getTileElement(to.x, to.y); // getting the element to
    if (!tf || !tt) return;

    const piece = tt.querySelector<HTMLElement>(".chess-piece");
    if(!piece) return;

    //setting the piece on top of the board to make the animation visible with white pieces
    piece.style.position = "relative";
    piece.style.zIndex = "40";

    const a = tf.getBoundingClientRect(); //getting the coordonates of the element from
    const b = tt.getBoundingClientRect(); //getting the coordonates of the element to
    const anim = piece.animate(
      //animation of the class chess-piece
      [
        { transform: `translate(${a.left - b.left}px, ${a.top - b.top}px)` },
        { transform: "none" },
      ] /*this is this animation translate from a to b*/,
      { duration: 200, easing: "ease-out" },
    );

    anim.onfinish = () => {
      piece.style.zIndex = "";
      piece.style.position = "";
    }
  }, [fen]);
}

export function gameOverScreen(gameId: number, token: string, setResult: React.Dispatch<React.SetStateAction<string>>, setOpen: React.Dispatch<React.SetStateAction<boolean>>, gameOver: boolean) {
  useEffect(() => {
    if (!gameOver) return;

    console.log("game over detected");
    async function receiveResult() {
      try {
        const game = await getResult(token, gameId);
        if(!game) return;
        console.log(game);
        if (game.status === "finished") {
          setResult(game.result);
          setOpen(true);
        }
      } catch {
        return;
      }
    }
    receiveResult();
  }, [gameOver]);
}
