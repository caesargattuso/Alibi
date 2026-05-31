import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Typography, Button, Card, Tag, Row, Col, message, Input, Modal, Descriptions } from "antd";
import { scriptService } from "../../services/scripts";
import { gameService } from "../../services/games";
import type { Script } from "../../types";

const { Title, Paragraph, Text } = Typography;

export default function ScriptDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [script, setScript] = useState<Script | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [playerName, setPlayerName] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!id) return;
    scriptService.get(Number(id)).then(({ data: resp }) => setScript(resp.data as Script));
  }, [id]);

  const startGame = async () => {
    if (!id || !playerName.trim()) {
      message.warning("请输入角色名");
      return;
    }
    setLoading(true);
    try {
      const { data: resp } = await gameService.create({ script_id: Number(id), player_name: playerName });
      const d = resp.data as unknown as Record<string, number>;
      setModalOpen(false);
      navigate(`/game/${d.id}`);
    } catch {
      message.error("创建游戏失败");
    } finally {
      setLoading(false);
    }
  };

  if (!script) return (
    <div style={{ minHeight: "100vh", background: "#0a0a1a", display: "flex", justifyContent: "center", alignItems: "center" }}>
      <div className="skeleton" style={{ width: "80%", maxWidth: 800, height: 400 }} />
    </div>
  );

  return (
    <div style={{ minHeight: "100vh", background: "linear-gradient(180deg, #0a0a1a 0%, #1a1a2e 100%)" }}>
      {/* Banner */}
      <div style={{
        height: 280, position: "relative", overflow: "hidden",
        background: script.cover_image
          ? `url(${script.cover_image}) center/cover`
          : "linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)",
      }}>
        <div style={{
          position: "absolute", inset: 0,
          background: "linear-gradient(transparent 30%, rgba(10,10,26,0.95))",
        }} />
        <div style={{
          position: "absolute", bottom: 24, left: 24, right: 24,
        }}>
          <Tag color="pink" style={{ marginBottom: 8 }}>{script.genre}</Tag>
          <Title level={2} style={{ color: "#fff", margin: 0 }}>{script.title}</Title>
        </div>
      </div>

      <div style={{ maxWidth: 900, margin: "0 auto", padding: "24px" }}>
        <Row gutter={[24, 24]}>
          {/* Main info */}
          <Col xs={24} md={16}>
            {/* Description */}
            <Card style={{
              background: "rgba(26,26,46,0.8)",
              border: "1px solid rgba(255,107,157,0.15)",
              borderRadius: 12, marginBottom: 16,
            }}>
              <Title level={5} style={{ color: "#FF6B9D", marginBottom: 12 }}>剧情简介</Title>
              <Paragraph style={{ color: "rgba(255,255,255,0.8)", fontSize: 15, lineHeight: 1.8 }}>
                {script.description}
              </Paragraph>
            </Card>

            {/* Game info */}
            <Card style={{
              background: "rgba(26,26,46,0.8)",
              border: "1px solid rgba(255,107,157,0.15)",
              borderRadius: 12,
            }}>
              <Descriptions column={2} labelStyle={{ color: "rgba(255,255,255,0.5)" }} contentStyle={{ color: "#fff" }}>
                <Descriptions.Item label="类型">
                  <Tag color="pink">{script.genre}</Tag>
                </Descriptions.Item>
                <Descriptions.Item label="难度">
                  <Tag style={{
                    background: script.difficulty === "hard" ? "rgba(255,82,82,0.2)" : "rgba(255,255,255,0.08)",
                    borderColor: script.difficulty === "hard" ? "rgba(255,82,82,0.4)" : "rgba(255,255,255,0.15)",
                    color: script.difficulty === "hard" ? "#ff5252" : "#fff",
                  }}>
                    {script.difficulty}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="评分">
                  <span style={{ color: "#ffeaa7" }}>⭐ {script.rating}</span>
                </Descriptions.Item>
                <Descriptions.Item label="游玩次数">
                  {script.play_count} 次
                </Descriptions.Item>
              </Descriptions>

              {script.tags && script.tags.length > 0 && (
                <div style={{ marginTop: 12 }}>
                  {script.tags.map((tag) => (
                    <Tag key={tag} style={{
                      background: "rgba(255,255,255,0.06)",
                      borderColor: "rgba(255,255,255,0.12)",
                      color: "rgba(255,255,255,0.6)",
                      marginRight: 4,
                    }}>
                      {tag}
                    </Tag>
                  ))}
                </div>
              )}
            </Card>
          </Col>

          {/* Side panel */}
          <Col xs={24} md={8}>
            {/* Cover image */}
            <div style={{
              width: "100%", aspectRatio: "3/4", borderRadius: 12, overflow: "hidden",
              background: script.cover_image
                ? `url(${script.cover_image}) center/cover`
                : "linear-gradient(135deg, #FF6B9D33, #1a1a2e)",
              marginBottom: 16, border: "1px solid rgba(255,107,157,0.15)",
            }} />

            {/* Start button */}
            <Button
              type="primary"
              size="large"
              block
              loading={loading}
              onClick={() => setModalOpen(true)}
              style={{
                height: 52, fontSize: 18, fontWeight: 700,
                borderRadius: 12, background: "#FF6B9D",
                border: "none",
                boxShadow: "0 4px 20px rgba(255,107,157,0.4)",
              }}
            >
              开始游戏
            </Button>

            <div style={{ textAlign: "center", marginTop: 12 }}>
              <Text style={{ color: "rgba(255,255,255,0.4)", fontSize: 13 }}>
                已有 {script.play_count} 名玩家体验
              </Text>
            </div>
          </Col>
        </Row>
      </div>

      <Modal
        title="输入角色名"
        open={modalOpen}
        onOk={startGame}
        onCancel={() => setModalOpen(false)}
        styles={{
          body: { background: "#1a1a2e", borderRadius: 12 },
          header: { background: "#1a1a2e", borderBottom: "1px solid rgba(255,107,157,0.2)" },
        }}
      >
        <Input
          placeholder="你的角色名"
          value={playerName}
          onChange={(e) => setPlayerName(e.target.value)}
          maxLength={100}
          style={{
            background: "rgba(0,0,0,0.3)",
            borderColor: "rgba(255,107,157,0.3)",
            color: "#fff",
          }}
        />
      </Modal>
    </div>
  );
}