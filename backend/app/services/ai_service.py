import asyncio
import json

from anthropic import AsyncAnthropic
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AIServiceError

STORY_TOOLS = [
    {
        "name": "generate_story_response",
        "description": "生成剧情回复，包含叙事文本、角色对话、选项和游戏指令",
        "input_schema": {
            "type": "object",
            "properties": {
                "narration": {
                    "type": "string",
                    "description": "场景描写和剧情叙述，300-500字，第二人称",
                },
                "dialogs": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "speaker": {"type": "string"},
                            "text": {"type": "string"},
                            "emotion": {"type": "string", "enum": ["neutral", "happy", "sad", "angry", "worried", "scared"]},
                        },
                        "required": ["speaker", "text"],
                    },
                },
                "choices": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "text": {"type": "string"},
                            "is_custom": {"type": "boolean", "default": False},
                        },
                        "required": ["id", "text"],
                    },
                    "description": "2-4个选项，最后一个为自由行动",
                },
                "scene_change": {
                    "type": "object",
                    "properties": {
                        "to_scene_id": {"type": "string"},
                        "transition": {"type": "string", "enum": ["fade", "slide", "warp"]},
                    },
                },
                "character_movements": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "character_id": {"type": "string"},
                            "action": {"type": "string"},
                            "position": {"type": "object", "properties": {"x": {"type": "number"}, "y": {"type": "number"}}},
                        },
                    },
                },
                "stat_changes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "target": {"type": "string", "enum": ["player", "npc"]},
                            "target_id": {"type": "string"},
                            "stat": {"type": "string"},
                            "change": {"type": "number"},
                        },
                    },
                },
                "flags_set": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "flag": {"type": "string"},
                            "value": {"type": "boolean"},
                        },
                    },
                },
                "is_game_over": {"type": "boolean", "default": False},
                "ending": {"type": "string"},
            },
            "required": ["narration", "choices"],
        },
    }
]

SYSTEM_PROMPT = """你是一个专业的互动小说游戏导演。

规则：
1. 以第二人称"你"进行叙述
2. 场景描写要生动，有画面感，300-500字
3. 对话要符合角色人设
4. 在关键节点提供2-4个明确选项，最后一个选项为"自由行动"
5. 恐怖场景描写要具体、冷静且有冲击力
6. 保持角色人设一致性
7. 非上帝视角，严格遵守角色视角
8. 必须使用 generate_story_response 工具返回结果"""


class AIService:
    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.CLAUDE_API_KEY)
        self.semaphore = asyncio.Semaphore(10)

    async def generate_story(self, session, player_input: str, history: list[dict]) -> dict:
        player_input = self._sanitize_input(player_input[:500])
        prompt = self._build_prompt(session, player_input, history)

        async with self.semaphore:
            try:
                response = await self._call_with_retry(
                    model=settings.CLAUDE_MODEL,
                    max_tokens=settings.CLAUDE_MAX_TOKENS,
                    temperature=0.8,
                    system=SYSTEM_PROMPT,
                    tools=STORY_TOOLS,
                    messages=[{"role": "user", "content": prompt}],
                )
                return self._parse_tool_response(response)
            except AIServiceError:
                return self._get_fallback_response()

    async def _call_with_retry(self, **kwargs):
        for attempt in range(3):
            try:
                return await asyncio.wait_for(self.client.messages.create(**kwargs), timeout=30.0)
            except asyncio.TimeoutError:
                if attempt == 2:
                    raise AIServiceError("AI响应超时")
            except Exception as e:
                if attempt == 2:
                    raise AIServiceError(f"AI调用失败: {e}")
                await asyncio.sleep(attempt + 1)

    def _parse_tool_response(self, response) -> dict:
        for block in response.content:
            if block.type == "tool_use" and block.name == "generate_story_response":
                return block.input
        for block in response.content:
            if block.type == "text":
                return self._fallback_text_parse(block.text)
        return self._get_fallback_response()

    def _build_prompt(self, session, player_input: str, history: list[dict]) -> str:
        script = session.script if hasattr(session, "script") else None
        scene = session.current_scene if hasattr(session, "current_scene") else None

        script_info = ""
        if script:
            script_info = f"""【剧本信息】
名称：{script.title}
类型：{script.genre}
背景：{script.setting.get('world', '') if script.setting else ''}
当前阶段：{session.game_phase or '开场'}"""

        scene_info = ""
        if scene:
            scene_info = f"""【当前场景】
场景名称：{scene.name}
场景描述：{scene.description or ''}
时间：{session.game_time or '第1天 上午'}"""

        history_text = "\n".join(f"{h['type']}: {h['content']}" for h in history[-5:])

        return f"""{script_info}

{scene_info}

【玩家信息】
名称：{session.player_name or '玩家'}
属性：{json.dumps(session.player_stats, ensure_ascii=False)}

【NPC状态】
{json.dumps(session.npc_states, ensure_ascii=False)}

【剧情标记】
{json.dumps(session.story_flags, ensure_ascii=False)}

【剧情历史（最近5轮）】
{history_text}

<user_input>
{player_input}
</user_input>

请使用 generate_story_response 工具生成剧情回复。"""

    def _sanitize_input(self, text: str) -> str:
        for tag in ["[SCENE:", "[CHAR:", "[EVENT:", "[STAT:", "[FLAG:", "</system>", "<system>"]:
            text = text.replace(tag, "")
        return text.strip()

    def _get_fallback_response(self) -> dict:
        return {
            "narration": "一阵迷雾笼罩了你的视线，你暂时无法看清周围的情况...",
            "dialogs": [],
            "choices": [{"id": "retry", "text": "再试一次"}, {"id": "wait", "text": "静静等待"}],
            "scene_change": None,
            "character_movements": [],
            "stat_changes": [],
            "flags_set": [],
            "is_game_over": False,
            "ending": None,
        }

    def _fallback_text_parse(self, text: str) -> dict:
        return {
            "narration": text,
            "dialogs": [],
            "choices": [{"id": "free", "text": "自由行动", "is_custom": True}],
            "scene_change": None,
            "character_movements": [],
            "stat_changes": [],
            "flags_set": [],
            "is_game_over": False,
            "ending": None,
        }


ai_service = AIService()