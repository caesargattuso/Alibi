import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Typography, Button, Card, Descriptions, Tag, Row, Col, message, Input, Modal } from "antd";
import { scriptService } from "../../services/scripts";
import { gameService } from "../../services/games";
import { useGameStore } from "../../stores/gameStore";
import type { Script } from "../../types";

const { Title, Paragraph } = Typography;

export default function ScriptDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const setSession = useGameStore((s) => s.setSession);
  const [script, setScript] = useState<Script | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [playerName, setPlayerName] = useState("");

  useEffect(() => {
    if (!id) return;
    scriptService.get(Number(id)).then(({ data }) => setScript(data.data));
  }, [id]);

  const startGame = async () => {
    if (!id || !playerName.trim()) {
      message.warning("请输入角色名");
      return;
    }
    try {
      const { data } = await gameService.create({ script_id: Number(id), player_name: playerName });
      setSession(data.data.id);
      setModalOpen(false);
      navigate(`/game/${data.data.id}`);
    } catch {
      message.error("创建游戏失败");
    }
  };

  if (!script) return <div style={{ padding: 24 }}>加载中...</div>;

  return (
    <div style={{ padding: 24, background: "#FFF5F7", minHeight: "100vh" }}>
      <Card>
        <Row gutter={24}>
          <Col span={8}>
            <div
              style={{
                height: 300,
                background: `url(${script.cover_image}) center/cover`,
                backgroundColor: "#FFE0E9",
                borderRadius: 12,
              }}
            />
          </Col>
          <Col span={16}>
            <Title level={2}>{script.title}</Title>
            <Descriptions column={2}>
              <Descriptions.Item label="类型"><Tag color="pink">{script.genre}</Tag></Descriptions.Item>
              <Descriptions.Item label="难度"><Tag>{script.difficulty}</Tag></Descriptions.Item>
              <Descriptions.Item label="评分">⭐ {script.rating}</Descriptions.Item>
              <Descriptions.Item label="游玩次数">{script.play_count}</Descriptions.Item>
            </Descriptions>
            <Paragraph style={{ marginTop: 16 }}>{script.description}</Paragraph>
            <Button type="primary" size="large" onClick={() => setModalOpen(true)}>
              开始游戏
            </Button>
          </Col>
        </Row>
      </Card>
      <Modal
        title="输入角色名"
        open={modalOpen}
        onOk={startGame}
        onCancel={() => setModalOpen(false)}
      >
        <Input
          placeholder="你的角色名"
          value={playerName}
          onChange={(e) => setPlayerName(e.target.value)}
          maxLength={100}
        />
      </Modal>
    </div>
  );
}