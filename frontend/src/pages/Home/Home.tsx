import { useEffect, useState } from "react";
import { Row, Col, Card, Typography, Tag, Button } from "antd";
import { useNavigate } from "react-router-dom";
import { scriptService } from "../../services/scripts";
import { gameService } from "../../services/games";
import type { Script } from "../../types";

const { Title, Text, Paragraph } = Typography;

const GENRE_FILTERS = ["全部", "悬疑推理", "恐怖惊悚", "奇幻冒险", "都市情感", "科幻未来"];

export default function Home() {
  const navigate = useNavigate();
  const [scripts, setScripts] = useState<Script[]>([]);
  const [activeGames, setActiveGames] = useState<Array<{ id: number; script_title: string; script_cover: string | null; player_name: string | null }>>([]);
  const [selectedGenre, setSelectedGenre] = useState("全部");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    scriptService.list({ per_page: 12 }).then(({ data: resp }) => {
      setScripts((resp.data as unknown as { items: Script[] }).items);
    }).finally(() => setLoading(false));

    gameService.list({ per_page: 3, status: "active" }).then(({ data: resp }) => {
      const data = resp.data as unknown as { items: Array<{ id: number; script_title: string; script_cover: string | null; player_name: string | null }> };
      setActiveGames(data.items);
    }).catch(() => {});
  }, []);

  const filteredScripts = selectedGenre === "全部"
    ? scripts
    : scripts.filter((s) => s.genre === selectedGenre);

  return (
    <div style={{ minHeight: "100vh", background: "linear-gradient(180deg, #0a0a1a 0%, #1a1a2e 40%, #16213e 100%)" }}>
      {/* Hero section */}
      <div style={{
        padding: "60px 24px 40px",
        textAlign: "center",
        position: "relative",
        overflow: "hidden",
      }}>
        <div style={{
          position: "absolute", inset: 0,
          background: "radial-gradient(ellipse at 50% 0%, rgba(255,107,157,0.15) 0%, transparent 70%)",
        }} />
        <Title level={1} style={{ color: "#fff", fontSize: 42, marginBottom: 8, position: "relative" }}>
          <span style={{ color: "#FF6B9D" }}>Alibi</span> 无限流
        </Title>
        <Paragraph style={{ color: "rgba(255,255,255,0.6)", fontSize: 18, position: "relative" }}>
          AI驱动的互动叙事游戏平台
        </Paragraph>
        <div style={{ display: "flex", justifyContent: "center", gap: 24, marginTop: 16, position: "relative" }}>
          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: 28, fontWeight: 700, color: "#FF6B9D" }}>{scripts.length}</div>
            <div style={{ color: "rgba(255,255,255,0.5)", fontSize: 13 }}>剧本</div>
          </div>
          <div style={{ width: 1, background: "rgba(255,255,255,0.1)" }} />
          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: 28, fontWeight: 700, color: "#FF6B9D" }}>∞</div>
            <div style={{ color: "rgba(255,255,255,0.5)", fontSize: 13 }}>可能</div>
          </div>
          <div style={{ width: 1, background: "rgba(255,255,255,0.1)" }} />
          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: 28, fontWeight: 700, color: "#FF6B9D" }}>AI</div>
            <div style={{ color: "rgba(255,255,255,0.5)", fontSize: 13 }}>叙事</div>
          </div>
        </div>
      </div>

      <div style={{ maxWidth: 1200, margin: "0 auto", padding: "0 24px 40px" }}>
        {/* Continue playing */}
        {activeGames.length > 0 && (
          <>
            <Title level={4} style={{ color: "#fff", marginBottom: 16 }}>
              <span style={{ marginRight: 8 }}>▶</span> 继续游戏
            </Title>
            <Row gutter={[16, 16]} style={{ marginBottom: 32 }}>
              {activeGames.map((game) => (
                <Col key={game.id} xs={24} sm={12} md={8}>
                  <Card
                    hoverable
                    style={{
                      background: "rgba(255,107,157,0.08)",
                      border: "1px solid rgba(255,107,157,0.2)",
                      borderRadius: 12,
                    }}
                    onClick={() => navigate(`/game/${game.id}`)}
                  >
                    <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
                      <div style={{
                        width: 48, height: 48, borderRadius: 8,
                        background: game.script_cover ? `url(${game.script_cover}) center/cover` : "linear-gradient(135deg, #FF6B9D, #ff9ebd)",
                        flexShrink: 0,
                      }} />
                      <div>
                        <Text style={{ color: "#fff", fontWeight: 600 }}>{game.script_title}</Text>
                        <br />
                        <Text style={{ color: "rgba(255,255,255,0.5)", fontSize: 13 }}>
                          {game.player_name} · 进行中
                        </Text>
                      </div>
                    </div>
                  </Card>
                </Col>
              ))}
            </Row>
          </>
        )}

        {/* Genre filters */}
        <div style={{ display: "flex", gap: 8, marginBottom: 24, flexWrap: "wrap" }}>
          {GENRE_FILTERS.map((genre) => (
            <Button
              key={genre}
              size="small"
              type={selectedGenre === genre ? "primary" : "default"}
              onClick={() => setSelectedGenre(genre)}
              style={{
                borderRadius: 20, fontSize: 13,
                background: selectedGenre === genre ? "#FF6B9D" : "rgba(255,255,255,0.08)",
                borderColor: selectedGenre === genre ? "#FF6B9D" : "rgba(255,255,255,0.15)",
                color: selectedGenre === genre ? "#fff" : "rgba(255,255,255,0.7)",
              }}
            >
              {genre}
            </Button>
          ))}
        </div>

        {/* Script grid */}
        <Title level={4} style={{ color: "#fff", marginBottom: 16 }}>
          <span style={{ marginRight: 8 }}>🔥</span> 热门剧本
        </Title>

        {loading ? (
          <Row gutter={[16, 16]}>
            {[1, 2, 3, 4].map((i) => (
              <Col key={i} xs={24} sm={12} md={8} lg={6}>
                <div className="skeleton" style={{ height: 280, borderRadius: 12 }} />
              </Col>
            ))}
          </Row>
        ) : (
          <Row gutter={[16, 16]}>
            {filteredScripts.map((script) => (
              <Col key={script.id} xs={24} sm={12} md={8} lg={6}>
                <Card
                  hoverable
                  style={{
                    background: "rgba(26,26,46,0.8)",
                    border: "1px solid rgba(255,107,157,0.15)",
                    borderRadius: 12,
                    overflow: "hidden",
                  }}
                  styles={{ body: { padding: 16 } }}
                  cover={
                    <div style={{
                      height: 180, position: "relative", overflow: "hidden",
                      background: script.cover_image
                        ? `url(${script.cover_image}) center/cover`
                        : "linear-gradient(135deg, #1a1a2e, #FF6B9D33)",
                    }}>
                      <div style={{
                        position: "absolute", bottom: 0, left: 0, right: 0, height: 60,
                        background: "linear-gradient(transparent, rgba(26,26,46,0.9))",
                      }} />
                      <Tag color="pink" style={{ position: "absolute", top: 8, left: 8 }}>
                        {script.genre}
                      </Tag>
                    </div>
                  }
                  onClick={() => navigate(`/scripts/${script.id}`)}
                >
                  <Title level={5} style={{ color: "#fff", margin: "0 0 8px" }}>{script.title}</Title>
                  <Paragraph
                    ellipsis={{ rows: 2 }}
                    style={{ color: "rgba(255,255,255,0.5)", fontSize: 13, margin: 0, marginBottom: 12 }}
                  >
                    {script.description}
                  </Paragraph>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <Tag style={{
                      background: "rgba(255,255,255,0.08)",
                      borderColor: "rgba(255,255,255,0.15)",
                      color: "rgba(255,255,255,0.7)",
                    }}>
                      {script.difficulty}
                    </Tag>
                    <Text style={{ color: "rgba(255,255,255,0.4)", fontSize: 12 }}>
                      ⭐ {script.rating} · {script.play_count}次
                    </Text>
                  </div>
                </Card>
              </Col>
            ))}
          </Row>
        )}

        {filteredScripts.length === 0 && !loading && (
          <div style={{ textAlign: "center", padding: 40, color: "rgba(255,255,255,0.4)" }}>
            暂无该类型剧本
          </div>
        )}
      </div>
    </div>
  );
}