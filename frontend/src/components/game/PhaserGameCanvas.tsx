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
const PROXIMITY_THRESHOLD = 150;

// Interactable data with Phaser game objects
interface InteractableData {
  item: Interactable;
  zone: Phaser.GameObjects.Zone;
  icon: Phaser.GameObjects.Text | Phaser.GameObjects.Sprite;
  label: Phaser.GameObjects.Text;
  glow: Phaser.GameObjects.Graphics;
  indicator: Phaser.GameObjects.Graphics;
  isNear: boolean;
}

class GameScene extends Phaser.Scene {
  private player!: Phaser.GameObjects.Container;
  private playerShadow!: Phaser.GameObjects.Ellipse;
  private cursors!: Phaser.Types.Input.Keyboard.CursorKeys;
  private groundGraphics!: Phaser.GameObjects.Graphics;
  private onPlayerMoveCallback: ((x: number, y: number) => void) | null = null;
  private onInteractCallback: ((interactable: Interactable) => void) | null = null;
  private interactablesData: InteractableData[] = [];
  private playerTargetX: number | null = null;
  private sceneInteractables: Interactable[] = [];

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
    this.sceneInteractables = data.interactables;
    this.interactablesData = [];
    this.playerTargetX = null;
  }

  preload() {
    // Load player portrait
    this.load.image("player", "/uploads/characters/player_portrait.png");
    this.load.image("bg-lobby", "/uploads/scenes/lobby_bg.png");
  }

  create() {
    // Dark background
    const bg = this.add.graphics();
    bg.fillGradientStyle(0x1a1a2e, 0x1a1a2e, 0x16213e, 0x16213e, 1);
    bg.fillRect(0, 0, WORLD_WIDTH, WORLD_HEIGHT);

    // Background image
    const bgImage = this.add.image(WORLD_WIDTH / 2, WORLD_HEIGHT / 2, "bg-lobby");
    bgImage.setDisplaySize(WORLD_WIDTH, WORLD_HEIGHT);
    bgImage.setAlpha(0.6);

    // Ground
    this.groundGraphics = this.add.graphics();
    this.drawGround();

    // Create player
    this.createPlayer();

    // Camera
    this.cameras.main.setBounds(0, 0, WORLD_WIDTH, WORLD_HEIGHT);
    this.cameras.main.startFollow(this.player, true, 0.08, 0.08);
    this.cameras.main.setZoom(0.8);

    // Keyboard
    this.cursors = this.input.keyboard!.createCursorKeys();

    // Load NPC portraits and create hotspots
    this.loadNPCPortraitsAndCreateHotspots();

    // Click to move
    this.input.on("pointerdown", (pointer: Phaser.Input.Pointer) => {
      this.handleGroundClick(pointer.worldX, pointer.worldY);
    });

    // Ambient particles
    this.createAmbientParticles();
  }

  loadNPCPortraitsAndCreateHotspots() {
    // Load NPC portrait textures dynamically
    let pendingLoads = 0;
    const interactables = this.sceneInteractables || [];

    interactables.forEach((item) => {
      if (item.icon && item.icon.startsWith("/")) {
        const textureKey = `npc_${item.id}`;
        if (!this.textures.exists(textureKey)) {
          pendingLoads++;
          this.load.image(textureKey, item.icon);
        }
      }
    });

    if (pendingLoads > 0) {
      this.load.once("complete", () => {
        this.createHotspots();
      });
      this.load.start();
    } else {
      this.createHotspots();
    }
  }

  createPlayer() {
    this.player = this.add.container(100, GROUND_Y - 60);

    // Shadow
    this.playerShadow = this.add.ellipse(0, 60, 50, 12, 0x000000, 0.3);

    // Try to use loaded texture, fallback to drawn circle
    let sprite: Phaser.GameObjects.Sprite | Phaser.GameObjects.Graphics;

    if (this.textures.exists("player") && this.textures.get("player").key !== "__MISSING") {
      sprite = this.add.sprite(0, 0, "player");
      sprite.setScale(0.15);
    } else {
      // Fallback: pink circle with face
      const g = this.add.graphics();
      g.fillStyle(0xFF69B4, 1);
      g.fillCircle(0, 0, 30);
      // Eyes
      g.fillStyle(0xFFFFFF, 1);
      g.fillCircle(-8, -5, 6);
      g.fillCircle(8, -5, 6);
      g.fillStyle(0x333333, 1);
      g.fillCircle(-8, -5, 3);
      g.fillCircle(8, -5, 3);
      // Mouth
      g.lineStyle(2, 0x333333, 1);
      g.beginPath();
      g.arc(0, 8, 6, 0, Math.PI);
      g.strokePath();
      sprite = g;
    }

    this.player.add(sprite);
    this.player.setSize(60, 60);

    // Idle animation
    this.tweens.add({
      targets: this.player,
      y: this.player.y - 3,
      duration: 1500,
      yoyo: true,
      repeat: -1,
      ease: "Sine.easeInOut",
    });
  }

  drawGround() {
    this.groundGraphics.clear();
    this.groundGraphics.fillStyle(0x2d3436, 0.8);
    this.groundGraphics.fillRect(0, GROUND_Y, WORLD_WIDTH, WORLD_HEIGHT - GROUND_Y);
    this.groundGraphics.lineStyle(2, 0x636e72, 0.5);
    this.groundGraphics.lineBetween(0, GROUND_Y, WORLD_WIDTH, GROUND_Y);
    for (let x = 0; x < WORLD_WIDTH; x += 200) {
      this.groundGraphics.fillStyle(0x3d4446, 0.3);
      this.groundGraphics.fillRect(x + 50, GROUND_Y + 20, 100, 5);
    }
  }

  createAmbientParticles() {
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
    particles.setName("ambient_dust");
  }

  createHotspots() {
    // Clean up old data
    this.interactablesData.forEach((data) => {
      data.zone.destroy();
      data.icon.destroy();
      data.label.destroy();
      data.glow.destroy();
      data.indicator.destroy();
    });
    this.interactablesData = [];

    // Create new hotspots from scene data
    this.sceneInteractables.forEach((item) => {
      const [x, y] = item.position;

      // Interaction zone (larger for easier clicking)
      const zone = this.add.zone(x, y, 100, 100).setInteractive({ useHandCursor: true });

      // Icon - use portrait image if available, otherwise emoji
      let icon: Phaser.GameObjects.Sprite | Phaser.GameObjects.Text;
      const textureKey = `npc_${item.id}`;
      if (item.icon && item.icon.startsWith("/") && this.textures.exists(textureKey)) {
        icon = this.add.sprite(x, y - 30, textureKey);
        icon.setScale(0.08);
      } else {
        const iconText = this.getIconForType(item.type);
        icon = this.add.text(x, y - 40, iconText, {
          fontSize: "32px",
          align: "center",
        }).setOrigin(0.5);
      }

      // Label
      const label = this.add.text(x, y + 25, item.name, {
        fontSize: "12px",
        color: "#ffffff",
        backgroundColor: "#00000080",
        padding: { x: 6, y: 2 },
      }).setOrigin(0.5);

      // Glow effect
      const glow = this.add.graphics();
      glow.setVisible(false);

      // Pulsing indicator (always visible)
      const indicator = this.add.graphics();
      this.drawIndicator(indicator, x, y, item.type, false);

      const data: InteractableData = {
        item,
        zone,
        icon: icon as Phaser.GameObjects.Text,
        label,
        glow,
        indicator,
        isNear: false,
      };

      this.interactablesData.push(data);

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

  drawIndicator(indicator: Phaser.GameObjects.Graphics, x: number, y: number, type: string, isNear: boolean) {
    indicator.clear();

    const color = type === "npc" ? 0x74b9ff : type === "exit" ? 0x55efc4 : 0xffeaa7;
    const alpha = isNear ? 1 : 0.6;

    // Outer ring
    indicator.lineStyle(2, color, alpha);
    indicator.strokeCircle(x, y, 35);

    // Inner fill
    indicator.fillStyle(color, alpha * 0.2);
    indicator.fillCircle(x, y, 35);

    // Pulsing dot in center
    indicator.fillStyle(color, alpha);
    indicator.fillCircle(x, y, 5);

    // Up arrow for visibility
    indicator.fillStyle(color, alpha);
    indicator.fillTriangle(x - 6, y - 25, x + 6, y - 25, x, y - 35);
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
      data.glow.lineStyle(3, 0xFF6B9D, 0.9);
      data.glow.strokeCircle(x, y, 45);
      data.glow.fillStyle(0xFF6B9D, 0.15);
      data.glow.fillCircle(x, y, 45);
    }
    data.glow.setVisible(active);
  }

  handleGroundClick(x: number, y: number) {
    if (y > GROUND_Y - 200) {
      this.playerTargetX = Phaser.Math.Clamp(x, 50, WORLD_WIDTH - 50);
    }
  }

  update() {
    // Keyboard
    if (this.cursors.left?.isDown) {
      this.player.x -= PLAYER_SPEED * 0.016;
      this.player.setScale(-1, 1);
    } else if (this.cursors.right?.isDown) {
      this.player.x += PLAYER_SPEED * 0.016;
      this.player.setScale(1, 1);
    }

    // Click to move
    if (this.playerTargetX !== null) {
      const dx = this.playerTargetX - this.player.x;
      if (Math.abs(dx) < 5) {
        this.playerTargetX = null;
        this.onPlayerMoveCallback?.(this.player.x, this.player.y);
      } else {
        const direction = Math.sign(dx);
        this.player.x += direction * PLAYER_SPEED * 0.016;
        this.player.setScale(direction < 0 ? -1 : 1, 1);
      }
    }

    // Clamp
    this.player.y = GROUND_Y - 60;
    this.player.x = Phaser.Math.Clamp(this.player.x, 50, WORLD_WIDTH - 50);

    // Shadow
    this.playerShadow.setPosition(this.player.x, GROUND_Y + 10);

    // Proximity check
    this.checkProximity();
  }

  checkProximity() {
    this.interactablesData.forEach((data) => {
      const [x, y] = data.item.position;
      const distance = Phaser.Math.Distance.Between(this.player.x, this.player.y, x, y);
      const isNear = distance < PROXIMITY_THRESHOLD;

      if (isNear !== data.isNear) {
        data.isNear = isNear;
        this.drawIndicator(data.indicator, x, y, data.item.type, isNear);

        if (isNear) {
          this.highlightInteractable(data, true);
        } else {
          this.highlightInteractable(data, false);
        }
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
