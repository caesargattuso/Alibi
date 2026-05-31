import { useState, useRef, useEffect } from "react";
import { Input, Spin } from "antd";
import { SendOutlined } from "@ant-design/icons";
import type { Interactable } from "../../services/scenes";

interface DialogueMessage {
  id: string;
  speaker: "player" | "npc";
  text: string;
  emotion?: string;
}

interface NPCDialogueProps {
  interactable: Interactable;
  sessionId: number;
  onClose: () => void;
  onTalkComplete?: (context: string) => void;
}

export function NPCDialogue({ interactable, onClose, onTalkComplete }: NPCDialogueProps) {
  const [messages, setMessages] = useState<DialogueMessage[]>([]);
  const [inputText, setInputText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [npcEmotion, setNpcEmotion] = useState("neutral");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Initial greeting
  useEffect(() => {
    const initialMessage: DialogueMessage = {
      id: "initial",
      speaker: "npc",
      text: interactable.description || `你好，我是${interactable.name}。有什么我可以帮你的吗？`,
      emotion: "neutral",
    };
    setMessages([initialMessage]);
  }, [interactable]);

  const handleSendMessage = async () => {
    if (!inputText.trim() || isLoading) return;

    const playerMessage: DialogueMessage = {
      id: Date.now().toString(),
      speaker: "player",
      text: inputText.trim(),
    };

    setMessages((prev) => [...prev, playerMessage]);
    setInputText("");
    setIsLoading(true);

    try {
      // Simulate AI response (will be replaced with real API call)
      await new Promise((resolve) => setTimeout(resolve, 1000));

      const npcResponse = getNPCResponse(inputText.trim(), interactable);
      const npcMessage: DialogueMessage = {
        id: (Date.now() + 1).toString(),
        speaker: "npc",
        text: npcResponse.text,
        emotion: npcResponse.emotion,
      };

      setMessages((prev) => [...prev, npcMessage]);
      setNpcEmotion(npcResponse.emotion);

      // Trigger completion callback
      if (onTalkComplete) {
        onTalkComplete(`与${interactable.name}对话：${inputText.trim()}`);
      }
    } catch (error) {
      console.error("Dialogue error:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const getNPCResponse = (_playerText: string, _npc: Interactable): { text: string; emotion: string } => {
    // Simple response logic - will be replaced with AI
    const responses = [
      { text: "这确实是个有趣的发现。让我想想...", emotion: "thinking" },
      { text: "你在说什么？我不明白你的意思。", emotion: "confused" },
      { text: "哼，这件事我可不能随便告诉你。", emotion: "suspicious" },
      { text: "啊！你怎么知道这个的？", emotion: "surprised" },
      { text: "没错，就是这样。你果然很敏锐。", emotion: "happy" },
    ];
    return responses[Math.floor(Math.random() * responses.length)];
  };

  const getEmotionIcon = (emotion?: string) => {
    const icons: Record<string, string> = {
      neutral: "😐",
      happy: "😊",
      sad: "😢",
      angry: "😠",
      worried: "😟",
      scared: "😨",
      thinking: "🤔",
      confused: "😕",
      suspicious: "🤨",
      surprised: "😮",
    };
    return icons[emotion || "neutral"] || "😐";
  };

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 200,
        display: "flex",
        alignItems: "flex-end",
        justifyContent: "center",
        background: "rgba(0, 0, 0, 0.7)",
        padding: "20px",
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: 800,
          background: "rgba(10, 10, 26, 0.95)",
          backdropFilter: "blur(12px)",
          borderRadius: 16,
          border: "1px solid rgba(255, 107, 157, 0.3)",
          overflow: "hidden",
          display: "flex",
          flexDirection: "column",
          maxHeight: "70vh",
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: "16px 20px",
            borderBottom: "1px solid rgba(255, 107, 157, 0.2)",
            display: "flex",
            alignItems: "center",
            gap: 12,
          }}
        >
          <div
            style={{
              width: 40,
              height: 40,
              borderRadius: "50%",
              background: "rgba(116, 185, 255, 0.2)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 20,
            }}
          >
            {interactable.icon && interactable.icon.startsWith("/") ? (
              <img
                src={interactable.icon}
                alt={interactable.name}
                style={{ width: "100%", height: "100%", borderRadius: "50%", objectFit: "cover" }}
              />
            ) : (
              "👤"
            )}
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ color: "#fff", fontSize: 16, fontWeight: 700 }}>{interactable.name}</div>
            <div style={{ color: "#888", fontSize: 12 }}>
              {interactable.description?.slice(0, 50)}...
            </div>
          </div>
          <div style={{ fontSize: 24 }}>{getEmotionIcon(npcEmotion)}</div>
          <button
            onClick={onClose}
            style={{
              background: "none",
              border: "none",
              color: "#888",
              fontSize: 20,
              cursor: "pointer",
              padding: "4px 8px",
            }}
          >
            ✕
          </button>
        </div>

        {/* Messages */}
        <div
          style={{
            flex: 1,
            overflow: "auto",
            padding: "16px 20px",
            display: "flex",
            flexDirection: "column",
            gap: 12,
          }}
        >
          {messages.map((msg) => (
            <div
              key={msg.id}
              style={{
                alignSelf: msg.speaker === "player" ? "flex-end" : "flex-start",
                maxWidth: "80%",
              }}
            >
              <div
                style={{
                  padding: "10px 14px",
                  borderRadius: msg.speaker === "player" ? "12px 12px 2px 12px" : "12px 12px 12px 2px",
                  background:
                    msg.speaker === "player"
                      ? "rgba(255, 107, 157, 0.2)"
                      : "rgba(116, 185, 255, 0.15)",
                  border: `1px solid ${
                    msg.speaker === "player" ? "rgba(255, 107, 157, 0.3)" : "rgba(116, 185, 255, 0.3)"
                  }`,
                  color: "#dfe6e9",
                  fontSize: 14,
                  lineHeight: 1.6,
                }}
              >
                {msg.text}
              </div>
              {msg.emotion && (
                <div style={{ fontSize: 10, color: "#888", marginTop: 4, textAlign: "right" }}>
                  {getEmotionIcon(msg.emotion)}
                </div>
              )}
            </div>
          ))}
          {isLoading && (
            <div style={{ alignSelf: "flex-start", padding: "8px 12px" }}>
              <Spin size="small" />
              <span style={{ color: "#888", marginLeft: 8, fontSize: 12 }}>对方正在输入...</span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div
          style={{
            padding: "12px 20px",
            borderTop: "1px solid rgba(255, 107, 157, 0.2)",
            display: "flex",
            gap: 8,
          }}
        >
          <Input
            placeholder="输入你想说的话..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onPressEnter={handleSendMessage}
            disabled={isLoading}
            style={{
              flex: 1,
              background: "rgba(0, 0, 0, 0.3)",
              borderColor: "rgba(255, 107, 157, 0.3)",
              color: "#fff",
              borderRadius: 8,
            }}
          />
          <button
            onClick={handleSendMessage}
            disabled={isLoading || !inputText.trim()}
            style={{
              padding: "8px 16px",
              borderRadius: 8,
              background: "rgba(255, 107, 157, 0.2)",
              border: "1px solid rgba(255, 107, 157, 0.3)",
              color: "#fff",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: 4,
              opacity: isLoading || !inputText.trim() ? 0.5 : 1,
            }}
          >
            <SendOutlined />
            发送
          </button>
        </div>
      </div>
    </div>
  );
}
