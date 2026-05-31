import { useEffect, useRef, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Button, Input, Spin } from "antd";
import { gameService } from "../../services/games";
import { useGameStore } from "../../stores/gameStore";
import type { ChoiceItem, StatChange } from "../../stores/gameStore";
import { InvestigationView } from "../../components/game/InvestigationView";

export default function Game() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const {
    turns, sceneBackground, sceneName, isStreaming,
    addPlayerTurn, appendNarration, completeTurn,
    loadHistory, setSceneName, reset,
  } = useGameStore();

  const [customInput, setCustomInput] = useState("");
  const [sceneTransition, setSceneTransition] = useState(false);
  const [statNotifications, setStatNotifications] = useState<StatChange[]>([]);
  const [isInvestigating, setIsInvestigating] = useState(false);
  const [currentSceneId, setCurrentSceneId] = useState<number | null>(null);
  const dialogEndRef = useRef<HTMLDivElement>(null);

  // Load history on mount
  useEffect(() => {
    if (!sessionId) return;
    const token = localStorage.getItem("access_token");
    if (!token) { navigate("/login"); return; }

    // Load game session info
    gameService.get(Number(sessionId)).then((resp: any) => {
      const session = resp.data as unknown as Record<string, unknown>;
      setSceneName((session.game_time as string) || "第1天 上午");
    }).catch(() => navigate("/login"));

    // Load dialog history — if empty, auto-trigger opening narration
    gameService.getHistory(Number(sessionId)).then(async (resp: any) => {
      const items = (resp.data?.data || []) as Array<{
        player_input: string | null;
        content: string;
        meta_data: { choices?: ChoiceItem[] } | null;
        created_at: string | null;
      }>;
      if (items.length > 0) {
        loadHistory(items);
      } else {
        // No history yet — auto-trigger the opening narration via streaming
        const turnId = addPlayerTurn("开始游戏");
        try {
          for await (const event of gameService.sendActionStream(Number(sessionId), { message: "开始游戏" })) {
            if (event.event === "narration_chunk") {
              const data = event.data as { text: string };
              appendNarration(turnId, data.text || "");
            } else if (event.event === "complete") {
              const data = event.data as Record<string, unknown>;
              const response = {
                narration: (data.narration as string) || "",
                dialogs: [],
                choices: (data.choices as ChoiceItem[]) || [],
                sceneChange: (data.scene_change as { to_scene_id: string; transition: string } | null) || null,
                statChanges: (data.stat_changes as StatChange[]) || [],
              };
              completeTurn(turnId, response);
            }
          }
        } catch {
          completeTurn(turnId, {
            narration: "开局生成失败，请重试。",
            dialogs: [],
            choices: [{ id: "retry", text: "再试一次", is_custom: false }],
            sceneChange: null,
            statChanges: [],
          });
        }
      }
    }).catch(() => {});

    return () => reset();
  }, [sessionId]);

  // Auto-scroll
  useEffect(() => {
    dialogEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns]);

  // Handle stat notifications
  const showStatNotification = useCallback((changes: StatChange[]) => {
    setStatNotifications(changes);
    setTimeout(() => setStatNotifications([]), 2500);
  }, []);

  // Streaming action handler
  const handleAction = useCallback(async (input: string) => {
    if (!sessionId || isStreaming) return;
    const turnId = addPlayerTurn(input);
    setCustomInput("");

    try {
      for await (const event of gameService.sendActionStream(Number(sessionId), { message: input })) {
        if (event.event === "narration_chunk") {
          const data = event.data as { text: string };
          appendNarration(turnId, data.text || "");
        } else if (event.event === "complete") {
          const data = event.data as Record<string, unknown>;
          const response = {
            narration: (data.narration as string) || "",
            dialogs: [],
            choices: (data.choices as ChoiceItem[]) || [],
            sceneChange: (data.scene_change as { to_scene_id: string; transition: string } | null) || null,
            statChanges: (data.stat_changes as StatChange[]) || [],
          };
          completeTurn(turnId, response);

          if (response.sceneChange) {
            setSceneTransition(true);
            setTimeout(() => setSceneTransition(false), 1200);
          }
          if (response.statChanges.length > 0) {
            showStatNotification(response.statChanges);
          }
        } else if (event.event === "error") {
          completeTurn(turnId, {
            narration: "连接出现问题，请重试...",
            dialogs: [],
            choices: [{ id: "retry", text: "再试一次", is_custom: false }],
            sceneChange: null,
            statChanges: [],
          });
        }
      }
    } catch {
      completeTurn(turnId, {
        narration: "操作失败，请重试。",
        dialogs: [],
        choices: [{ id: "retry", text: "再试一次", is_custom: false }],
        sceneChange: null,
        statChanges: [],
      });
    }
  }, [sessionId, isStreaming]);

  const handleInvestigationComplete = useCallback((context: string) => {
    // Close investigation view and trigger AI with investigation context
    setIsInvestigating(false);
    handleAction(`调查发现：${context}`);
  }, [handleAction]);

  const startInvestigation = useCallback(() => {
    // Get current scene ID from game session
    if (!sessionId) return;
    gameService.get(Number(sessionId)).then((resp: any) => {
      const session = resp.data as unknown as Record<string, unknown>;
      const sceneId = session.current_scene_id as number;
      if (sceneId) {
        setCurrentSceneId(sceneId);
        setIsInvestigating(true);
      }
    }).catch(() => {});
  }, [sessionId]);

  const lastTurn = turns[turns.length - 1];
  const showChoices = lastTurn?.isComplete && lastTurn?.choices.length > 0 && !isStreaming;

  const endGame = async () => {
    if (!sessionId) return;
    await gameService.end(Number(sessionId), "abandoned");
    reset();
    navigate("/");
  };

  const gradientBg = "linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)";
  const bgStyle = sceneBackground
    ? { backgroundImage: `url(${sceneBackground})`, backgroundSize: "cover", backgroundPosition: "center" }
    : { background: gradientBg };

  return (
    <div className="game-container" style={{ ...bgStyle, position: "relative", minHeight: "100vh" }}>
      {/* Scene transition overlay */}
      {sceneTransition && (
        <div style={{
          position: "fixed", inset: 0, background: "black", opacity: 0.8,
          transition: "opacity 0.6s ease", zIndex: 100, pointerEvents: "none",
        }} />
      )}

      {/* Stat change notifications */}
      {statNotifications.length > 0 && (
        <div style={{ position: "fixed", top: 80, right: 20, zIndex: 50 }}>
          {statNotifications.map((s, i) => (
            <div key={i} className="stat-notification" style={{
              background: s.change > 0 ? "rgba(0,200,83,0.9)" : "rgba(255,82,82,0.9)",
              color: "#fff", padding: "8px 16px", borderRadius: 8, marginBottom: 4,
              fontSize: 14, animation: "slideIn 0.3s ease-out",
            }}>
              {s.stat}: {s.change > 0 ? "+" : ""}{s.change}
            </div>
          ))}
        </div>
      )}

      {/* Top bar */}
      <div style={{
        position: "sticky", top: 0, zIndex: 10,
        background: "rgba(10,10,26,0.85)", backdropFilter: "blur(12px)",
        padding: "12px 20px", display: "flex", justifyContent: "space-between", alignItems: "center",
        borderBottom: "1px solid rgba(255,107,157,0.2)",
      }}>
        <div style={{ color: "#fff" }}>
          <span style={{ fontSize: 18, fontWeight: 700, color: "#FF6B9D" }}>{sceneName || "游戏中"}</span>
        </div>
        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
          <Button danger size="small" onClick={endGame}>退出</Button>
        </div>
      </div>

      {/* Dialog history area */}
      <div style={{
        flex: 1, overflow: "auto", padding: "16px 20px",
        background: "rgba(10,10,26,0.7)", backdropFilter: "blur(8px)",
        minHeight: 0,
      }}>
        {/* Empty state */}
        {turns.length === 0 && !isStreaming && (
          <div style={{ textAlign: "center", padding: "40px 0", color: "#888" }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>🎭</div>
            <div style={{ fontSize: 16 }}>故事正在展开，输入你的第一步行动...</div>
          </div>
        )}

        {/* Turn history */}
        {turns.map((turn) => (
          <div key={turn.id} style={{ marginBottom: 24 }}>
            {/* Player input */}
            {turn.playerInput && (
              <div style={{
                textAlign: "right", marginBottom: 12,
                padding: "8px 16px", borderRadius: "12px 12px 2px 12px",
                background: "rgba(255,107,157,0.15)", borderLeft: "3px solid #FF6B9D",
                color: "#FF6B9D", fontSize: 14, fontWeight: 500,
              }}>
                {turn.playerInput}
              </div>
            )}

            {/* Narration */}
            {turn.narration && (
              <div style={{
                padding: "16px 20px", borderRadius: 12,
                background: "rgba(45,52,54,0.9)", color: "#dfe6e9",
                fontSize: 16, lineHeight: 1.8, whiteSpace: "pre-wrap",
                border: "1px solid rgba(255,107,157,0.1)",
              }}>
                {turn.narration.replace(/\\n/g, "\n")}
                {turn.isStreaming && (
                  <span className="typewriter-cursor" style={{
                    color: "#FF6B9D", fontWeight: 700,
                    animation: "blink 0.8s infinite",
                  }}>▌</span>
                )}
              </div>
            )}

            {/* Streaming indicator */}
            {turn.isStreaming && !turn.narration && (
              <div style={{ textAlign: "center", padding: 16 }}>
                <Spin size="small" />
                <span style={{ color: "#888", marginLeft: 8 }}>剧情生成中...</span>
              </div>
            )}
          </div>
        ))}

        <div ref={dialogEndRef} />
      </div>

      {/* Choice panel */}
      {showChoices && (
        <div style={{
          position: "sticky", bottom: 0, zIndex: 10,
          background: "rgba(10,10,26,0.85)", backdropFilter: "blur(12px)",
          padding: "12px 20px", borderTop: "1px solid rgba(255,107,157,0.2)",
        }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {lastTurn.choices.map((choice, i) => (
              <button
                key={choice.id}
                className="choice-btn"
                style={{
                  padding: "12px 20px", borderRadius: 10,
                  background: choice.is_custom ? "rgba(255,107,157,0.08)" : "rgba(255,107,157,0.15)",
                  border: choice.is_custom ? "1px dashed rgba(255,107,157,0.3)" : "1px solid rgba(255,107,157,0.3)",
                  color: "#fff", fontSize: 15, textAlign: "left",
                  cursor: "pointer", transition: "all 0.2s",
                  animation: `fadeIn 0.3s ease-out ${i * 0.1}s both`,
                }}
                onClick={() => handleAction(choice.text)}
              >
                <span style={{ color: "#FF6B9D", fontWeight: 700, marginRight: 8 }}>
                  {choice.is_custom ? "✦" : `▸`}
                </span>
                {choice.text}
              </button>
            ))}
          </div>

          {/* Custom input */}
          <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
            <Input
              placeholder="输入你的行动..."
              value={customInput}
              onChange={(e) => setCustomInput(e.target.value)}
              onPressEnter={() => { if (customInput.trim()) handleAction(customInput); }}
              style={{
                flex: 1, background: "rgba(0,0,0,0.3)", borderColor: "rgba(255,107,157,0.3)",
                color: "#fff", borderRadius: 8,
              }}
            />
            <Button type="primary" onClick={() => { if (customInput.trim()) handleAction(customInput); }}
              style={{ borderRadius: 8, minWidth: 60 }}>
              发送
            </Button>
            <Button
              onClick={startInvestigation}
              style={{
                borderRadius: 8,
                background: "rgba(255, 107, 157, 0.2)",
                borderColor: "rgba(255, 107, 157, 0.5)",
                color: "#FF6B9D",
              }}
            >
              🔍 调查
            </Button>
          </div>
        </div>
      )}

      {/* Investigation View */}
      {isInvestigating && currentSceneId && (
        <InvestigationView
          sessionId={Number(sessionId)}
          sceneId={currentSceneId}
          onClose={() => setIsInvestigating(false)}
          onInvestigationComplete={handleInvestigationComplete}
        />
      )}
    </div>
  );
}