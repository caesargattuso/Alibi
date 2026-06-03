import json as json_lib
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import Script, Scene, Character, User
from app.core.config import settings
from app.services.ai_service import ai_service
from app.services.file_service import file_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scripts", tags=["scripts"])


class AIScriptGenerateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    genre: str
    difficulty: str = "normal"
    description: str = Field(min_length=1, max_length=2000)


class AIScriptGenerateResponse(BaseModel):
    script_id: int
    script: dict
    scenes: list[dict]
    characters: list[dict]
    cover_image_url: str | None = None


SCRIPT_GENERATION_PROMPT = """你是一个专业的互动小说剧本创作助手。请根据用户提供的剧本信息，生成一个完整的互动小说剧本。

你需要生成以下内容：
1. 剧本设定（setting）：世界观、时代背景、核心谜题/冲突
2. 场景列表（scenes）：3-5个主要场景，每个场景包含场景key、名称、描述、背景描述
3. 角色列表（characters）：3-6个主要角色，每个角色包含角色key、名称、角色类型、外观描述、性格特点、背景故事、对话风格

请严格按照以下JSON格式输出：

{
  "setting": {
    "world": "世界观描述",
    "time_period": "时代背景",
    "core_mystery": "核心谜题或冲突"
  },
  "scenes": [
    {
      "scene_key": "场景唯一标识符(英文小写)",
      "name": "场景名称",
      "description": "场景描述(100-200字)",
      "background_description": "场景背景画面描述(用于AI生成图片)"
    }
  ],
  "characters": [
    {
      "character_key": "角色唯一标识符(英文小写)",
      "name": "角色名称",
      "role_type": "主角/嫌疑人/受害者/侦探/证人/其他",
      "appearance": "外观描述(50-100字)",
      "personality": "性格特点描述",
      "background": "背景故事(100-200字)",
      "dialogue_style": "对话风格描述"
    }
  ]
}

注意：
- 场景key和角色key必须使用英文小写，用下划线连接
- 描述要生动具体，符合剧本类型风格
- 角色之间要有复杂的关系和秘密
- 场景之间要有逻辑关联和递进关系"""


@router.post("/generate", response_model=dict)
async def generate_script_with_ai(
    data: AIScriptGenerateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """使用AI生成完整的剧本内容。"""
    logger.info(f"Generate request: title={data.title}, genre={data.genre}, difficulty={data.difficulty}, desc_len={len(data.description)}")
    prompt = f"""请根据以下信息生成一个完整的互动小说剧本：

剧本标题：{data.title}
剧本类型：{data.genre}
难度：{data.difficulty}
简介：{data.description}

{SCRIPT_GENERATION_PROMPT}"""

    async with ai_service.semaphore:
        response = await ai_service.client.chat.completions.create(
            model=settings.SILICONFLOW_MODEL,
            max_tokens=4096,
            temperature=0.8,
            messages=[
                {"role": "system", "content": SCRIPT_GENERATION_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )

    # Parse AI response
    content = response.choices[0].message.content
    generated = _parse_ai_script_response(content)

    # Generate cover image
    cover_prompt = f"游戏封面插画，{data.genre}风格，{data.title}，高质量，精美细节"
    cover_image_url = await ai_service.generate_image(cover_prompt, "1024x1024")
    stored_cover_url = None
    if cover_image_url:
        # Create a temporary script ID for image storage
        temp_script_id = int(datetime.now(timezone.utc).timestamp())
        stored_cover_url = await file_service.store_ai_image(
            script_id=temp_script_id,
            session_id=0,
            image_url=cover_image_url,
            image_type="cover",
        )

    return {
        "code": 200,
        "data": {
            "script": {
                "title": data.title,
                "genre": data.genre,
                "difficulty": data.difficulty,
                "description": data.description,
                "setting": generated.get("setting", {}),
            },
            "scenes": generated.get("scenes", []),
            "characters": generated.get("characters", []),
            "cover_image_url": stored_cover_url,
        },
    }


def _parse_ai_script_response(content: str) -> dict:
    """Parse AI response and extract structured script data."""
    if not content:
        return {}

    # Try to extract JSON from the response
    try:
        # Find JSON block
        if "```json" in content:
            json_start = content.find("```json") + 7
            json_end = content.find("```", json_start)
            content = content[json_start:json_end].strip()
        elif "```" in content:
            json_start = content.find("```") + 3
            json_end = content.find("```", json_start)
            content = content[json_start:json_end].strip()

        return json_lib.loads(content)
    except (json_lib.JSONDecodeError, ValueError):
        # Fallback: try to find any JSON in the response
        try:
            start = content.find("{")
            end = content.rfind("}")
            if start != -1 and end != -1:
                return json_lib.loads(content[start:end + 1])
        except (json_lib.JSONDecodeError, ValueError):
            pass

    return {}
