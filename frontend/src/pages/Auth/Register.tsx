import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Form, Input, Button, Card, message, Typography } from "antd";
import { authService } from "../../services/auth";
import { useAuthStore } from "../../stores/authStore";

const { Title } = Typography;

export default function Register() {
  const navigate = useNavigate();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [loading, setLoading] = useState(false);

  const onFinish = async (values: { username: string; email: string; password: string }) => {
    setLoading(true);
    try {
      const { data: resp } = await authService.register(values);
      const d = resp.data as Record<string, unknown>;
      setAuth(d.access_token as string, d.refresh_token as string, {
        id: d.user_id as number,
        username: d.username as string,
        avatar_url: null,
      });
      message.success("注册成功");
      navigate("/");
    } catch {
      message.error("注册失败");
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
        <div style={{ color: "rgba(255,255,255,0.4)", fontSize: 14 }}>创建你的冒险者身份</div>
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
          <Form.Item name="username" label={<span style={{ color: "rgba(255,255,255,0.7)" }}>用户名</span>} rules={[{ required: true, min: 3, max: 50 }]}>
            <Input style={{ background: "rgba(0,0,0,0.3)", borderColor: "rgba(255,107,157,0.3)", color: "#fff" }} />
          </Form.Item>
          <Form.Item name="email" label={<span style={{ color: "rgba(255,255,255,0.7)" }}>邮箱</span>} rules={[{ required: true, type: "email" }]}>
            <Input style={{ background: "rgba(0,0,0,0.3)", borderColor: "rgba(255,107,157,0.3)", color: "#fff" }} />
          </Form.Item>
          <Form.Item name="password" label={<span style={{ color: "rgba(255,255,255,0.7)" }}>密码</span>} rules={[{ required: true, min: 6, max: 20 }]}>
            <Input.Password style={{ background: "rgba(0,0,0,0.3)", borderColor: "rgba(255,107,157,0.3)", color: "#fff" }} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block
              style={{ height: 44, borderRadius: 10, background: "#FF6B9D", border: "none", fontSize: 16 }}>
              注册
            </Button>
          </Form.Item>
          <Button type="link" onClick={() => navigate("/login")} style={{ color: "#FF6B9D" }}>
            已有账号？去登录
          </Button>
        </Form>
      </Card>
    </div>
  );
}