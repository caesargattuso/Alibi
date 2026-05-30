import { useEffect, useState, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Typography, Button, Input, Card, Spin, message } from "antd";
import { gameService } from "../../services/games";
import { useGameStore } from "../../stores/gameStore";

const { Paragraph, Title } = Typography;

export default function Game() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const { narration, dialogs, choices, isLoading, updateFromAI, setLoading } = useGameStore();
  const [customInput, setCustomInput] = useState("");
  const dialogEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    dialogEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [narration, dialogs]);

  const handleChoice = async (choiceId: string) => {
    if (!sessionId) return;
    setLoading(true);
    try {
      const { data } = await gameService.sendMessage(Number(sessionId), { choice_id: choiceId });
      updateFromAI(data.data);
    } catch {
      message.error("操作失败");
    } finally {
      setLoading(false);
    }
  };

  const handleCustomInput = async () => {
    if (!sessionId || !customInput.trim()) return;
    setLoading(true);
    try {
      const { data } = await gameService.sendMessage(Number(sessionId), { message: customInput });
      updateFromAI(data.data);
      setCustomInput("");
    } catch {
      message.error("操作失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", background: "#1a1a2e", color: "#fff" }}>
      {/* 顶部信息栏 */}
      <div style={{ padding: "8px 16px", background: "#2d3436", display: "flex", justifyContent: "space-between" }}>
        <Title level={4} style={{ color: "#fff", margin: 0 }}>游戏中</Title>
        <Button danger onClick={() => { gameService.end(Number(sessionId), "abandoned"); navigate("/"); }}>
          退出
        </Button>
      </div>

      {/* 剧情文本区域 */}
      <div style={{ flex: 1, overflow: "auto", padding: 16 }}>
        <Card style={{ background: "#2d3436", color: "#fff", border: "none" }}>
          <Paragraph style={{ color: "#dfe6e9", whiteSpace: "pre-wrap", fontSize: 16, lineHeight: 1.8 }}>
            {narration || "故事正在展开..."}
          </Paragraph>
        </Card>

        {dialogs.map((d, i) => (
          <Card key={i} size="small" style={{ background: "#636e72", color: "#fff", border: "none", marginTop: 8 }}>
            <strong style={{ color: "#ffeaa7" }}>{d.speaker}：</strong>
            <span>{d.text}</span>
          </Card>
        ))}

        {isLoading && (
          <div style={{ textAlign: "center", padding: 16 }}>
            <Spin tip="剧情生成中..." />
          </div>
        )}

        <div ref={dialogEndRef} />
      </div>

      {/* 选项区域 */}
      {!isLoading && choices.length > 0 && (
        <div style={{ padding: "8px 16px", background: "#2d3436" }}>
          {choices.map((choice) => (
            <Button
              key={choice.id}
              block
              style={{ marginBottom: 4, textAlign: "left", height: "auto", whiteSpace: "normal" }}
              onClick={() => handleChoice(choice.id)}
            >
              {choice.text}
            </Button>
          ))}
        </div>
      )}

      {/* 自由输入区域 */}
      {!isLoading && (
        <div style={{ padding: "8px 16px", background: "#2d3436", display: "flex", gap: 8 }}>
          <Input
            placeholder="输入你的行动..."
            value={customInput}
            onChange={(e) => setCustomInput(e.target.value)}
            onPressEnter={handleCustomInput}
            style={{ flex: 1 }}
          />
          <Button type="primary" onClick={handleCustomInput}>
            发送
          </Button>
        </div>
      )}
    </div>
  );
}