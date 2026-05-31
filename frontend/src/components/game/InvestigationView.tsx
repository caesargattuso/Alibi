import { useState, useEffect, useCallback } from "react";
import { sceneService, type Interactable, type MapData } from "../../services/scenes";
import { PhaserGameCanvas } from "./PhaserGameCanvas";
import { InteractionMenu } from "./InteractionMenu";
import { NPCDialogue } from "./NPCDialogue";

interface Point {
  x: number;
  y: number;
}

interface InvestigationViewProps {
  sessionId: number;
  sceneId: number;
  onClose: () => void;
  onInvestigationComplete: (context: string) => void;
}

export function InvestigationView({
  sessionId,
  sceneId,
  onClose,
  onInvestigationComplete,
}: InvestigationViewProps) {
  const [mapData, setMapData] = useState<MapData | null>(null);
  const [interactables, setInteractables] = useState<Interactable[]>([]);
  const [playerPosition, setPlayerPosition] = useState<Point>({ x: 960, y: 800 });
  const [selectedInteractable, setSelectedInteractable] = useState<Interactable | null>(null);
  const [dialogueNPC, setDialogueNPC] = useState<Interactable | null>(null);
  const [investigationLog, setInvestigationLog] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadSceneData();
  }, [sceneId]);

  const loadSceneData = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const [mapRes, interactablesRes] = await Promise.all([
        sceneService.getMap(sceneId),
        sceneService.getInteractables(sceneId),
      ]);

      setMapData(mapRes.data.data);
      setInteractables(interactablesRes.data.data.interactables);

      // Set initial player position to default spawn point
      const spawnPoints = mapRes.data.data.spawn_points || [];
      const defaultSpawn = spawnPoints.find((sp) => sp.is_default);
      if (defaultSpawn) {
        setPlayerPosition({ x: defaultSpawn.position[0], y: defaultSpawn.position[1] });
      }
    } catch (error) {
      console.error("Failed to load scene data:", error);
      setError("加载场景数据失败，请重试。");
    } finally {
      setIsLoading(false);
    }
  };

  const handlePlayerMove = useCallback((x: number, y: number) => {
    setPlayerPosition({ x, y });
  }, []);

  const handleInteract = useCallback((interactable: Interactable) => {
    // For NPCs, open dialogue directly
    if (interactable.type === "npc") {
      setDialogueNPC(interactable);
    } else {
      setSelectedInteractable(interactable);
    }
  }, []);

  const handleAction = async (actionId: string) => {
    if (!selectedInteractable) return;

    try {
      const result = await sceneService.interact(sceneId, {
        session_id: sessionId,
        interactable_id: selectedInteractable.id,
        action_id: actionId,
      });

      const data = result.data.data;

      // Add to investigation log
      setInvestigationLog((prev) => [...prev, data.message]);

      // If there are clues revealed, add them to log
      if (data.clues_revealed && data.clues_revealed.length > 0) {
        data.clues_revealed.forEach((clue: string) => {
          setInvestigationLog((prev) => [...prev, `发现线索: ${clue}`]);
        });
      }

      // Trigger AI narrative generation with investigation context
      if (data.ai_trigger?.should_generate) {
        onInvestigationComplete(data.ai_trigger.context);
      }
    } catch (error) {
      console.error("Interaction failed:", error);
    }

    setSelectedInteractable(null);
  };

  const handleCloseMenu = () => {
    setSelectedInteractable(null);
  };

  const handleCloseDialogue = () => {
    setDialogueNPC(null);
  };

  const handleTalkComplete = (context: string) => {
    setInvestigationLog((prev) => [...prev, context]);
  };

  if (isLoading) {
    return (
      <div
        style={{
          position: "fixed",
          inset: 0,
          background: "#1a1a2e",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 100,
        }}
      >
        <div style={{ color: "#FF6B9D", fontSize: 16 }}>加载场景中...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div
        style={{
          position: "fixed",
          inset: 0,
          background: "#1a1a2e",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 100,
        }}
      >
        <div style={{ textAlign: "center" }}>
          <div style={{ color: "#FF6B9D", fontSize: 16, marginBottom: 16 }}>{error}</div>
          <button
            onClick={loadSceneData}
            style={{
              padding: "10px 20px",
              borderRadius: 8,
              background: "rgba(255, 107, 157, 0.15)",
              border: "1px solid rgba(255, 107, 157, 0.3)",
              color: "#fff",
              cursor: "pointer",
            }}
          >
            重试
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "#1a1a2e",
        zIndex: 100,
        display: "flex",
        flexDirection: "column",
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: "12px 20px",
          background: "rgba(10, 10, 26, 0.9)",
          borderBottom: "1px solid rgba(255, 107, 157, 0.2)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <span style={{ color: "#FF6B9D", fontSize: 18, fontWeight: 700 }}>调查模式</span>
        <button
          onClick={onClose}
          style={{
            padding: "8px 16px",
            borderRadius: 8,
            background: "rgba(255, 107, 157, 0.15)",
            border: "1px solid rgba(255, 107, 157, 0.3)",
            color: "#fff",
            cursor: "pointer",
          }}
        >
          返回剧情
        </button>
      </div>

      {/* Map and Log */}
      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
        {/* Phaser Game Canvas */}
        <div style={{ flex: 2, position: "relative" }}>
          <PhaserGameCanvas
            mapData={mapData}
            interactables={interactables}
            playerPosition={playerPosition}
            onPlayerMove={handlePlayerMove}
            onInteract={handleInteract}
          />
        </div>

        {/* Investigation Log */}
        <div
          style={{
            flex: 1,
            maxWidth: 300,
            padding: 16,
            borderLeft: "1px solid rgba(255, 107, 157, 0.2)",
            overflow: "auto",
          }}
        >
          <h3 style={{ color: "#FF6B9D", fontSize: 16, marginBottom: 12 }}>调查记录</h3>
          {investigationLog.length === 0 ? (
            <p style={{ color: "#636e72", fontSize: 14 }}>点击地图上的交互点进行调查</p>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {investigationLog.map((log, i) => (
                <div
                  key={i}
                  style={{
                    padding: "8px 12px",
                    borderRadius: 8,
                    background: "rgba(255, 107, 157, 0.1)",
                    color: "#dfe6e9",
                    fontSize: 14,
                  }}
                >
                  {log}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Interaction Menu Modal */}
      {selectedInteractable && (
        <InteractionMenu
          interactable={selectedInteractable}
          onAction={handleAction}
          onClose={handleCloseMenu}
        />
      )}

      {/* NPC Dialogue */}
      {dialogueNPC && (
        <NPCDialogue
          interactable={dialogueNPC}
          sessionId={sessionId}
          onClose={handleCloseDialogue}
          onTalkComplete={handleTalkComplete}
        />
      )}
    </div>
  );
}
