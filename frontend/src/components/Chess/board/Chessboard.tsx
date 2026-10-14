  import type React from "react";
  import Tile from "./Tile";
  import { useEffect, useRef, useState } from "react";
  import {
    getColor,
    getTileElement,
    horizontalAxis,
    names,
    resetPiece,
    squareToPos,
    verticalAxis,
    type LastPick,
    type Movements,
    type PromoParams,
  } from "../utils/utils";
  import { Chess, KING, type Square } from "chess.js";
  import GameOver from "../popup/GameOver";
  import { useAuth } from "../../AuthProvider";
  import Promotion from "../popup/Promotion";
  import type { Moves } from "../Chess";
  import { postMove } from "../utils/api";
  import { gameOverScreen, moveAnimation } from "../utils/animation";


  const CAPTURE_IMG = "https://media1.tenor.com/m/Rd0jrWH5JjgAAAAC/cat-scuba.gif";

  export interface ChessboardProps {
    setMoves: React.Dispatch<React.SetStateAction<Moves[]>>;
    setBBonus: React.Dispatch<React.SetStateAction<boolean>>;
    setWBonus: React.Dispatch<React.SetStateAction<boolean>>;
    gameId: number;
    fenInit: string;
    gameOver: boolean;
    result: string;
    setGameOver: React.Dispatch<React.SetStateAction<boolean>>;
    setResult: React.Dispatch<React.SetStateAction<string>>;
  }

  export default function Chessboard({
    setMoves,
    setBBonus,
    setWBonus,
    setGameOver,
    setResult,
    gameId,
    fenInit,
    gameOver,
    result,
  }: ChessboardProps) {
    const chessRef = useRef(new Chess(fenInit));
    const checkedKing: string | null = chessRef.current.isCheck()
      ? (chessRef.current.findPiece({
          type: KING,
          color: chessRef.current.turn(),
        })[0] ?? null)
      : null;

    const { token, profil } = useAuth();

    const [activePiece, setActivePiece] = useState<HTMLElement | null>(null);
    const [gridX, setGridX] = useState(0);
    const [gridY, setGridY] = useState(0);
    const [fen, setFen] = useState<string>(chessRef.current.fen());
    const [tileColor, setTileColor] = useState<Movements[]>([]);
    const [lastPick, setLastPick] = useState<LastPick | null>(null);
    const [moveTile, setMoveTile] = useState<HTMLElement[]>([]);
    const [currentFen, setCurrentFen] = useState<string | null>(null);
    const [open, setOpen] = useState<boolean>(false);
    const [promoOpen, setPromoOpen] = useState<boolean>(false);
    const [pendingPromo, setPendinPromo] = useState<{
      from: Square;
      to: Square;
      color: "b" | "w";
    } | null>(null);
    const [params, setParams] = useState<PromoParams | null>(null);
    const [captured, setCaptured] = useState<string | null>(null);

    const lastMove = useRef<{ from: string; to: string } | null>(null);
    let newPos: string = "";
    let oldPos: string = "";
    let possible: string[] | null = null;

    //moving animation
    moveAnimation(fen, lastMove);

    //useEffect pour charger le fen quand un mouv est clique
    useEffect(() => {
      if (!fenInit) return;
      if (!currentFen) setCurrentFen(chessRef.current.fen());
      chessRef.current.load(fenInit);
      setFen(fenInit);
    }, [fenInit]);

    //gameOver
    gameOverScreen(gameId, token, setResult, setOpen, gameOver);

    function removeDot() {
      for (let i = 0; i < moveTile.length; i++) {
        if (moveTile[i]) {
          moveTile[i].style.backgroundImage = "";
          moveTile[i].style.cursor = "";
          moveTile[i].style.boxShadow = "";
        }
      }
      setMoveTile([]);
    }

    function cancelMove() {
      if (activePiece) {
        const back = activePiece.parentNode as HTMLElement;
        resetPiece(activePiece);
        setActivePiece(null);
        setTileColor((prev) => {
          const entry = prev.find((m) => m.tile === back);
          if (entry) {
            entry.tile.style.backgroundColor = entry.bg;
            return prev.filter((m) => m.tile !== back);
          }
          return prev;
        });
      }
    }

    //show dot or selected tile if ennemi piece
    function possibleMoves(possible: string[]) {
      const currentTurn = chessRef.current.turn();

      for (let i = 0; i < possible.length; i++) {
        const { x, y } = squareToPos(possible[i]);
        const tile = getTileElement(x, y);
        const possiblePiece = chessRef.current.get(possible[i] as Square);
        if (tile) {
          if(possiblePiece && possiblePiece.color != currentTurn){
              tile.style.backgroundColor = tile.dataset.dark === "true" ? profil.board_dark_color :  profil.board_light_color
              tile.style.backgroundImage = `radial-gradient(transparent 0%, transparent 79%, rgba(80, 138, 82, 1) 80%)`;
          }
          else
            tile.style.backgroundImage = "radial-gradient(circle, rgba(0,0,0,0.2) 20%, transparent 21%)";
          tile.style.cursor = "pointer";
          setMoveTile((prev) => {
            let newMoveTile = [...prev];
            newMoveTile.push(tile);
            return newMoveTile;
          });
        }
      }
    }

    async function sendMove(move: string) {
      try {
        const turn = chessRef.current.turn();
        const bob =
          "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyIiwiZXhwIjoxNzkyMDAxNzAwLCJ0eXBlIjoiYWNjZXNzIn0.WBazlgKX8F-WZo5SOmSFmviYrCyKuJv0jlRAFmew4Qs";
        const infos = await postMove(move, gameId, turn === "b" ? bob : token);
        if (!infos.ok) return false;
        setFen(infos.current_fen);
        chessRef.current.load(infos.current_fen);
        if (infos.status === "finished") {
          setGameOver(true);
          setResult(infos.result);
        }
        return true;
      } catch {
        console.log("error makeMove");
        return false;
      }
    }

    function afterMove(played: string) {
      setMoves((prev) => {
        let tmp = [...prev];
        tmp.push({ move: played, fen: chessRef.current.fen() });
        return tmp;
      });
      setLastPick(null);
      setFen(chessRef.current.fen());
      setPendinPromo(null);
      setParams(null);

      const turn = chessRef.current.turn();
      setBBonus(turn === "w");
      setWBonus(turn === "b");
      if (chessRef.current.isGameOver()) {
        setGameOver(true);
        setOpen(true);
      }
    }

    function getCoords(e: React.MouseEvent) {
      const rect = document.getElementById("chessboard")!.getBoundingClientRect();
      const tileSize = rect.width / 8;
      return {
        rect,
        tileSize,
        x: Math.floor((e.clientX - rect.left) / tileSize),
        y: 7 - Math.floor((e.clientY - rect.top) / tileSize),
      };
    }

    function setBgColor(
      target: { x: number; y: number } | undefined,
      x: number,
      y: number,
      chessboard: HTMLElement,
      active: HTMLElement | null,
    ) {
      lastMove.current = target ? { from: `${oldPos}`, to: `${newPos}` } : null;
      if (x !== gridX || y !== gridY) {
        const originTile = tileColor.find(
          (m) => m.tile === (active!.parentNode as HTMLElement),
        );
        const dest = chessboard.children[(7 - y) * 8 + x] as HTMLElement;
        const destExisting = tileColor.find((m) => m.tile === dest);
        const destColor = destExisting ? destExisting.bg : getColor(dest);

        tileColor.forEach((m) => {
          if (m.tile !== originTile?.tile && m.tile !== dest) {
            m.tile.style.backgroundColor = m.bg;
          }
        });

        if (originTile && destColor) {
          if (originTile && destColor) {
            originTile.tile.style.backgroundColor =
              originTile.tile.dataset.dark === "true" ? "#738a38" : "#97b54a";
            dest.style.backgroundColor =
              dest.dataset.dark === "true" ? "#738a38" : "#97b54a";
            setTileColor([originTile, { bg: destColor, tile: dest }]);
          }
        }
      }
    }

    function setStyle(element: HTMLElement, e: React.MouseEvent) {
      const { rect, tileSize } = getCoords(e);
      Object.assign(element.style, {
        width: `${tileSize}px`,
        height: `${tileSize}px`,
        position: "absolute",
        left: `${e.clientX - rect.left - tileSize / 2}px`,
        top: `${e.clientY - rect.top - tileSize / 2}px`,
        zIndex: "50",
      });
    }

    function grabPiece(e: React.MouseEvent) {
      if (gameOver) return;
      //set current fen visible
      if (currentFen) {
        chessRef.current.load(currentFen);
        setCurrentFen("");
      }
      const chessboard = document.getElementById("chessboard");
      if (!chessboard) return;
      
      //drop if clicked
      const { x, y } = getCoords(e);
      const clicked = getTileElement(x, y);
      if (clicked && moveTile.includes(clicked)) {
        const selected = getTileElement(gridX, gridY)?.querySelector(
          ".chess-piece",
        ) as HTMLElement | null;
        if (selected) {
          dropPiece(null, { x, y }, selected);
          return;
        }
      }

      //arrow
      if (e.button === 2) {
        console.log("arrow");
        //arrow code
        return;
      }

      const element = e.target as HTMLElement;
      if (!element.classList.contains("chess-piece")) return;
      let back = element.parentNode as HTMLElement;
      if (!back) return;

      setGridX(x);
      setGridY(y);

      setStyle(element, e);
      setActivePiece(element);
      removeDot();
      if (!lastPick) {
        setLastPick({ piece: element, bg: back.style.backgroundColor });
      } else {
        if (element != lastPick.piece) {
          const old = lastPick.piece.parentNode as HTMLElement;
          if (old) {
            old.style.backgroundColor = lastPick.bg;
            setLastPick({ piece: element, bg: back.style.backgroundColor });
          }
        }
      }

      // Si la case est déjà suivie (ex: faisait partie du dernier mouvement), on réutilise sa vraie couleur
      const existing = tileColor.find((m) => m.tile === back);
      const tmpColor = existing ? existing.bg : getColor(back);
      if (!tmpColor) return;

      setTileColor((prev) =>
        existing ? prev : [...prev, { bg: tmpColor, tile: back }],
      );
      back.style.backgroundColor = "var(--select-tile)";

      const square = `${horizontalAxis[x]}${verticalAxis[y]}` as Square;
      possible = chessRef.current
        .moves({ square: square, verbose: true })
        .map((m) => m.to);
      possibleMoves(possible);
    }

    function movePiece(e: React.MouseEvent) {
      if (activePiece && activePiece.classList.contains("chess-piece")) {
        const chessboard = document.getElementById("chessboard");
        if (!chessboard) return;
        setStyle(activePiece, e);
      }
    }

    //PROMO
    async function promotion(choice: "q" | "r" | "b" | "n") {
      console.log("calling");
      if (!pendingPromo || !params) return;

      const played = chessRef.current.move({
        from: pendingPromo.from,
        to: pendingPromo.to,
        promotion: choice,
      }).san;

      await sendMove(pendingPromo?.from + pendingPromo?.to + choice);

      setBgColor(
        params.target,
        params.x,
        params.y,
        params.chessboard,
        params.active,
      );
      afterMove(played);
    }

    async function dropPiece(
      e: React.MouseEvent | null,
      target?: { x: number; y: number },
      piece?: HTMLElement,
    ) {
      const active = piece ?? activePiece;
      if (gameOver) return;
      if (active && (e || target)) {
        let played: string = "";
        const chessboard = document.getElementById("chessboard");
        if (!chessboard) return;
        const { x, y } = target ?? getCoords(e!);

        if (x < 0 || x > 7 || y < 0 || y > 7) {
          cancelMove();
          return;
        }

        //TOUTE LES MODIFS LA
        //verif du mouv
        newPos = `${horizontalAxis[x]}${verticalAxis[y]}`;
        oldPos = `${horizontalAxis[gridX]}${verticalAxis[gridY]}`;
        try {
          if (newPos == oldPos) throw "invalid";

          const piece = chessRef.current.get(oldPos as Square);

          //promo
          if (piece?.type === "p" && (newPos[1] === "8" || newPos[1] === "1")) {
            setPendinPromo({
              from: oldPos as Square,
              to: newPos as Square,
              color: piece?.color,
            });

            setParams({
              target: target,
              x: x,
              y: y,
              chessboard: chessboard,
              active: active,
            });

            setPromoOpen(true);
            resetPiece(active);
            removeDot();
            setActivePiece(null);
            return;
          }

          //normal move
          else {
            const moveNow =chessRef.current.move({
              from: `${oldPos}`,
              to: `${newPos}`,
            });
            played = moveNow.san;
            sendMove(oldPos + newPos);
            if(moveNow.captured) setCaptured(moveNow.to);
            else setCaptured(null);
          }
        } catch (error) {
          resetPiece(active);
          setActivePiece(null);
          return;
        }

        setBgColor(target, x, y, chessboard, active);
        resetPiece(active);
        removeDot();
        setActivePiece(null);
        //show movements
        afterMove(played);
      }
    }

    //render du board
    const grid = chessRef.current.board();

    let board = [];
    for (let j = 7; j >= 0; j--) {
      for (let i = 0; i < 8; i++) {
        const p = grid[7 - j][i];
        const image = p
          ? `/src/assets/${names[p.type]}_${p.color}.png`
          : undefined;
        const square = `${horizontalAxis[i]}${verticalAxis[j]}`;
        board.push(
          <Tile
            key={`${j}, ${i}`}
            image={image}
            number={i + j + 2}
            gameOver={gameOver}
            inCheck={square === checkedKing}
            captured={square === captured ? CAPTURE_IMG : null}
          />,
        );
      }
    }
    return (
      <div
        onMouseMove={(e) => movePiece(e)}
        onMouseDown={(e) => grabPiece(e)}
        onMouseUp={(e) => dropPiece(e)}
        onMouseLeave={cancelMove}
        onContextMenu={(e) => e.preventDefault()}
        id="chessboard"
        className={`relative bg-black grid grid-cols-8 grid-rows-8 w-[min(100cqw,100cqh)] h-[min(100cqw,100cqh)] aspect-square select-none rounded-xl overflow-hidden border-2 border-black shadow-[0_0_30px_#000000]`}
        style={{
          gridTemplateColumns: "repeat(8, 1fr)",
          gridTemplateRows: "repeat(8, 1fr)",
        }}
      >
        {board}
        <GameOver open={open} onClose={() => setOpen(false)} result={result} />
        <Promotion
          open={promoOpen}
          onClose={() => setPromoOpen(false)}
          setChoice={promotion}
          color={pendingPromo?.color as string}
        />
      </div>
    );
  }
