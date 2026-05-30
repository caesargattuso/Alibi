import { useEffect, useState } from "react";
import { Row, Col, Card, Typography, Tag } from "antd";
import { useNavigate } from "react-router-dom";
import { scriptService } from "../../services/scripts";
import type { Script } from "../../types";

const { Title, Text } = Typography;

export default function Home() {
  const navigate = useNavigate();
  const [scripts, setScripts] = useState<Script[]>([]);

  useEffect(() => {
    scriptService.list({ per_page: 8 }).then(({ data }) => {
      setScripts(data.data.items);
    });
  }, []);

  return (
    <div style={{ padding: "24px", background: "#FFF5F7", minHeight: "100vh" }}>
      <Title level={2}>热门剧本</Title>
      <Row gutter={[16, 16]}>
        {scripts.map((script) => (
          <Col key={script.id} xs={24} sm={12} md={8} lg={6}>
            <Card
              hoverable
              cover={
                <div
                  style={{
                    height: 200,
                    background: `url(${script.cover_image}) center/cover`,
                    backgroundColor: "#FFE0E9",
                  }}
                />
              }
              onClick={() => navigate(`/scripts/${script.id}`)}
            >
              <Title level={4}>{script.title}</Title>
              <Text>{script.description?.slice(0, 60)}...</Text>
              <div style={{ marginTop: 8 }}>
                <Tag color="pink">{script.genre}</Tag>
                <Tag>{script.difficulty}</Tag>
                <Text type="secondary">⭐ {script.rating} | {script.play_count}次游玩</Text>
              </div>
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  );
}