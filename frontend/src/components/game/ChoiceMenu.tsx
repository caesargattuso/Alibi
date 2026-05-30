import { Button, Input } from "antd";
import { useState } from "react";

interface Choice {
  id: string;
  text: string;
  is_custom?: boolean;
}

interface ChoiceMenuProps {
  choices: Choice[];
  isLoading: boolean;
  onChoice: (choiceId: string) => void;
  onCustomInput: (text: string) => void;
}

export function ChoiceMenu({ choices, isLoading, onChoice, onCustomInput }: ChoiceMenuProps) {
  const [customText, setCustomText] = useState("");

  const handleCustomSubmit = () => {
    if (!customText.trim()) return;
    onCustomInput(customText);
    setCustomText("");
  };

  if (isLoading) return null;

  return (
    <div className="flex flex-col gap-1 p-2" style={{ background: "#2d3436" }}>
      {choices.map((choice) => (
        <Button
          key={choice.id}
          block
          className="text-left h-auto whitespace-normal"
          onClick={() => onChoice(choice.id)}
        >
          {choice.text}
        </Button>
      ))}

      <div className="flex gap-2 mt-1">
        <Input
          placeholder="输入你的行动..."
          value={customText}
          onChange={(e) => setCustomText(e.target.value)}
          onPressEnter={handleCustomSubmit}
          className="flex-1"
        />
        <Button type="primary" onClick={handleCustomSubmit}>
          发送
        </Button>
      </div>
    </div>
  );
}
