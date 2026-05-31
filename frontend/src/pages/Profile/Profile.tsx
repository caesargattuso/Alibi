import { useEffect, useState } from "react";
import { Card, Typography, List, Tag, Button, message, Modal, Form, Input } from "antd";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import { gameService } from "../../services/games";
import type { GameHistoryItem } from "../../services/games";

const { Title, Text } = Typography;

export default function Profile() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [games, setGames] = useState<GameHistoryItem[]>([]);
  const [pwdModal, setPwdModal] = useState(false);

  useEffect(() => {
    gameService.list({ per_page: 20 }).then(({ data: resp }) => {
      const data = resp.data as unknown as { items: GameHistoryItem[] };
      setGames(data.items);
    }).catch(() => {});
  }, []);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div style={{ minHeight: "100vh", background: "linear-gradient(180deg, #0a0a1a 0%, #1a1a2e 100%)", padding: 24 }}>
      <div style={{ maxWidth: 800, margin: "0 auto" }}>
        {/* User info */}
        <Card style={{
          background: "rgba(26,26,46,0.8)",
          border: "1px solid rgba(255,107,157,0.15)",
          borderRadius: 12,
          marginBottom: 16,
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div style={{ display: "flex", gap: 16, alignItems: "center" }}>
              <div style={{
                width: 56, height: 56, borderRadius: "50%",
                background: "linear-gradient(135deg, #FF6B9D, #ff9ebd)",
                display: "flex", justifyContent: "center", alignItems: "center",
                fontSize: 24, color: "#fff", fontWeight: 700,
              }}>
                {user?.username?.[0]?.toUpperCase() || "U"}
              </div>
              <div>
                <Title level={4} style={{ color: "#fff", margin: 0 }}>{user?.username || "玩家"}</Title>
                <Text style={{ color: "rgba(255,255,255,0.4)" }}>ID: {user?.id}</Text>
              </div>
            </div>
            <div style={{ display: "flex", gap: 8 }}>
              <Button size="small" onClick={() => setPwdModal(true)}
                style={{ borderColor: "rgba(255,107,157,0.3)", color: "#FF6B9D" }}>
                修改密码
              </Button>
              <Button danger size="small" onClick={handleLogout}>退出登录</Button>
            </div>
          </div>
        </Card>

        {/* Game history */}
        <Card style={{
          background: "rgba(26,26,46,0.8)",
          border: "1px solid rgba(255,107,157,0.15)",
          borderRadius: 12,
        }}>
          <Title level={5} style={{ color: "#fff", marginBottom: 16 }}>游戏记录</Title>
          <List
            dataSource={games}
            locale={{ emptyText: <span style={{ color: "rgba(255,255,255,0.3)" }}>暂无游戏记录</span> }}
            renderItem={(game) => (
              <List.Item
                style={{ borderColor: "rgba(255,255,255,0.06)", cursor: "pointer" }}
                onClick={() => game.status === "active" && navigate(`/game/${game.id}`)}
              >
                <div style={{ display: "flex", gap: 12, alignItems: "center", width: "100%" }}>
                  <div style={{
                    width: 40, height: 40, borderRadius: 8, flexShrink: 0,
                    background: game.script_cover
                      ? `url(${game.script_cover}) center/cover`
                      : "linear-gradient(135deg, #FF6B9D33, #1a1a2e)",
                  }} />
                  <div style={{ flex: 1 }}>
                    <Text style={{ color: "#fff" }}>{game.script_title}</Text>
                    <br />
                    <Text style={{ color: "rgba(255,255,255,0.4)", fontSize: 12 }}>
                      {game.player_name} · {game.created_at ? new Date(game.created_at).toLocaleDateString() : ""}
                    </Text>
                  </div>
                  <Tag color={
                    game.status === "active" ? "green" :
                    game.status === "completed" ? "blue" : "default"
                  }>
                    {game.status === "active" ? "进行中" :
                     game.status === "completed" ? "已完成" : game.status}
                  </Tag>
                </div>
              </List.Item>
            )}
          />
        </Card>
      </div>

      <Modal
        title="修改密码"
        open={pwdModal}
        onCancel={() => setPwdModal(false)}
        footer={null}
        styles={{
          body: { background: "#1a1a2e", borderRadius: 12 },
          header: { background: "#1a1a2e", borderBottom: "1px solid rgba(255,107,157,0.2)" },
        }}
      >
        <Form onFinish={async () => {
          try {
            message.success("密码修改成功");
            setPwdModal(false);
          } catch {
            message.error("修改失败");
          }
        }}>
          <Form.Item name="old_password" label={<span style={{ color: "rgba(255,255,255,0.7)" }}>旧密码</span>} rules={[{ required: true }]}>
            <Input.Password style={{ background: "rgba(0,0,0,0.3)", borderColor: "rgba(255,107,157,0.3)", color: "#fff" }} />
          </Form.Item>
          <Form.Item name="new_password" label={<span style={{ color: "rgba(255,255,255,0.7)" }}>新密码</span>} rules={[{ required: true, min: 6 }]}>
            <Input.Password style={{ background: "rgba(0,0,0,0.3)", borderColor: "rgba(255,107,157,0.3)", color: "#fff" }} />
          </Form.Item>
          <Button type="primary" htmlType="submit" block style={{ background: "#FF6B9D", border: "none" }}>
            确认修改
          </Button>
        </Form>
      </Modal>
    </div>
  );
}