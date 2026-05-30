import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Form, Input, Button, Card, message } from "antd";
import { authService } from "../../services/auth";
import { useAuthStore } from "../../stores/authStore";

export default function Register() {
  const navigate = useNavigate();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [loading, setLoading] = useState(false);

  const onFinish = async (values: { username: string; email: string; password: string }) => {
    setLoading(true);
    try {
      const { data } = await authService.register(values);
      setAuth(data.data.access_token, data.data.refresh_token, {
        id: data.data.user_id,
        username: data.data.username,
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
    <div style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "100vh", background: "#FFF5F7" }}>
      <Card title="注册" style={{ width: 400 }}>
        <Form onFinish={onFinish} layout="vertical">
          <Form.Item name="username" label="用户名" rules={[{ required: true, min: 3, max: 50 }]}>
            <Input />
          </Form.Item>
          <Form.Item name="email" label="邮箱" rules={[{ required: true, type: "email" }]}>
            <Input />
          </Form.Item>
          <Form.Item name="password" label="密码" rules={[{ required: true, min: 6, max: 20 }]}>
            <Input.Password />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block>
              注册
            </Button>
          </Form.Item>
          <Button type="link" onClick={() => navigate("/login")}>
            已有账号？去登录
          </Button>
        </Form>
      </Card>
    </div>
  );
}