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

export function findPath(
  start: Point,
  end: Point,
  isWalkable: (x: number, y: number) => boolean,
  gridWidth: number,
  gridHeight: number,
): Point[] {
  if (!isWalkable(start.x, start.y) || !isWalkable(end.x, end.y)) return [];

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

  const startNode: Node = { x: start.x, y: start.y, g: 0, f: heuristic(start, end), parent: null };
  open.push(startNode);
  gScores.set(key(start), 0);

  while (open.size > 0) {
    const current = open.pop()!;

    if (current.x === end.x && current.y === end.y) {
      const path: Point[] = [];
      let node: Node | null = current;
      while (node) {
        path.unshift({ x: node.x, y: node.y });
        node = node.parent;
      }
      return path;
    }

    const ck = key(current);
    if (closed.has(ck)) continue;
    closed.add(ck);

    for (const dir of DIRS) {
      const nx = current.x + dir.x;
      const ny = current.y + dir.y;

      if (nx < 0 || ny < 0 || nx >= gridWidth || ny >= gridHeight) continue;
      if (!isWalkable(nx, ny)) continue;

      const nk = `${nx},${ny}`;
      if (closed.has(nk)) continue;

      // Diagonal movement requires both adjacent cells to be walkable
      if (dir.x !== 0 && dir.y !== 0) {
        if (!isWalkable(current.x + dir.x, current.y) || !isWalkable(current.x, current.y + dir.y)) {
          continue;
        }
      }

      const moveCost = dir.x !== 0 && dir.y !== 0 ? 1.414 : 1;
      const ng = current.g + moveCost;
      const prevG = gScores.get(nk);

      if (prevG === undefined || ng < prevG) {
        gScores.set(nk, ng);
        const h = heuristic({ x: nx, y: ny }, end);
        open.push({ x: nx, y: ny, g: ng, f: ng + h, parent: current });
      }
    }
  }

  return [];
}
