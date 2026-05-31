import { useEffect, useRef, useCallback, useState } from "react";
import type { Interactable, MapData } from "../../services/scenes";
import { findPath } from "../../utils/pathfinding";

interface Point {
  x: number;
  y: number;
}

interface SceneMapProps {
  mapData: MapData | null;
  interactables: Interactable[];
  playerPosition: Point;
  onPlayerMove?: (x: number, y: number) => void;
  onInteract?: (interactable: Interactable) => void;
  pathColor?: string;
}

export function SceneMap({
  mapData,
  interactables,
  playerPosition,
  onPlayerMove,
  onInteract,
  pathColor = "#FF6B9D",
}: SceneMapProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [currentPath, setCurrentPath] = useState<Point[]>([]);
  const [isMoving, setIsMoving] = useState(false);
  const [playerPosState, setPlayerPosState] = useState<Point>(playerPosition);
  const animationRef = useRef<number>(0);
  const playerPosRef = useRef<Point>(playerPosition);

  // Update player position ref when prop changes
  useEffect(() => {
    playerPosRef.current = playerPosition;
    setPlayerPosState(playerPosition);
  }, [playerPosition]);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || !mapData) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Only set canvas dimensions if they changed
    if (canvas.width !== mapData.width || canvas.height !== mapData.height) {
      canvas.width = mapData.width;
      canvas.height = mapData.height;
    }

    // Background
    ctx.fillStyle = "#1a1a2e";
    ctx.fillRect(0, 0, mapData.width, mapData.height);

    // Walkable areas
    ctx.fillStyle = "rgba(139, 69, 19, 0.2)";
    for (const area of mapData.walkable_areas) {
      ctx.beginPath();
      const polygon = area.polygon;
      if (polygon.length > 0) {
        ctx.moveTo(polygon[0][0], polygon[0][1]);
        for (let i = 1; i < polygon.length; i++) {
          ctx.lineTo(polygon[i][0], polygon[i][1]);
        }
        ctx.closePath();
        ctx.fill();
      }
    }

    // Obstacles
    ctx.fillStyle = "rgba(100, 100, 100, 0.6)";
    for (const obs of mapData.obstacles) {
      ctx.beginPath();
      const polygon = obs.polygon;
      if (polygon.length > 0) {
        ctx.moveTo(polygon[0][0], polygon[0][1]);
        for (let i = 1; i < polygon.length; i++) {
          ctx.lineTo(polygon[i][0], polygon[i][1]);
        }
        ctx.closePath();
        ctx.fill();
      }
    }

    // Path
    if (currentPath.length > 1) {
      ctx.beginPath();
      ctx.moveTo(currentPath[0].x, currentPath[0].y);
      for (let i = 1; i < currentPath.length; i++) {
        ctx.lineTo(currentPath[i].x, currentPath[i].y);
      }
      ctx.strokeStyle = pathColor;
      ctx.lineWidth = 3;
      ctx.setLineDash([10, 5]);
      ctx.stroke();
      ctx.setLineDash([]);
    }

    // Interactable points
    for (const point of interactables) {
      const [x, y] = point.position;
      const color = point.type === "npc" ? "#74b9ff" : point.type === "exit" ? "#55efc4" : "#ffeaa7";
      ctx.beginPath();
      ctx.arc(x, y, 15, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.fill();
      ctx.strokeStyle = "#fff";
      ctx.lineWidth = 2;
      ctx.stroke();

      ctx.fillStyle = "#fff";
      ctx.font = "12px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(point.name, x, y - 20);
    }

    // Spawn points
    for (const sp of mapData.spawn_points) {
      const [x, y] = sp.position;
      ctx.beginPath();
      ctx.arc(x, y, 8, 0, Math.PI * 2);
      ctx.fillStyle = "#e17055";
      ctx.fill();
    }

    // Player character
    const player = playerPosState;
    ctx.beginPath();
    ctx.arc(player.x, player.y, 12, 0, Math.PI * 2);
    ctx.fillStyle = "#FF6B9D";
    ctx.fill();
    ctx.strokeStyle = "#fff";
    ctx.lineWidth = 3;
    ctx.stroke();

    // Player direction indicator
    ctx.beginPath();
    ctx.moveTo(player.x, player.y - 12);
    ctx.lineTo(player.x - 6, player.y + 6);
    ctx.lineTo(player.x + 6, player.y + 6);
    ctx.closePath();
    ctx.fillStyle = "rgba(255, 255, 255, 0.5)";
    ctx.fill();
  }, [mapData, interactables, currentPath, pathColor, playerPosState]);

  useEffect(() => {
    draw();
  }, [draw]);

  // Animation loop for player movement
  useEffect(() => {
    if (!isMoving || currentPath.length < 2) return;

    let pathIndex = 0;
    const speed = 200; // pixels per second
    let lastTime = performance.now();

    const animate = (time: number) => {
      const deltaTime = (time - lastTime) / 1000;
      lastTime = time;

      if (pathIndex >= currentPath.length - 1) {
        setIsMoving(false);
        setCurrentPath([]);
        return;
      }

      const target = currentPath[pathIndex + 1];
      const current = playerPosRef.current;
      const dx = target.x - current.x;
      const dy = target.y - current.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      const moveDist = speed * deltaTime;

      if (moveDist >= dist) {
        playerPosRef.current = { ...target };
        pathIndex++;
        if (pathIndex >= currentPath.length - 1) {
          setIsMoving(false);
          setCurrentPath([]);
          onPlayerMove?.(target.x, target.y);
          return;
        }
      } else {
        const ratio = moveDist / dist;
        playerPosRef.current = {
          x: current.x + dx * ratio,
          y: current.y + dy * ratio,
        };
      }

      setPlayerPosState({ ...playerPosRef.current });
      animationRef.current = requestAnimationFrame(animate);
    };

    animationRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isMoving, currentPath, draw, onPlayerMove]);

  const handleClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (isMoving) return;

    const canvas = canvasRef.current;
    if (!canvas || !mapData) return;

    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const x = Math.round((e.clientX - rect.left) * scaleX);
    const y = Math.round((e.clientY - rect.top) * scaleY);

    // Check if clicked on an interactable
    for (const point of interactables) {
      const [px, py] = point.position;
      const dist = Math.sqrt((x - px) ** 2 + (y - py) ** 2);
      if (dist < 30) {
        onInteract?.(point);
        return;
      }
    }

    // Calculate path using A*
    const start = { x: Math.round(playerPosRef.current.x), y: Math.round(playerPosRef.current.y) };
    const end = { x, y };

    // Simple walkability check - check if point is in any walkable area
    const isWalkable = (px: number, py: number) => {
      // Check if in any walkable area
      for (const area of mapData.walkable_areas) {
        const polygon = area.polygon;
        if (pointInPolygon(px, py, polygon)) return true;
      }
      return false;
    };

    const path = findPath(start, end, isWalkable, mapData.width, mapData.height);
    if (path.length > 1) {
      setCurrentPath(path);
      setIsMoving(true);
    }
  };

  return (
    <canvas
      ref={canvasRef}
      onClick={handleClick}
      className="w-full cursor-pointer"
      style={{ maxHeight: "60vh", objectFit: "contain" }}
    />
  );
}

// Helper function: point in polygon (ray casting)
function pointInPolygon(x: number, y: number, polygon: number[][]): boolean {
  let inside = false;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const xi = polygon[i][0], yi = polygon[i][1];
    const xj = polygon[j][0], yj = polygon[j][1];
    if (((yi > y) !== (yj > y)) && (x < (xj - xi) * (y - yi) / (yj - yi) + xi)) {
      inside = !inside;
    }
  }
  return inside;
}
