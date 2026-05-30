import { Card, Tag, Progress } from "antd";
import type { Character, Relationship } from "../../services/characters";

interface CharacterPanelProps {
  character: Character | null;
  relationships?: Relationship[];
}

const roleColors: Record<string, string> = {
  protagonist: "blue",
  npc: "green",
  antagonist: "red",
  supporting: "orange",
};

export function CharacterPanel({ character, relationships }: CharacterPanelProps) {
  if (!character) return null;

  return (
    <Card
      size="small"
      className="border-none"
      style={{ background: "#2d3436", color: "#fff" }}
    >
      <div className="flex items-start gap-3">
        {character.avatar_url && (
          <img
            src={character.avatar_url}
            alt={character.name}
            className="w-16 h-16 rounded-full object-cover"
          />
        )}
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <strong style={{ color: "#ffeaa7" }}>{character.name}</strong>
            {character.display_name && (
              <span style={{ color: "#b2bec3" }}>"{character.display_name}"</span>
            )}
            <Tag color={roleColors[character.role_type] || "default"}>
              {character.role_type}
            </Tag>
          </div>

          {character.appearance && (
            <p className="text-sm mb-2" style={{ color: "#dfe6e9" }}>{character.appearance}</p>
          )}

          {character.stats && Object.entries(character.stats).map(([key, value]) => (
            <div key={key} className="flex items-center gap-2 mb-1">
              <span className="text-xs w-16" style={{ color: "#b2bec3" }}>{key}</span>
              <Progress
                percent={typeof value === "number" ? value : 0}
                size="small"
                strokeColor="#FF6B9D"
                className="flex-1"
              />
            </div>
          ))}
        </div>
      </div>

      {relationships && relationships.length > 0 && (
        <div className="mt-3 pt-3 border-t" style={{ borderColor: "#636e72" }}>
          <div className="text-xs mb-2" style={{ color: "#b2bec3" }}>关系</div>
          {relationships.map((rel, i) => (
            <div key={i} className="flex items-center gap-2 mb-1 text-sm">
              <span>{rel.target_name}</span>
              <Tag color={rel.attitude === "hostile" ? "red" : rel.attitude === "friendly" ? "green" : "default"}>
                {rel.relation_type}
              </Tag>
              {rel.description && (
                <span className="text-xs" style={{ color: "#636e72" }}>{rel.description}</span>
              )}
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
