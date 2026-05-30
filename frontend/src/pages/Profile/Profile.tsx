import { useEffect, useState } from "react";
import { Card, Tabs, List, Avatar, Button, Modal, Form, Input, message, Tag, Empty } from "antd";
import { useAuth } from "../../hooks/useAuth";
import { userService } from "../../services/auth";
import { gameService, type GameHistoryItem } from "../../services/games";

export function Profile() {
  const { user, fetchMe } = useAuth();
  const [history, setHistory] = useState<GameHistoryItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pwdModalOpen, setPwdModalOpen] = useState(false);
  const [pwdForm] = Form.useForm();

  useEffect(() => { fetchMe(); }, [fetchMe]);

  const loadHistory = async (p: number) => {
    const { data } = await gameService.list({ page: p, per_page: 10 });
    setHistory(data.data.items);
    setTotal(data.data.total);
    setPage(p);
  };

  useEffect(() => { loadHistory(1); }, []);

  const handlePasswordChange = async (values: { old_password: string; new_password: string }) => {
    try {
      await userService.changePassword(values);
      message.success("密码修改成功");
      setPwdModalOpen(false);
      pwdForm.resetFields();
    } catch {
      message.error("密码修改失败");
    }
  };

  const statusColors: Record<string, string> = {
    active: "processing",
    completed: "success",
    paused: "warning",
    abandoned: "default",
  };

  const statusLabels: Record<string, string> = {
    active: "进行中",
    completed: "已完成",
    paused: "已暂停",
    abandoned: "已放弃",
  };

  return (
    <div className="max-w-3xl mx-auto p-4">
      <Card className="border-none mb-4">
        <div className="flex items-center gap-4">
          <Avatar size={64} src={user?.avatar_url} style={{ backgroundColor: "#FF6B9D" }}>
            {user?.username?.[0]?.toUpperCase()}
          </Avatar>
          <div className="flex-1">
            <h2 className="text-xl font-bold m-0">{user?.username}</h2>
            <p className="text-gray-500 text-sm m-0">ID: {user?.id}</p>
          </div>
          <Button onClick={() => setPwdModalOpen(true)}>修改密码</Button>
        </div>
      </Card>

      <Card className="border-none">
        <Tabs
          items={[
            {
              key: "history",
              label: "游戏历史",
              children: (
                <List
                  dataSource={history}
                  locale={{ emptyText: <Empty description="暂无游戏记录" /> }}
                  renderItem={(item) => (
                    <List.Item>
                      <div className="flex items-center gap-3 w-full">
                        {item.script_cover && (
                          <img src={item.script_cover} alt="" className="w-12 h-16 object-cover rounded" />
                        )}
                        <div className="flex-1">
                          <div className="font-medium">{item.script_title}</div>
                          <div className="text-sm text-gray-500">
                            {item.player_name && `角色: ${item.player_name}`}
                            {item.current_ending && ` | 结局: ${item.current_ending}`}
                          </div>
                          <div className="text-xs text-gray-400">
                            {item.created_at?.slice(0, 10)}
                          </div>
                        </div>
                        <Tag color={statusColors[item.status]}>
                          {statusLabels[item.status] || item.status}
                        </Tag>
                      </div>
                    </List.Item>
                  )}
                  pagination={{
                    current: page,
                    total,
                    pageSize: 10,
                    onChange: loadHistory,
                    size: "small",
                  }}
                />
              ),
            },
          ]}
        />
      </Card>

      <Modal
        title="修改密码"
        open={pwdModalOpen}
        onCancel={() => setPwdModalOpen(false)}
        footer={null}
      >
        <Form form={pwdForm} onFinish={handlePasswordChange} layout="vertical">
          <Form.Item name="old_password" label="旧密码" rules={[{ required: true, min: 6 }]}>
            <Input.Password />
          </Form.Item>
          <Form.Item name="new_password" label="新密码" rules={[{ required: true, min: 6 }]}>
            <Input.Password />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block>确认修改</Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
