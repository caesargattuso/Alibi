import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Form, Input, Button, Card, message } from "antd";
import { authService } from "../../services/auth";
import { useAuthStore } from "../../stores/authStore";

export default function Login() {
  const navigate = useNavigate();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [loading, setLoading] = useState(false);

  const onFinish = async (values: { username_or_email: string; password: string }) => {
    setLoading(true);
    try {
      const { data } = await authService.login(values);
      setAuth(data.data.access_token, data.data.refresh_token, {
        id: data.data.user_id,
        username: data.data.username,
        avatar_url: data.data.avatar_url,
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
    <div style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "100vh", background: "#FFF5F7" }}>
      <Card title="登录" style={{ width: 400 }}>
        <Form onFinish={onFinish} layout="vertical">
          <Form.Item name="username_or_email" label="用户名/邮箱" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="password" label="密码" rules={[{ required: true }]}>
            <Input.Password />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block>
              登录
            </Button>
          </Form.Item>
          <Button type="link" onClick={() => navigate("/register")}>
            没有账号？去注册
          </Button>
        </Form>
      </Card>
    </div>
  );
}