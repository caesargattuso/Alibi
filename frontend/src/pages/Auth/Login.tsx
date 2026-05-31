import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Form, Input, Button, Card, message, Typography } from "antd";
import { authService } from "../../services/auth";
import { useAuthStore } from "../../stores/authStore";

const { Title } = Typography;

export default function Login() {
  const navigate = useNavigate();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [loading, setLoading] = useState(false);

  const onFinish = async (values: { username_or_email: string; password: string }) => {
    setLoading(true);
    try {
      const { data: resp } = await authService.login(values);
      const d = resp.data as Record<string, unknown>;
      setAuth(d.access_token as string, d.refresh_token as string, {
        id: d.user_id as number,
        username: d.username as string,
        avatar_url: (d.avatar_url as string) || null,
      });
      message.success("登录成功");
      navigate("/");
    } catch {
      message.error("登录失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      display: "flex", justifyContent: "center", alignItems: "center", minHeight: "100vh",
      background: "linear-gradient(135deg, #0a0a1a 0%, #1a1a2e 50%, #16213e 100%)",
    }}>
      <div style={{ textAlign: "center", marginBottom: 32 }}>
        <Title level={2} style={{ color: "#fff" }}>
          <span style={{ color: "#FF6B9D" }}>Alibi</span> 无限流
        </Title>
        <div style={{ color: "rgba(255,255,255,0.4)", fontSize: 14 }}>AI驱动的互动叙事游戏平台</div>
      </div>

      <Card style={{
        width: 400,
        background: "rgba(26,26,46,0.8)",
        border: "1px solid rgba(255,107,157,0.2)",
        borderRadius: 16,
      }}
      styles={{
        header: { background: "transparent", borderBottom: "1px solid rgba(255,107,157,0.15)", color: "#fff" },
        body: { color: "#fff" },
      }}
      >
        <Form onFinish={onFinish} layout="vertical">
          <Form.Item name="username_or_email" label={<span style={{ color: "rgba(255,255,255,0.7)" }}>用户名/邮箱</span>} rules={[{ required: true }]}>
            <Input style={{ background: "rgba(0,0,0,0.3)", borderColor: "rgba(255,107,157,0.3)", color: "#fff" }} />
          </Form.Item>
          <Form.Item name="password" label={<span style={{ color: "rgba(255,255,255,0.7)" }}>密码</span>} rules={[{ required: true }]}>
            <Input.Password style={{ background: "rgba(0,0,0,0.3)", borderColor: "rgba(255,107,157,0.3)", color: "#fff" }} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block
              style={{ height: 44, borderRadius: 10, background: "#FF6B9D", border: "none", fontSize: 16 }}>
              登录
            </Button>
          </Form.Item>
          <Button type="link" onClick={() => navigate("/register")} style={{ color: "#FF6B9D" }}>
            没有账号？去注册
          </Button>
        </Form>
      </Card>
    </div>
  );
}