import { useEffect, useRef, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Button, Input, Spin } from "antd";
import { gameService } from "../../services/games";
import { useGameStore } from "../../stores/gameStore";
import type { ChoiceItem, DialogItem, StatChange } from "../../stores/gameStore";

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

    // Load dialog history
    gameService.getHistory(Number(sessionId)).then((resp: any) => {
      const items = (resp.data?.data || []) as Array<{
        player_input: string | null;
        content: string;
        meta_data: { choices?: ChoiceItem[]; dialogs?: DialogItem[] } | null;
        created_at: string | null;
      }>;
      if (items.length > 0) loadHistory(items);
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

  // Streaming action handler with typewriter effect
  const handleAction = useCallback(async (input: string) => {
    if (!sessionId || isStreaming) return;
    const turnId = addPlayerTurn(input);
    setCustomInput("");

    const chunkQueue: string[] = [];
    let completeData: Record<string, unknown> | null = null;
    let processing = true;

    // Process chunks with typewriter effect
    const processChunks = async () => {
      while (processing || chunkQueue.length > 0) {
        if (chunkQueue.length > 0) {
          const chunk = chunkQueue.shift()!;
          appendNarration(turnId, chunk);
          // Delay between chunks for typing effect
          await new Promise((resolve) => setTimeout(resolve, 30));
        } else {
          // Wait for more chunks
          await new Promise((resolve) => setTimeout(resolve, 50));
        }
      }
      // All chunks processed, now complete the turn
      if (completeData) {
        const data = completeData;
        const response = {
          narration: (data.narration as string) || "",
          dialogs: (data.dialogs as DialogItem[]) || [],
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
      }
    };

    // Start processing chunks
    const processPromise = processChunks();

    try {
      for await (const event of gameService.sendActionStream(Number(sessionId), { message: input })) {
        if (event.event === "narration_chunk") {
          const data = event.data as { text: string };
          chunkQueue.push(data.text || "");
        } else if (event.event === "complete") {
          completeData = event.data as Record<string, unknown>;
          processing = false;
        } else if (event.event === "error") {
          processing = false;
          completeData = {
            narration: "连接出现问题，请重试...",
            dialogs: [],
            choices: [{ id: "retry", text: "再试一次", is_custom: false }],
            scene_change: null,
            stat_changes: [],
          };
        }
      }
    } catch {
      processing = false;
      completeData = {
        narration: "操作失败，请重试。",
        dialogs: [],
        choices: [{ id: "retry", text: "再试一次", is_custom: false }],
        scene_change: null,
        stat_changes: [],
      };
    }

    await processPromise;
  }, [sessionId, isStreaming]);

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
                {turn.narration}
                {turn.isStreaming && (
                  <span className="typewriter-cursor" style={{
                    color: "#FF6B9D", fontWeight: 700,
                    animation: "blink 0.8s infinite",
                  }}>▌</span>
                )}
              </div>
            )}

            {/* Dialogs */}
            {turn.dialogs.map((d, i) => (
              <div key={i} style={{
                marginTop: 8, padding: "10px 16px", borderRadius: 10,
                background: "rgba(99,110,114,0.7)", color: "#fff",
                fontSize: 15,
              }}>
                <span style={{ color: "#ffeaa7", fontWeight: 600 }}>{d.speaker}</span>
                {d.emotion && d.emotion !== "neutral" && (
                  <span style={{
                    marginLeft: 6, fontSize: 12, padding: "2px 6px", borderRadius: 4,
                    background: d.emotion === "happy" ? "rgba(0,200,83,0.3)" :
                      d.emotion === "sad" ? "rgba(255,82,82,0.3)" :
                      d.emotion === "angry" ? "rgba(255,165,0,0.3)" :
                      "rgba(116,185,255,0.3)",
                    color: "#fff",
                  }}>
                    {d.emotion}
                  </span>
                )}
                <div style={{ marginTop: 4 }}>{d.text}</div>
              </div>
            ))}

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
          </div>
        </div>
      )}

      {/* Waiting for first chunk */}
      {isStreaming && !lastTurn?.narration && (
        <div style={{
          position: "sticky", bottom: 60, textAlign: "center",
          padding: 8, color: "#888", fontSize: 14, zIndex: 5,
        }}>
          <Spin size="small" /> 思考中...
        </div>
      )}
    </div>
  );
}