import { useEffect, useRef, useCallback } from "react";
import type { Interactable, MapData } from "../../services/scenes";

interface SceneMapProps {
  mapData: MapData | null;
  interactables: Interactable[];
  onInteract?: (interactable: Interactable) => void;
  onMove?: (x: number, y: number) => void;
}

export function SceneMap({ mapData, interactables, onInteract, onMove }: SceneMapProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || !mapData) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    canvas.width = mapData.width;
    canvas.height = mapData.height;

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
  }, [mapData, interactables]);

  useEffect(() => {
    draw();
  }, [draw]);

  const handleClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas || !mapData) return;

    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const x = (e.clientX - rect.left) * scaleX;
    const y = (e.clientY - rect.top) * scaleY;

    // Check if clicked on an interactable
    for (const point of interactables) {
      const [px, py] = point.position;
      const dist = Math.sqrt((x - px) ** 2 + (y - py) ** 2);
      if (dist < 20) {
        onInteract?.(point);
        return;
      }
    }

    onMove?.(Math.round(x), Math.round(y));
  };

  return (
    <canvas
      ref={canvasRef}
      onClick={handleClick}
      className="w-full cursor-pointer"
      style={{ maxHeight: "50vh", objectFit: "contain" }}
    />
  );
}
