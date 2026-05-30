import { useEffect, useRef } from "react";
import { Card, Tag } from "antd";

interface Dialog {
  speaker: string;
  text: string;
  emotion?: string;
}

interface DialogBoxProps {
  narration: string;
  dialogs: Dialog[];
}

const emotionColors: Record<string, string> = {
  neutral: "default",
  happy: "success",
  sad: "error",
  angry: "warning",
  worried: "processing",
  scared: "error",
};

export function DialogBox({ narration, dialogs }: DialogBoxProps) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [narration, dialogs]);

  return (
    <div className="flex flex-col gap-2">
      {narration && (
        <Card
          className="border-none"
          style={{ background: "#2d3436", color: "#dfe6e9" }}
        >
          <p className="text-base leading-8 whitespace-pre-wrap">{narration}</p>
        </Card>
      )}

      {dialogs.map((d, i) => (
        <Card
          key={i}
          size="small"
          className="border-none"
          style={{ background: "#636e72", color: "#fff" }}
        >
          <div className="flex items-center gap-2 mb-1">
            <strong style={{ color: "#ffeaa7" }}>{d.speaker}</strong>
            {d.emotion && d.emotion !== "neutral" && (
              <Tag color={emotionColors[d.emotion] || "default"}>{d.emotion}</Tag>
            )}
          </div>
          <div>{d.text}</div>
        </Card>
      ))}

      <div ref={endRef} />
    </div>
  );
}
