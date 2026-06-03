import { useState, useCallback } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  Button, Input, Select, Card, Form, message, Upload, Spin,
  Tag, Descriptions, Empty, Image,
} from "antd";
import {
  PlusOutlined, RobotOutlined, ArrowLeftOutlined,
  EnvironmentOutlined, UserOutlined, PictureOutlined,
  ThunderboltOutlined,
} from "@ant-design/icons";
import { scriptService } from "../../services/scripts";

const { TextArea } = Input;

interface GeneratedScene {
  scene_key: string;
  name: string;
  description: string;
  background_description: string;
  background_image_url?: string;
}

interface GeneratedCharacter {
  character_key: string;
  name: string;
  role_type: string;
  appearance: string;
  personality: string;
  background: string;
  dialogue_style: string;
  avatar_url?: string;
}

interface GeneratedData {
  script_id: number;
  script: {
    title: string;
    genre: string;
    difficulty: string;
    description: string;
    setting: Record<string, unknown>;
  };
  scenes: GeneratedScene[];
  characters: GeneratedCharacter[];
  cover_image_url: string | null;
}

const roleTypeColors: Record<string, string> = {
  主角: "#FF6B9D",
  嫌疑人: "#FF4D4F",
  受害者: "#8B8B8B",
  侦探: "#1890FF",
  证人: "#52C41A",
  其他: "#FAAD14",
};

export default function ScriptEditor() {
  const navigate = useNavigate();
  const { id: _id } = useParams<{ id: string }>();
  const [currentStep, setCurrentStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [scriptData, setScriptData] = useState({
    title: "",
    genre: "悬疑推理",
    difficulty: "normal",
    description: "",
    setting: {} as Record<string, unknown>,
    coverImage: "",
  });
  const [scenes, setScenes] = useState<GeneratedScene[]>([]);
  const [characters, setCharacters] = useState<GeneratedCharacter[]>([]);
  const [coverImageUrl, setCoverImageUrl] = useState<string | null>(null);

  const [scriptId, setScriptId] = useState<number | null>(null);

  const genres = [
    { value: "悬疑推理", label: "悬疑推理" },
    { value: "恐怖惊悚", label: "恐怖惊悚" },
    { value: "奇幻冒险", label: "奇幻冒险" },
    { value: "都市情感", label: "都市情感" },
    { value: "科幻未来", label: "科幻未来" },
  ];

  const difficulties = [
    { value: "easy", label: "简单" },
    { value: "normal", label: "中等" },
    { value: "hard", label: "困难" },
  ];

  const handleGenerateWithAI = useCallback(async () => {
    if (!scriptData.title || !scriptData.description) {
      message.warning("请先填写剧本标题和简介");
      return;
    }
    setGenerating(true);
    try {
      const res = await scriptService.generateWithAI({
        title: scriptData.title,
        genre: scriptData.genre,
        difficulty: scriptData.difficulty,
        description: scriptData.description,
      });
      const data = res.data.data as GeneratedData;

      setScriptId(data.script_id);
      setScriptData((prev) => ({
        ...prev,
        setting: data.script.setting,
        coverImage: data.cover_image_url || "",
      }));
      setScenes(data.scenes);
      setCharacters(data.characters);
      setCoverImageUrl(data.cover_image_url);

      message.success("AI生成完成！剧本已自动保存");
      setCurrentStep(1);
    } catch (error) {
      message.error("AI生成失败，请稍后重试");
      console.error("AI generation failed:", error);
    } finally {
      setGenerating(false);
    }
  }, [scriptData]);

  const handleSave = useCallback(async () => {
    if (scriptId) {
      message.success("剧本已保存");
      navigate(`/scripts/${scriptId}`);
      return;
    }
    if (!scriptData.title) {
      message.warning("请填写剧本标题");
      return;
    }
    setLoading(true);
    try {
      const res = await scriptService.create({
        title: scriptData.title,
        genre: scriptData.genre,
        difficulty: scriptData.difficulty,
        description: scriptData.description,
        setting: scriptData.setting,
        cover_image: scriptData.coverImage,
      });
      const newId = (res.data as { data: { id: number } }).data?.id;
      message.success("剧本保存成功");
      navigate(newId ? `/scripts/${newId}` : "/");
    } catch (error) {
      message.error("保存失败");
    } finally {
      setLoading(false);
    }
  }, [scriptData, scriptId, navigate]);

  const handleDeleteScene = (index: number) => {
    setScenes((prev) => prev.filter((_, i) => i !== index));
  };

  const handleDeleteCharacter = (index: number) => {
    setCharacters((prev) => prev.filter((_, i) => i !== index));
  };

  const stepLabels = ["基本信息", "场景设计", "角色设计", "交互点配置"];

  const steps = [
    {
      title: "基本信息",
      content: (
        <div style={{ display: "flex", gap: 24 }}>
          <Card
            title="剧本基本信息"
            style={{ flex: 1, background: "#1a1a2e", borderColor: "#333" }}
            styles={{ header: { color: "#fff", borderBottomColor: "#333" } }}
          >
            <Form layout="vertical">
              <Form.Item label={<span style={{ color: "#ccc" }}>剧本标题</span>} required>
                <Input
                  placeholder="输入剧本标题"
                  value={scriptData.title}
                  onChange={(e) => setScriptData({ ...scriptData, title: e.target.value })}
                  style={{ background: "#0a0a1a", borderColor: "#333", color: "#fff" }}
                />
              </Form.Item>
              <div style={{ display: "flex", gap: 16 }}>
                <Form.Item label={<span style={{ color: "#ccc" }}>剧本类型</span>} style={{ flex: 1 }}>
                  <Select
                    value={scriptData.genre}
                    onChange={(value) => setScriptData({ ...scriptData, genre: value })}
                    options={genres}
                    style={{ background: "#0a0a1a" }}
                  />
                </Form.Item>
                <Form.Item label={<span style={{ color: "#ccc" }}>难度</span>} style={{ flex: 1 }}>
                  <Select
                    value={scriptData.difficulty}
                    onChange={(value) => setScriptData({ ...scriptData, difficulty: value })}
                    options={difficulties}
                    style={{ background: "#0a0a1a" }}
                  />
                </Form.Item>
              </div>
              <Form.Item label={<span style={{ color: "#ccc" }}>剧本简介</span>}>
                <TextArea
                  rows={4}
                  placeholder="描述剧本的故事背景..."
                  value={scriptData.description}
                  onChange={(e) => setScriptData({ ...scriptData, description: e.target.value })}
                  style={{ background: "#0a0a1a", borderColor: "#333", color: "#fff" }}
                />
              </Form.Item>
              <Form.Item>
                <Button
                  type="primary"
                  icon={<ThunderboltOutlined />}
                  onClick={handleGenerateWithAI}
                  loading={generating}
                  size="large"
                  block
                  style={{
                    background: "linear-gradient(135deg, #FF6B9D, #C850C0)",
                    borderColor: "transparent",
                    height: 48,
                    fontSize: 16,
                  }}
                >
                  {generating ? "AI正在创作中..." : "AI一键生成剧本"}
                </Button>
              </Form.Item>
            </Form>
          </Card>

          {coverImageUrl && (
            <Card
              title="封面预览"
              style={{ width: 280, background: "#1a1a2e", borderColor: "#333" }}
              styles={{ header: { color: "#fff", borderBottomColor: "#333" } }}
            >
              <Image
                src={coverImageUrl}
                alt="封面"
                style={{ width: "100%", borderRadius: 8 }}
                fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mN88P/BfwAJhAPk2iMa1AAAAABJRU5ErkJggg=="
              />
              <Upload
                listType="picture-card"
                showUploadList={false}
                style={{ marginTop: 12, width: "100%" }}
              >
                <div style={{ color: "#999" }}>
                  <PlusOutlined /> 更换封面
                </div>
              </Upload>
            </Card>
          )}
        </div>
      ),
    },
    {
      title: "场景设计",
      content: (
        <Card
          title="场景设计"
          style={{ background: "#1a1a2e", borderColor: "#333" }}
          styles={{ header: { color: "#fff", borderBottomColor: "#333" } }}
          extra={
            <Button type="primary" icon={<PlusOutlined />} onClick={() => {}}>
              添加场景
            </Button>
          }
        >
          {scenes.length === 0 ? (
            <Empty
              description={<span style={{ color: "#666" }}>暂无场景，请先使用AI生成或手动添加</span>}
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 16 }}>
              {scenes.map((scene, index) => (
                <Card
                  key={scene.scene_key}
                  style={{ background: "#0a0a1a", borderColor: "#2a2a4a" }}
                  styles={{ header: { color: "#fff", borderBottomColor: "#2a2a4a" } }}
                  title={
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <EnvironmentOutlined style={{ color: "#FF6B9D" }} />
                      <span>{scene.name}</span>
                      <Tag color="#2a2a4a" style={{ marginLeft: "auto" }}>{scene.scene_key}</Tag>
                    </div>
                  }
                  extra={
                    <Button type="link" danger size="small" onClick={() => handleDeleteScene(index)}>
                      删除
                    </Button>
                  }
                >
                  <p style={{ color: "#bbb", margin: 0 }}>{scene.description}</p>
                  {scene.background_description && (
                    <div style={{ marginTop: 8, padding: "8px 12px", background: "#111", borderRadius: 6 }}>
                      <PictureOutlined style={{ color: "#666", marginRight: 6 }} />
                      <span style={{ color: "#666", fontSize: 12 }}>{scene.background_description}</span>
                    </div>
                  )}
                </Card>
              ))}
            </div>
          )}
        </Card>
      ),
    },
    {
      title: "角色设计",
      content: (
        <Card
          title="角色设计"
          style={{ background: "#1a1a2e", borderColor: "#333" }}
          styles={{ header: { color: "#fff", borderBottomColor: "#333" } }}
          extra={
            <Button type="primary" icon={<PlusOutlined />} onClick={() => {}}>
              添加角色
            </Button>
          }
        >
          {characters.length === 0 ? (
            <Empty
              description={<span style={{ color: "#666" }}>暂无角色，请先使用AI生成或手动添加</span>}
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              {characters.map((char, index) => (
                <Card
                  key={char.character_key}
                  style={{ background: "#0a0a1a", borderColor: "#2a2a4a" }}
                  styles={{ header: { color: "#fff", borderBottomColor: "#2a2a4a" } }}
                  title={
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <UserOutlined style={{ color: roleTypeColors[char.role_type] || "#FAAD14" }} />
                      <span>{char.name}</span>
                      <Tag color={roleTypeColors[char.role_type] || "#FAAD14"}>{char.role_type}</Tag>
                      <Tag color="#2a2a4a" style={{ marginLeft: "auto" }}>{char.character_key}</Tag>
                    </div>
                  }
                  extra={
                    <Button type="link" danger size="small" onClick={() => handleDeleteCharacter(index)}>
                      删除
                    </Button>
                  }
                >
                  <Descriptions
                    column={1}
                    size="small"
                    labelStyle={{ color: "#888" }}
                    contentStyle={{ color: "#ccc" }}
                  >
                    <Descriptions.Item label="外观">{char.appearance}</Descriptions.Item>
                    <Descriptions.Item label="性格">{char.personality}</Descriptions.Item>
                    <Descriptions.Item label="背景">{char.background}</Descriptions.Item>
                    <Descriptions.Item label="对话风格">{char.dialogue_style}</Descriptions.Item>
                  </Descriptions>
                </Card>
              ))}
            </div>
          )}
        </Card>
      ),
    },
    {
      title: "交互点配置",
      content: (
        <Card
          title="交互点配置"
          style={{ background: "#1a1a2e", borderColor: "#333" }}
          styles={{ header: { color: "#fff", borderBottomColor: "#333" } }}
        >
          <Empty
            description={<span style={{ color: "#666" }}>交互点配置功能开发中，敬请期待</span>}
          />
        </Card>
      ),
    },
  ];

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "linear-gradient(180deg, #0a0a1a 0%, #1a1a2e 40%, #16213e 100%)",
        padding: "24px",
      }}
    >
      <div style={{ maxWidth: 1200, margin: "0 auto" }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: 24,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <Button
              icon={<ArrowLeftOutlined />}
              onClick={() => navigate("/")}
              type="text"
              style={{ color: "#999" }}
            />
            <h1 style={{ color: "#fff", margin: 0 }}>AI剧本创作</h1>
          </div>
          <div style={{ display: "flex", gap: 12 }}>
            <Button
              icon={<RobotOutlined />}
              onClick={handleGenerateWithAI}
              loading={generating}
              style={{ background: "#FF6B9D", borderColor: "#FF6B9D", color: "#fff" }}
            >
              AI辅助生成
            </Button>
            <Button
              type="primary"
              onClick={handleSave}
              loading={loading}
              style={{
                background: "linear-gradient(135deg, #1890FF, #096DD9)",
                borderColor: "transparent",
              }}
            >
              保存剧本
            </Button>
          </div>
        </div>

        <div style={{ marginBottom: 24 }}>
          <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
            {stepLabels.map((step, idx) => (
              <Button
                key={step}
                type={currentStep === idx ? "primary" : "default"}
                onClick={() => setCurrentStep(idx)}
                style={
                  currentStep === idx
                    ? { background: "#FF6B9D", borderColor: "#FF6B9D" }
                    : { background: "#1a1a2e", borderColor: "#333", color: "#999" }
                }
              >
                {step}
                {idx === 1 && scenes.length > 0 && (
                  <Tag color="#FF6B9D" style={{ marginLeft: 6 }}>{scenes.length}</Tag>
                )}
                {idx === 2 && characters.length > 0 && (
                  <Tag color="#1890FF" style={{ marginLeft: 6 }}>{characters.length}</Tag>
                )}
              </Button>
            ))}
          </div>
        </div>

        {generating ? (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              minHeight: 400,
              gap: 16,
            }}
          >
            <Spin size="large" />
            <p style={{ color: "#FF6B9D", fontSize: 16 }}>
              <RobotOutlined /> AI正在创作剧本...
            </p>
            <p style={{ color: "#666", fontSize: 13 }}>
              正在生成世界观、场景、角色和封面图片，请稍候
            </p>
          </div>
        ) : (
          <div style={{ marginBottom: 24 }}>{steps[currentStep].content}</div>
        )}

        <div style={{ display: "flex", justifyContent: "space-between" }}>
          <Button
            disabled={currentStep === 0}
            onClick={() => setCurrentStep(currentStep - 1)}
            style={{ background: "#1a1a2e", borderColor: "#333", color: "#999" }}
          >
            上一步
          </Button>
          <Button
            type="primary"
            disabled={currentStep === steps.length - 1}
            onClick={() => setCurrentStep(currentStep + 1)}
            style={{ background: "#FF6B9D", borderColor: "#FF6B9D" }}
          >
            下一步
          </Button>
        </div>
      </div>
    </div>
  );
}
