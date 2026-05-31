import { useState } from "react";
import type { Interactable } from "../../services/scenes";

interface InteractionMenuProps {
  interactable: Interactable;
  onAction: (actionId: string) => void;
  onClose: () => void;
}

export function InteractionMenu({ interactable, onAction, onClose }: InteractionMenuProps) {
  const [selectedAction, setSelectedAction] = useState<string | null>(null);

  const actionLabels: Record<string, string> = {
    examine: "调查",
    talk: "对话",
    touch: "触摸",
    enter: "进入",
    sit: "坐下",
    use: "使用",
    pick_up: "拾取",
    search: "搜索",
  };

  const handleAction = (actionId: string) => {
    setSelectedAction(actionId);
    onAction(actionId);
    onClose();
  };

  return (
    <div
      style={{
        position: "fixed",
        top: "50%",
        left: "50%",
        transform: "translate(-50%, -50%)",
        zIndex: 100,
        background: "rgba(10, 10, 26, 0.95)",
        backdropFilter: "blur(12px)",
        borderRadius: 16,
        padding: "24px",
        minWidth: 300,
        maxWidth: 400,
        border: "1px solid rgba(255, 107, 157, 0.3)",
      }}
    >
      {/* Header */}
      <div style={{ marginBottom: 16, textAlign: "center" }}>
        <div
          style={{
            width: 48,
            height: 48,
            borderRadius: "50%",
            background:
              interactable.type === "npc"
                ? "rgba(116, 185, 255, 0.2)"
                : interactable.type === "exit"
                  ? "rgba(85, 239, 196, 0.2)"
                  : "rgba(255, 234, 167, 0.2)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            margin: "0 auto 12px",
            fontSize: 24,
          }}
        >
          {interactable.type === "npc" ? "👤" : interactable.type === "exit" ? "🚪" : "📦"}
        </div>
        <h3 style={{ color: "#fff", fontSize: 18, fontWeight: 700, margin: 0 }}>
          {interactable.name}
        </h3>
        {interactable.description && (
          <p style={{ color: "#b2bec3", fontSize: 14, margin: "8px 0 0" }}>
            {interactable.description}
          </p>
        )}
      </div>

      {/* Actions */}
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {interactable.actions.map((action) => (
          <button
            key={action}
            onClick={() => handleAction(action)}
            disabled={selectedAction === action}
            style={{
              padding: "12px 16px",
              borderRadius: 10,
              background: "rgba(255, 107, 157, 0.15)",
              border: "1px solid rgba(255, 107, 157, 0.3)",
              color: "#fff",
              fontSize: 15,
              textAlign: "left",
              cursor: "pointer",
              transition: "all 0.2s",
            }}
          >
            <span style={{ color: "#FF6B9D", fontWeight: 700, marginRight: 8 }}>▸</span>
            {actionLabels[action] || action}
          </button>
        ))}
      </div>

      {/* Close button */}
      <button
        onClick={onClose}
        style={{
          marginTop: 16,
          width: "100%",
          padding: "10px",
          borderRadius: 8,
          background: "transparent",
          border: "1px solid rgba(255, 255, 255, 0.2)",
          color: "#b2bec3",
          fontSize: 14,
          cursor: "pointer",
        }}
      >
        取消
      </button>
    </div>
  );
}
