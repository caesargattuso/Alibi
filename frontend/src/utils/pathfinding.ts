interface Point {
  x: number;
  y: number;
}

class MinHeap<T extends { f: number }> {
  private heap: T[] = [];

  push(item: T) {
    this.heap.push(item);
    this._bubbleUp(this.heap.length - 1);
  }

  pop(): T | undefined {
    const top = this.heap[0];
    const last = this.heap.pop();
    if (this.heap.length > 0 && last) {
      this.heap[0] = last;
      this._sinkDown(0);
    }
    return top;
  }

  get size() {
    return this.heap.length;
  }

  private _bubbleUp(i: number) {
    while (i > 0) {
      const parent = Math.floor((i - 1) / 2);
      if (this.heap[parent].f <= this.heap[i].f) break;
      [this.heap[parent], this.heap[i]] = [this.heap[i], this.heap[parent]];
      i = parent;
    }
  }

  private _sinkDown(i: number) {
    const n = this.heap.length;
    while (true) {
      let smallest = i;
      const left = 2 * i + 1;
      const right = 2 * i + 2;
      if (left < n && this.heap[left].f < this.heap[smallest].f) smallest = left;
      if (right < n && this.heap[right].f < this.heap[smallest].f) smallest = right;
      if (smallest === i) break;
      [this.heap[smallest], this.heap[i]] = [this.heap[i], this.heap[smallest]];
      i = smallest;
    }
  }
}

const DIRS: Point[] = [
  { x: 0, y: -1 }, { x: 0, y: 1 }, { x: -1, y: 0 }, { x: 1, y: 0 },
  { x: -1, y: -1 }, { x: 1, y: -1 }, { x: -1, y: 1 }, { x: 1, y: 1 },
];

function heuristic(a: Point, b: Point): number {
  return Math.abs(a.x - b.x) + Math.abs(a.y - b.y);
}

function key(p: Point): string {
  return `${p.x},${p.y}`;
}

/**
 * Find path using A* algorithm on a grid.
 * @param start - Start position in pixel coordinates
 * @param end - End position in pixel coordinates
 * @param isWalkable - Function to check if a pixel coordinate is walkable
 * @param gridWidth - Canvas width in pixels
 * @param gridHeight - Canvas height in pixels
 * @param cellSize - Size of each grid cell in pixels (default 32)
 * @returns Array of points representing the path
 */
export function findPath(
  start: Point,
  end: Point,
  isWalkable: (x: number, y: number) => boolean,
  gridWidth: number,
  gridHeight: number,
  cellSize: number = 32,
): Point[] {
  // Convert pixel coordinates to grid coordinates
  const startGrid = { x: Math.floor(start.x / cellSize), y: Math.floor(start.y / cellSize) };
  const endGrid = { x: Math.floor(end.x / cellSize), y: Math.floor(end.y / cellSize) };

  // Calculate grid dimensions
  const cols = Math.ceil(gridWidth / cellSize);
  const rows = Math.ceil(gridHeight / cellSize);

  // Check if start and end are within bounds
  if (startGrid.x < 0 || startGrid.x >= cols || startGrid.y < 0 || startGrid.y >= rows) return [];
  if (endGrid.x < 0 || endGrid.x >= cols || endGrid.y < 0 || endGrid.y >= rows) return [];

  // Check if start and end are walkable (using center of cell)
  const startPixel = { x: startGrid.x * cellSize + cellSize / 2, y: startGrid.y * cellSize + cellSize / 2 };
  const endPixel = { x: endGrid.x * cellSize + cellSize / 2, y: endGrid.y * cellSize + cellSize / 2 };
  if (!isWalkable(startPixel.x, startPixel.y) || !isWalkable(endPixel.x, endPixel.y)) return [];

  interface Node {
    x: number;
    y: number;
    g: number;
    f: number;
    parent: Node | null;
  }

  const open = new MinHeap<Node>();
  const closed = new Set<string>();
  const gScores = new Map<string, number>();

  const startNode: Node = { x: startGrid.x, y: startGrid.y, g: 0, f: heuristic(startGrid, endGrid), parent: null };
  open.push(startNode);
  gScores.set(key(startGrid), 0);

  while (open.size > 0) {
    const current = open.pop()!;

    if (current.x === endGrid.x && current.y === endGrid.y) {
      // Reconstruct path and convert back to pixel coordinates
      const path: Point[] = [];
      let node: Node | null = current;
      while (node) {
        // Use center of cell for pixel coordinates
        path.unshift({
          x: node.x * cellSize + cellSize / 2,
          y: node.y * cellSize + cellSize / 2,
        });
        node = node.parent;
      }
      // Add the actual end point for precision
      path[path.length - 1] = { x: end.x, y: end.y };
      return path;
    }

    const ck = key(current);
    if (closed.has(ck)) continue;
    closed.add(ck);

    for (const dir of DIRS) {
      const nx = current.x + dir.x;
      const ny = current.y + dir.y;

      if (nx < 0 || ny < 0 || nx >= cols || ny >= rows) continue;

      // Check if the cell is walkable (using center of cell)
      const cellPixelX = nx * cellSize + cellSize / 2;
      const cellPixelY = ny * cellSize + cellSize / 2;
      if (!isWalkable(cellPixelX, cellPixelY)) continue;

      // Diagonal movement requires both adjacent cells to be walkable
      if (dir.x !== 0 && dir.y !== 0) {
        const adjPixelX1 = (current.x + dir.x) * cellSize + cellSize / 2;
        const adjPixelY1 = current.y * cellSize + cellSize / 2;
        const adjPixelX2 = current.x * cellSize + cellSize / 2;
        const adjPixelY2 = (current.y + dir.y) * cellSize + cellSize / 2;
        if (!isWalkable(adjPixelX1, adjPixelY1) || !isWalkable(adjPixelX2, adjPixelY2)) {
          continue;
        }
      }

      const nk = `${nx},${ny}`;
      if (closed.has(nk)) continue;

      const moveCost = dir.x !== 0 && dir.y !== 0 ? 1.414 : 1;
      const ng = current.g + moveCost;
      const prevG = gScores.get(nk);

      if (prevG === undefined || ng < prevG) {
        gScores.set(nk, ng);
        const h = heuristic({ x: nx, y: ny }, endGrid);
        open.push({ x: nx, y: ny, g: ng, f: ng + h, parent: current });
      }
    }
  }

  return [];
}
