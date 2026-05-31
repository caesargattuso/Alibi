import { useEffect, useRef } from "react";
import Phaser from "phaser";
import type { MapData, Interactable } from "../../services/scenes";

interface Point {
  x: number;
  y: number;
}

interface PhaserGameCanvasProps {
  mapData: MapData | null;
  interactables: Interactable[];
  playerPosition: Point;
  onPlayerMove: (x: number, y: number) => void;
  onInteract: (interactable: Interactable) => void;
}

// Constants for the game world
const WORLD_WIDTH = 1920;
const WORLD_HEIGHT = 1080;
const GROUND_Y = 800;
const PLAYER_SPEED = 400;
const PROXIMITY_THRESHOLD = 120;

// Interactable data with Phaser game objects
interface InteractableData {
  item: Interactable;
  zone: Phaser.GameObjects.Zone;
  icon: Phaser.GameObjects.Text;
  label: Phaser.GameObjects.Text;
  glow: Phaser.GameObjects.Graphics;
}

class GameScene extends Phaser.Scene {
  private player!: Phaser.GameObjects.Sprite;
  private playerShadow!: Phaser.GameObjects.Ellipse;
  private cursors!: Phaser.Types.Input.Keyboard.CursorKeys;
  private groundGraphics!: Phaser.GameObjects.Graphics;
  private onPlayerMoveCallback: ((x: number, y: number) => void) | null = null;
  private onInteractCallback: ((interactable: Interactable) => void) | null = null;
  private interactablesData: InteractableData[] = [];
  private playerTargetX: number | null = null;

  constructor() {
    super({ key: "GameScene" });
  }

  init(data: {
    mapData: MapData;
    interactables: Interactable[];
    playerPosition: Point;
    onPlayerMove: (x: number, y: number) => void;
    onInteract: (interactable: Interactable) => void;
  }) {
    this.onPlayerMoveCallback = data.onPlayerMove;
    this.onInteractCallback = data.onInteract;
    this.interactablesData = [];
    this.playerTargetX = null;
  }

  preload() {
    // Load player portrait - use a colored circle as fallback if image not available
    this.load.image("player", "/uploads/characters/player_portrait.png");
    this.load.image("bg-lobby", "/uploads/scenes/lobby_bg.png");
  }

  create() {
    // Create a dark background gradient
    const bg = this.add.graphics();
    bg.fillGradientStyle(0x1a1a2e, 0x1a1a2e, 0x16213e, 0x16213e, 1);
    bg.fillRect(0, 0, WORLD_WIDTH, WORLD_HEIGHT);

    // Try to load background image, fallback to gradient
    const bgImage = this.add.image(WORLD_WIDTH / 2, WORLD_HEIGHT / 2, "bg-lobby");
    bgImage.setDisplaySize(WORLD_WIDTH, WORLD_HEIGHT);
    bgImage.setAlpha(0.6);

    // Draw ground/platform
    this.groundGraphics = this.add.graphics();
    this.drawGround();

    // Create player shadow (ellipse under player)
    this.playerShadow = this.add.ellipse(100, GROUND_Y + 10, 40, 10, 0x000000, 0.3);


    // Create player sprite - use a colored circle as fallback
    const playerTexture = this.textures.exists("player") ? "player" : undefined;
    if (playerTexture) {
      this.player = this.add.sprite(100, GROUND_Y - 60, "player");
      this.player.setScale(0.4);
    } else {
      // Create a placeholder player (pink-haired loli representation)
      this.player = this.add.sprite(100, GROUND_Y - 60, "__DEFAULT");
      const g = this.add.graphics();
      g.fillStyle(0xFF69B4, 1);
      g.fillCircle(16, 16, 16);
      g.generateTexture("player_placeholder", 32, 32);
      this.player.setTexture("player_placeholder");
      this.player.setScale(1.5);
    }

    // Setup camera
    this.cameras.main.setBounds(0, 0, WORLD_WIDTH, WORLD_HEIGHT);
    this.cameras.main.startFollow(this.player, true, 0.08, 0.08);
    this.cameras.main.setZoom(0.8);

    // Setup keyboard
    this.cursors = this.input.keyboard!.createCursorKeys();

    // Create interactable hotspots
    this.createHotspots();

    // Setup click-to-move
    this.input.on("pointerdown", (pointer: Phaser.Input.Pointer) => {
      this.handleGroundClick(pointer.worldX, pointer.worldY);
    });

    // Ambient particles for atmosphere
    this.createAmbientParticles();
  }

  drawGround() {
    this.groundGraphics.clear();

    // Main ground
    this.groundGraphics.fillStyle(0x2d3436, 0.8);
    this.groundGraphics.fillRect(0, GROUND_Y, WORLD_WIDTH, WORLD_HEIGHT - GROUND_Y);

    // Ground line
    this.groundGraphics.lineStyle(2, 0x636e72, 0.5);
    this.groundGraphics.lineBetween(0, GROUND_Y, WORLD_WIDTH, GROUND_Y);

    // Decorative ground elements
    for (let x = 0; x < WORLD_WIDTH; x += 200) {
      this.groundGraphics.fillStyle(0x3d4446, 0.3);
      this.groundGraphics.fillRect(x + 50, GROUND_Y + 20, 100, 5);
    }
  }

  createAmbientParticles() {
    // Simple floating dust particles - stored to avoid unused variable warning
    const particles = this.add.particles(0, 0, "__DEFAULT", {
      x: { min: 0, max: WORLD_WIDTH },
      y: { min: 0, max: GROUND_Y },
      quantity: 20,
      frequency: 2000,
      lifespan: 4000,
      scale: { start: 0.02, end: 0 },
      alpha: { start: 0.3, end: 0 },
      tint: 0xffffff,
      blendMode: Phaser.BlendModes.ADD,
    });
    // Keep reference to prevent garbage collection
    particles.setName("ambient_dust");
  }

  createHotspots() {
    this.interactablesData.forEach((data) => {
      const item = data.item;
      const [x, y] = item.position;

      // Create interaction zone
      const zone = this.add.zone(x, y, 80, 80).setInteractive({ useHandCursor: true });

      // Icon based on type
      const iconText = this.getIconForType(item.type);
      const icon = this.add.text(x, y - 30, iconText, {
        fontSize: "28px",
        align: "center",
      }).setOrigin(0.5);

      // Label
      const label = this.add.text(x, y + 20, item.name, {
        fontSize: "12px",
        color: "#ffffff",
        backgroundColor: "#00000080",
        padding: { x: 6, y: 2 },
      }).setOrigin(0.5);

      // Glow effect (initially hidden)
      const glow = this.add.graphics();
      glow.setVisible(false);

      // Store references
      data.zone = zone;
      data.icon = icon;
      data.label = label;
      data.glow = glow;

      // Events
      zone.on("pointerover", () => {
        this.highlightInteractable(data, true);
        document.body.style.cursor = "pointer";
      });

      zone.on("pointerout", () => {
        this.highlightInteractable(data, false);
        document.body.style.cursor = "default";
      });

      zone.on("pointerdown", () => {
        this.onInteractCallback?.(item);
      });
    });
  }

  getIconForType(type: string): string {
    const icons: Record<string, string> = {
      npc: "👤",
      object: "📦",
      exit: "🚪",
      event: "❗",
      item: "💎",
    };
    return icons[type] || "❓";
  }

  highlightInteractable(data: InteractableData, active: boolean) {
    data.glow.clear();
    if (active) {
      const [x, y] = data.item.position;
      data.glow.lineStyle(2, 0xFF6B9D, 0.8);
      data.glow.strokeCircle(x, y, 40);
      data.glow.fillStyle(0xFF6B9D, 0.1);
      data.glow.fillCircle(x, y, 40);
    }
    data.glow.setVisible(active);
  }

  handleGroundClick(x: number, y: number) {
    // Only move if clicked below a certain threshold (ground area)
    if (y > GROUND_Y - 200) {
      this.playerTargetX = Phaser.Math.Clamp(x, 50, WORLD_WIDTH - 50);
    }
  }

  update() {
    // Handle keyboard input
    if (this.cursors.left?.isDown) {
      this.player.x -= PLAYER_SPEED * 0.016;
      this.player.setFlipX(true);
    } else if (this.cursors.right?.isDown) {
      this.player.x += PLAYER_SPEED * 0.016;
      this.player.setFlipX(false);
    }

    // Handle click-to-move
    if (this.playerTargetX !== null) {
      const dx = this.playerTargetX - this.player.x;
      if (Math.abs(dx) < 5) {
        this.playerTargetX = null;
        this.onPlayerMoveCallback?.(this.player.x, this.player.y);
      } else {
        const direction = Math.sign(dx);
        this.player.x += direction * PLAYER_SPEED * 0.016;
        this.player.setFlipX(direction < 0);
      }
    }

    // Clamp player to ground
    this.player.y = GROUND_Y - 60;
    this.player.x = Phaser.Math.Clamp(this.player.x, 50, WORLD_WIDTH - 50);

    // Update shadow position
    this.playerShadow.setPosition(this.player.x, GROUND_Y + 10);
    this.playerShadow.setScale(1 - Math.abs(this.player.y - GROUND_Y) / 200);

    // Check proximity to hotspots
    this.checkProximity();
  }

  checkProximity() {
    this.interactablesData.forEach((data) => {
      const [x, y] = data.item.position;
      const distance = Phaser.Math.Distance.Between(this.player.x, this.player.y, x, y);
      const isNear = distance < PROXIMITY_THRESHOLD;

      if (isNear) {
        this.highlightInteractable(data, true);
      } else {
        this.highlightInteractable(data, false);
      }
    });
  }
}

export function PhaserGameCanvas({
  mapData,
  interactables,
  playerPosition,
  onPlayerMove,
  onInteract,
}: PhaserGameCanvasProps) {
  const gameRef = useRef<Phaser.Game | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const callbacksRef = useRef({ onPlayerMove, onInteract });

  // Keep callbacks fresh
  callbacksRef.current = { onPlayerMove, onInteract };

  useEffect(() => {
    if (!containerRef.current || !mapData) return;

    const config: Phaser.Types.Core.GameConfig = {
      type: Phaser.AUTO,
      width: 1280,
      height: 720,
      parent: containerRef.current,
      backgroundColor: "#1a1a2e",
      scene: [GameScene],
      physics: {
        default: "arcade",
        arcade: {
          gravity: { x: 0, y: 0 },
        },
      },
      scale: {
        mode: Phaser.Scale.FIT,
        autoCenter: Phaser.Scale.CENTER_BOTH,
      },
      render: {
        antialias: true,
        pixelArt: false,
      },
    };

    gameRef.current = new Phaser.Game(config);

    // Pass data to scene after creation
    const timer = setTimeout(() => {
      const scene = gameRef.current?.scene.getScene("GameScene") as GameScene;
      if (scene) {
        scene.scene.restart({
          mapData,
          interactables,
          playerPosition,
          onPlayerMove: (x: number, y: number) => callbacksRef.current.onPlayerMove(x, y),
          onInteract: (item: Interactable) => callbacksRef.current.onInteract(item),
        });
      }
    }, 100);

    return () => {
      clearTimeout(timer);
      gameRef.current?.destroy(true);
    };
  }, [mapData, interactables, playerPosition]);

  return (
    <div
      ref={containerRef}
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "#0a0a1a",
        borderRadius: 8,
        overflow: "hidden",
      }}
    />
  );
}
