import asyncio
import json
from collections.abc import AsyncGenerator

from openai import AsyncOpenAI

from app.core.config import settings
from app.core.exceptions import AIServiceError

STORY_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "generate_story_response",
            "description": "生成互动小说的剧情响应",
            "parameters": {
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
                                "speaker": {"type": "string", "description": "角色名"},
                                "text": {"type": "string", "description": "对话内容"},
                                "emotion": {
                                    "type": "string",
                                    "enum": ["neutral", "happy", "sad", "angry", "worried", "scared"],
                                    "description": "情绪",
                                },
                            },
                            "required": ["speaker", "text", "emotion"],
                        },
                        "description": "角色对话列表",
                    },
                    "choices": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string", "description": "选项ID，如c1,c2"},
                                "text": {"type": "string", "description": "选项文本"},
                                "is_custom": {"type": "boolean", "description": "是否为自由行动选项"},
                            },
                            "required": ["id", "text", "is_custom"],
                        },
                        "description": "2-4个选项，最后一个为自由行动",
                    },
                    "scene_change": {
                        "type": "object",
                        "properties": {
                            "to_scene_id": {"type": "string", "description": "目标场景key"},
                            "transition": {"type": "string", "description": "过渡效果：fade/slide/instant"},
                        },
                        "nullable": True,
                        "description": "场景切换，无则null",
                    },
                    "stat_changes": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "target": {"type": "string", "enum": ["player", "npc"]},
                                "target_id": {"type": "string", "description": "目标ID"},
                                "stat": {"type": "string", "description": "属性名"},
                                "change": {"type": "number", "description": "变化值，正为增负为减"},
                            },
                            "required": ["target", "target_id", "stat", "change"],
                        },
                        "description": "属性变化列表",
                    },
                    "flags_set": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "flag": {"type": "string", "description": "标记名"},
                                "value": {"type": "boolean", "description": "标记值"},
                            },
                            "required": ["flag", "value"],
                        },
                        "description": "标记设置列表",
                    },
                    "is_game_over": {
                        "type": "boolean",
                        "description": "游戏是否结束",
                    },
                    "ending": {
                        "type": "string",
                        "nullable": True,
                        "description": "结局名称，is_game_over为true时填写",
                    },
                },
                "required": [
                    "narration", "dialogs", "choices", "scene_change",
                    "stat_changes", "flags_set", "is_game_over", "ending",
                ],
            },
        },
    }
]

SYSTEM_PROMPT = """你是一个专业的互动小说游戏导演，负责创造引人入胜的互动故事体验。

核心规则：
1. 以第二人称"你"进行叙述
2. 场景描写要生动，有画面感，300-500字
3. 对话要符合角色人设，每个角色有独特的说话方式
4. 在关键节点提供2-4个明确选项，最后一个选项为"自由行动"
5. 保持角色人设一致性，NPC要有自己的动机和秘密
6. 非上帝视角，严格遵守角色视角
7. 重视玩家的选择，让选择产生后果
8. 适时推进剧情，但给玩家探索空间

请调用 generate_story_response 函数来生成你的回复。"""


class AIService:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.SILICONFLOW_API_KEY,
            base_url=settings.SILICONFLOW_BASE_URL,
        )
        self.semaphore = asyncio.Semaphore(settings.AI_MAX_CONCURRENCY)

    async def generate_story(self, session, script, current_scene, player_input: str, history: list[dict]) -> dict:
        player_input = self._sanitize_input(player_input[:500])
        prompt = self._build_prompt(session, script, current_scene, player_input, history)

        async with self.semaphore:
            try:
                response = await self._call_with_retry(
                    model=settings.SILICONFLOW_MODEL,
                    max_tokens=settings.AI_MAX_TOKENS,
                    temperature=0.8,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    tools=STORY_TOOLS,
                    tool_choice={"type": "function", "function": {"name": "generate_story_response"}},
                )
                return self._parse_tool_response(response)
            except AIServiceError:
                return self._get_fallback_response()

    async def generate_story_stream(
        self, session, script, current_scene, player_input: str, history: list[dict]
    ) -> AsyncGenerator[tuple[str, dict], None]:
        """Stream AI story response with real streaming from SiliconFlow.

        Uses tool_calls streaming. We track the JSON buffer and extract narration
        text in real-time by detecting when we're inside the "narration" value.

        Event types:
        - ("narration_chunk", {"text": "..."}) — partial narration text (real-time)
        - ("complete", {...full AI response...}) — complete parsed response
        """
        player_input = self._sanitize_input(player_input[:500])
        prompt = self._build_prompt(session, script, current_scene, player_input, history)

        async with self.semaphore:
            try:
                stream = await self._call_stream_with_retry(
                    model=settings.SILICONFLOW_MODEL,
                    max_tokens=settings.AI_MAX_TOKENS,
                    temperature=0.8,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    tools=STORY_TOOLS,
                    tool_choice={"type": "function", "function": {"name": "generate_story_response"}},
                    stream=True,
                )

                buffer = ""
                # JSON stream state machine for real-time text extraction
                state = "idle"
                escaped = False
                recent_chars = ""

                async for chunk in stream:
                    if not chunk.choices:
                        continue
                    delta = chunk.choices[0].delta

                    if delta.content:
                        buffer += delta.content
                        yield ("narration_chunk", {"text": delta.content})

                    if delta.tool_calls and len(delta.tool_calls) > 0:
                        tc_delta = delta.tool_calls[0]
                        if tc_delta.function and tc_delta.function.arguments:
                            new_frag = tc_delta.function.arguments
                            buffer += new_frag

                            for char in new_frag:
                                recent_chars += char
                                if len(recent_chars) > 40:
                                    recent_chars = recent_chars[-40:]

                                if state == "idle":
                                    if '"narration"' in recent_chars:
                                        idx = recent_chars.rfind('"narration"')
                                        after = recent_chars[idx + len('"narration"'):]
                                        colon_pos = after.find(':')
                                        if colon_pos != -1:
                                            rest = after[colon_pos + 1:].lstrip()
                                            if rest.startswith('"'):
                                                state = "in_narration"
                                                escaped = False

                                elif state == "in_narration":
                                    if escaped:
                                        escaped = False
                                        if char == 'n':
                                            yield ("narration_chunk", {"text": "\n"})
                                        elif char == 't':
                                            yield ("narration_chunk", {"text": "\t"})
                                        elif char == 'r':
                                            yield ("narration_chunk", {"text": "\r"})
                                        else:
                                            yield ("narration_chunk", {"text": char})
                                    elif char == '\\':
                                        escaped = True
                                    elif char == '"':
                                        state = "idle"
                                    else:
                                        yield ("narration_chunk", {"text": char})

                # Parse the complete response
                parsed = None
                if buffer:
                    try:
                        start = buffer.find("{")
                        if start != -1:
                            json_str = buffer[start:]
                            for suffix in ["", "}", "}}", '"}']:
                                try:
                                    parsed = json.loads(json_str + suffix)
                                    if "narration" in parsed:
                                        break
                                except json.JSONDecodeError:
                                    continue
                    except Exception:
                        pass

                if parsed and "narration" in parsed:
                    yield ("complete", self._fill_defaults(parsed))
                else:
                    fallback = self._fallback_text_parse(buffer) if buffer.strip() else self._get_fallback_response()
                    yield ("complete", fallback)

            except AIServiceError:
                fallback = self._get_fallback_response()
                yield ("complete", fallback)

    async def _call_stream_with_retry(self, **kwargs):
        for attempt in range(settings.AI_MAX_RETRIES):
            try:
                return await self.client.chat.completions.create(**kwargs)
            except Exception as e:
                if attempt == settings.AI_MAX_RETRIES - 1:
                    raise AIServiceError(f"AI调用失败: {e}")
                await asyncio.sleep(attempt + 1)

    async def _call_with_retry(self, **kwargs):
        for attempt in range(settings.AI_MAX_RETRIES):
            try:
                return await asyncio.wait_for(
                    self.client.chat.completions.create(**kwargs),
                    timeout=settings.AI_TIMEOUT,
                )
            except asyncio.TimeoutError:
                if attempt == settings.AI_MAX_RETRIES - 1:
                    raise AIServiceError("AI响应超时")
            except Exception as e:
                if attempt == settings.AI_MAX_RETRIES - 1:
                    raise AIServiceError(f"AI调用失败: {e}")
                await asyncio.sleep(attempt + 1)

    async def generate_image(self, prompt: str, size: str = "1024x576") -> str | None:
        async with self.semaphore:
            try:
                response = await asyncio.wait_for(
                    self.client.images.generate(
                        model=settings.SILICONFLOW_IMAGE_MODEL,
                        prompt=prompt,
                        size=size,
                        n=1,
                    ),
                    timeout=60,
                )
                return response.data[0].url
            except Exception:
                return None

    def _parse_tool_response(self, response) -> dict:
        message = response.choices[0].message

        if message.tool_calls and len(message.tool_calls) > 0:
            tool_call = message.tool_calls[0]
            try:
                return self._fill_defaults(json.loads(tool_call.function.arguments))
            except json.JSONDecodeError:
                pass

        content = message.content or ""
        if content.strip():
            return self._fallback_text_parse(content)

        return self._get_fallback_response()

    def _fill_defaults(self, parsed: dict) -> dict:
        defaults = {
            "dialogs": [], "choices": [{"id": "free", "text": "自由行动", "is_custom": True}],
            "scene_change": None, "stat_changes": [], "flags_set": [],
            "is_game_over": False, "ending": None,
        }
        for key, val in defaults.items():
            if key not in parsed:
                parsed[key] = val
        return parsed

    def _build_prompt(self, session, script, current_scene, player_input: str, history: list[dict]) -> str:
        script_info = ""
        if script:
            script_info = f"""【剧本信息】
名称：{script.title}
类型：{script.genre}
背景：{script.setting.get('world', '') if script.setting else ''}
当前阶段：{session.game_phase or '开场'}"""

        scene_info = ""
        if current_scene:
            scene_info = f"""【当前场景】
场景名称：{current_scene.name}
场景描述：{current_scene.description or ''}
时间：{session.game_time or '第1天 上午'}"""

        history_text = "\n".join(f"{h['type']}: {h['content']}" for h in history[-5:]) if history else "无"

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

请调用 generate_story_response 函数生成剧情回复。"""

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
            "stat_changes": [],
            "flags_set": [],
            "is_game_over": False,
            "ending": None,
        }

    def _fallback_text_parse(self, text: str) -> dict:
        stripped = text.strip()
        if stripped.startswith("```"):
            lines = stripped.split("\n")
            lines = [l for l in lines if not l.startswith("```")]
            stripped = "\n".join(lines).strip()
        try:
            result = json.loads(stripped)
            return self._fill_defaults(result)
        except json.JSONDecodeError:
            return {
                "narration": stripped,
                "dialogs": [],
                "choices": [{"id": "free", "text": "自由行动", "is_custom": True}],
                "scene_change": None,
                "stat_changes": [],
                "flags_set": [],
                "is_game_over": False,
                "ending": None,
            }


ai_service = AIService()
