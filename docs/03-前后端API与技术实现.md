# 前后端API与技术实现文档

## 文档信息

| 项目 | 内容 |
|------|------|
| 文档名称 | 前后端API与技术实现 |
| 版本 | v2.0 |
| 更新日期 | 2026-05-30 |

---

## 一、技术栈选型

### 1.1 前端技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 框架 | React 18 + TypeScript | 主框架，类型安全 |
| 状态管理 | Zustand | 轻量级状态管理 |
| 路由 | React Router v6 | 单页应用路由 |
| UI组件 | Ant Design + Tailwind CSS | 组件库 + 原子化CSS |
| 地图渲染 | PixiJS | 场景地图渲染 |
| 动画 | Framer Motion | 过渡动画、角色移动动画 |
| 通信 | Socket.IO Client | WebSocket通信 |
| 构建工具 | Vite | 快速构建 |

### 1.2 后端技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 框架 | FastAPI (Python) | 原生asyncio异步框架 |
| ORM | SQLAlchemy 2.0 (async) | 异步ORM + 连接池 |
| 迁移 | Alembic | 数据库迁移管理 |
| 缓存 | Redis + aioredis | 会话、缓存、消息队列 |
| 数据库 | PostgreSQL 16 | 主数据库，JSONB支持 |
| 文件存储 | MinIO / 阿里云OSS | 图片、音频等资源 |
| AI接口 | Anthropic Claude SDK | 剧情生成，支持tool_use |
| 部署 | Docker + Docker Compose | 容器化部署 |

---

## 二、API设计

### 2.1 API设计原则

- **RESTful风格**：资源导向，使用标准HTTP方法
- **版本控制**：URL中包含版本号 `/api/v1/`
- **统一响应格式**：所有API返回统一的JSON格式
- **错误处理**：统一的错误码和错误信息
- **分页**：列表接口支持分页
- **认证**：JWT Token认证

### 2.2 统一响应格式

```json
{
  "code": 200,
  "message": "success",
  "data": {},
  "timestamp": "2026-05-30T12:00:00Z"
}
```

### 2.3 错误响应格式

```json
{
  "code": 400,
  "message": "参数错误",
  "data": null,
  "error": {
    "field": "username",
    "detail": "用户名不能为空"
  },
  "timestamp": "2026-05-30T12:00:00Z"
}
```

---

## 三、API接口列表

### 3.1 用户模块

#### 用户注册

```
POST /api/v1/auth/register
```

请求：
```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "captcha_id": "string",
  "captcha_code": "string"
}
```

> 验证码方案：服务端生成图形验证码，captcha_id为验证码会话ID，captcha_code为用户输入。验证后立即失效，防止重放攻击。

响应：
```json
{
  "code": 200,
  "data": {
    "user_id": 1,
    "username": "string",
    "token": "jwt_access_token",
    "refresh_token": "jwt_refresh_token",
    "expires_in": 3600
  }
}
```

#### 获取验证码

```
GET /api/v1/auth/captcha
```

响应：
```json
{
  "code": 200,
  "data": {
    "captcha_id": "uuid",
    "captcha_image": "base64_encoded_image"
  }
}
```

#### 用户登录

```
POST /api/v1/auth/login
```

请求：
```json
{
  "username_or_email": "string",
  "password": "string"
}
```

#### Token刷新

```
POST /api/v1/auth/refresh
```

请求：
```json
{
  "refresh_token": "string"
}
```

> JWT策略：Access Token 1小时过期，Refresh Token 7天过期。前端在Access Token过期时自动用Refresh Token刷新，两个Token都过期则跳转登录页。

#### 获取/更新用户信息

```
GET  /api/v1/users/me
PUT  /api/v1/users/me
PUT  /api/v1/users/me/password
```

---

### 3.2 剧本模块

#### 获取剧本列表

```
GET /api/v1/scripts
```

查询参数：

| 参数 | 类型 | 说明 |
|------|------|------|
| page | int | 页码，默认1 |
| per_page | int | 每页数量，默认20 |
| genre | string | 类型筛选 |
| difficulty | string | 难度筛选 |
| sort_by | string | 排序字段 |
| search | string | 搜索关键词 |

#### 剧本CRUD

```
GET    /api/v1/scripts/{script_id}
POST   /api/v1/scripts
PUT    /api/v1/scripts/{script_id}
DELETE /api/v1/scripts/{script_id}
```

#### 剧本互动

```
POST   /api/v1/scripts/{script_id}/favorite
DELETE /api/v1/scripts/{script_id}/favorite
POST   /api/v1/scripts/{script_id}/rate    # body: {"rating": 5, "comment": "..."}
```

---

### 3.3 游戏模块

#### 开始游戏

```
POST /api/v1/games
```

请求：
```json
{
  "script_id": 1,
  "player_name": "string"
}
```

响应：
```json
{
  "code": 200,
  "data": {
    "session_id": 1,
    "current_scene": {
      "id": 1,
      "name": "正殿",
      "background_image": "url",
      "map_data": {},
      "interactable_points": []
    },
    "player_stats": {},
    "npc_states": {},
    "game_time": "第1天 上午",
    "game_phase": "初选"
  }
}
```

#### 执行动作

```
POST /api/v1/games/{session_id}/actions
```

请求：
```json
{
  "action_type": "move|interact|talk|custom",
  "target_id": "string",
  "target_position": {"x": 100, "y": 200},
  "input": "string"
}
```

#### 发送消息（AI对话）

```
POST /api/v1/games/{session_id}/messages
```

请求：
```json
{
  "message": "string",
  "choice_id": "string"
}
```

响应（AI通过tool_use返回结构化结果）：
```json
{
  "code": 200,
  "data": {
    "message_id": 1,
    "narration": "剧情文本...",
    "dialogs": [
      {"speaker": "沈越", "text": "...", "emotion": "worried"}
    ],
    "choices": [
      {"id": "c1", "text": "观察周围的环境"},
      {"id": "c2", "text": "自由行动", "is_custom": true}
    ],
    "commands": {
      "scene_change": null,
      "character_movements": [],
      "stat_changes": [],
      "flags_set": []
    },
    "is_game_over": false,
    "ending": null
  }
}
```

#### 其他游戏接口

```
GET  /api/v1/games/{session_id}          # 获取游戏状态
GET  /api/v1/games/{session_id}/messages  # 对话历史
POST /api/v1/games/{session_id}/pause     # 暂停
POST /api/v1/games/{session_id}/resume    # 恢复
POST /api/v1/games/{session_id}/end       # 结束 body: {"reason": "completed|abandoned|died"}
GET  /api/v1/games                        # 游戏历史
```

---

### 3.4 场景/角色/排行榜/成就/上传模块

```
GET /api/v1/scenes/{scene_id}
GET /api/v1/scenes/{scene_id}/map
GET /api/v1/scenes/{scene_id}/interactables
POST /api/v1/scenes/{scene_id}/interact   # body: {"interactable_id": "...", "action_id": "..."}

GET /api/v1/characters/{character_id}
GET /api/v1/characters/{character_id}/relationships

GET /api/v1/leaderboards/scripts?period=week&sort_by=play_count
GET /api/v1/leaderboards/players?period=week&sort_by=completed_games

GET  /api/v1/achievements
GET  /api/v1/users/me/achievements

POST /api/v1/upload/image   # multipart/form-data
POST /api/v1/upload/audio   # multipart/form-data
```

---

## 四、WebSocket API

### 4.1 连接与认证

```
ws://api.example.com/ws/v1/games/{session_id}?token={jwt_access_token}
```

> WebSocket握手验证：连接时携带JWT Token，服务端在accept前验证Token有效性。Token无效则拒绝连接（返回401关闭）。连接建立后，Token过期不主动断开，但操作时重新校验。

### 4.2 消息格式

```json
{
  "type": "message|action|system|error",
  "data": {},
  "timestamp": "2026-05-30T12:00:00Z"
}
```

### 4.3 客户端→服务端

**发送游戏动作：**
```json
{
  "type": "action",
  "data": {
    "action_type": "move|interact|talk|custom",
    "target_id": "string",
    "input": "string"
  }
}
```

**心跳：**
```json
{"type": "ping"}
```

### 4.4 服务端→客户端

**剧情更新：**
```json
{
  "type": "story_update",
  "data": {
    "narration": "string",
    "dialogs": [...],
    "choices": [...],
    "commands": {...}
  }
}
```

**角色移动 / 场景切换 / 系统通知 / 错误：**
```json
{"type": "character_move", "data": {"character_id": 1, "from": {"x":0,"y":0}, "to": {"x":100,"y":200}}}
{"type": "scene_change", "data": {"from_scene_id": 1, "to_scene_id": 2, "transition": "fade"}}
{"type": "system", "data": {"message": "string", "level": "info|warning|error"}}
{"type": "error", "data": {"code": 400, "message": "string"}}
```

---

## 五、AI服务实现（tool_use结构化输出）

### 5.1 tool_use设计

AI剧情生成使用Claude的tool_use功能，确保输出格式可靠、可解析。

```python
# app/services/ai_service.py

import json
from typing import List, Dict, Any, Optional
from anthropic import AsyncAnthropic
from app.core.config import settings

# AI工具定义：让Claude通过tool_use返回结构化指令
STORY_TOOLS = [
    {
        "name": "generate_story_response",
        "description": "生成剧情回复，包含叙事文本、角色对话、选项和游戏指令",
        "input_schema": {
            "type": "object",
            "properties": {
                "narration": {
                    "type": "string",
                    "description": "场景描写和剧情叙述，300-500字，第二人称"
                },
                "dialogs": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "speaker": {"type": "string"},
                            "text": {"type": "string"},
                            "emotion": {"type": "string", "enum": ["neutral", "happy", "sad", "angry", "worried", "scared"]}
                        },
                        "required": ["speaker", "text"]
                    }
                },
                "choices": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "text": {"type": "string"},
                            "is_custom": {"type": "boolean", "default": False}
                        },
                        "required": ["id", "text"]
                    },
                    "description": "2-4个选项，最后一个为自由行动"
                },
                "scene_change": {
                    "type": "object",
                    "properties": {
                        "to_scene_id": {"type": "string"},
                        "transition": {"type": "string", "enum": ["fade", "slide", "warp"]}
                    }
                },
                "character_movements": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "character_id": {"type": "string"},
                            "action": {"type": "string"},
                            "position": {"type": "object", "properties": {"x": {"type": "number"}, "y": {"type": "number"}}}
                        }
                    }
                },
                "stat_changes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "target": {"type": "string", "enum": ["player", "npc"]},
                            "target_id": {"type": "string"},
                            "stat": {"type": "string"},
                            "change": {"type": "number"}
                        }
                    }
                },
                "flags_set": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "flag": {"type": "string"},
                            "value": {"type": "boolean"}
                        }
                    }
                },
                "is_game_over": {"type": "boolean", "default": False},
                "ending": {"type": "string"}
            },
            "required": ["narration", "choices"]
        }
    }
]


class AIService:
    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.CLAUDE_API_KEY)
        self.semaphore = asyncio.Semaphore(10)  # 并发限制

    async def generate_story(
        self,
        session: "GameSession",
        player_input: str,
        history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """生成剧情 — 使用tool_use确保结构化输出"""

        # 输入长度限制
        player_input = player_input[:500]

        # 输入安全过滤
        player_input = self._sanitize_input(player_input)

        prompt = self._build_prompt(session, player_input, history)

        async with self.semaphore:
            try:
                response = await self._call_with_retry(
                    model=settings.CLAUDE_MODEL,  # 配置化模型名
                    max_tokens=4096,
                    temperature=0.8,
                    system=self._get_system_prompt(),
                    tools=STORY_TOOLS,
                    messages=[{"role": "user", "content": prompt}]
                )

                # 解析tool_use输出
                return self._parse_tool_response(response)

            except AIServiceError:
                # 降级：返回默认提示
                return self._get_fallback_response()

    async def _call_with_retry(self, **kwargs) -> Any:
        """带重试的AI调用"""
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                return await asyncio.wait_for(
                    self.client.messages.create(**kwargs),
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                if attempt == max_retries:
                    raise AIServiceError("AI响应超时")
            except Exception as e:
                if attempt == max_retries:
                    raise AIServiceError(f"AI调用失败: {str(e)}")
                await asyncio.sleep(1 * (attempt + 1))  # 指数退避

    def _parse_tool_response(self, response: Any) -> Dict[str, Any]:
        """解析tool_use结构化输出"""
        for block in response.content:
            if block.type == "tool_use" and block.name == "generate_story_response":
                return block.input  # 直接获得结构化JSON

        # 降级：如果AI没有使用tool_use，尝试从文本中提取
        for block in response.content:
            if block.type == "text":
                return self._fallback_text_parse(block.text)

        return self._get_fallback_response()

    def _sanitize_input(self, text: str) -> str:
        """输入安全过滤：防prompt注入"""
        # 移除可能的注入标记
        for tag in ["[SCENE:", "[CHAR:", "[EVENT:", "[STAT:", "[FLAG:", "</system>", "<system>"]:
            text = text.replace(tag, "")
        return text.strip()

    def _get_fallback_response(self) -> Dict[str, Any]:
        """AI服务不可用时的降级回复"""
        return {
            "narration": "一阵迷雾笼罩了你的视线，你暂时无法看清周围的情况...",
            "dialogs": [],
            "choices": [
                {"id": "retry", "text": "再试一次"},
                {"id": "wait", "text": "静静等待"}
            ],
            "scene_change": None,
            "character_movements": [],
            "stat_changes": [],
            "flags_set": [],
            "is_game_over": False,
            "ending": None
        }

    def _build_prompt(self, session, player_input: str, history: List[Dict]) -> str:
        """构建提示词"""
        script = session.script
        scene = session.current_scene

        prompt = f"""【剧本信息】
名称：{script.title}
类型：{script.genre}
背景：{script.setting.get('world', '')}
当前阶段：{session.game_phase}

【当前场景】
场景名称：{scene.name}
场景描述：{scene.description}
时间：{session.game_time}

【玩家信息】
名称：{session.player_name}
属性：{json.dumps(session.player_stats, ensure_ascii=False)}

【NPC状态】
{json.dumps(session.npc_states, ensure_ascii=False)}

【剧情标记】
{json.dumps(session.story_flags, ensure_ascii=False)}

【剧情历史（最近5轮）】
{self._format_history(history)}

<user_input>
{player_input}
</user_input>

请使用 generate_story_response 工具生成剧情回复。"""

        return prompt

    def _get_system_prompt(self) -> str:
        """系统提示词 — 使用prompt caching"""
        return """你是一个专业的互动小说游戏导演。

规则：
1. 以第二人称"你"进行叙述
2. 场景描写要生动，有画面感，300-500字
3. 对话要符合角色人设
4. 在关键节点提供2-4个明确选项，最后一个选项为"自由行动"
5. 恐怖场景描写要具体、冷静且有冲击力
6. 保持角色人设一致性
7. 非上帝视角，严格遵守角色视角
8. 必须使用 generate_story_response 工具返回结果"""

    def _format_history(self, history: List[Dict]) -> str:
        formatted = []
        for item in history[-5:]:
            formatted.append(f"{item['type']}: {item['content']}")
        return "\n".join(formatted)

    def _fallback_text_parse(self, text: str) -> Dict[str, Any]:
        """降级文本解析（tool_use失败时使用）"""
        return {
            "narration": text,
            "dialogs": [],
            "choices": [{"id": "free", "text": "自由行动", "is_custom": True}],
            "scene_change": None,
            "character_movements": [],
            "stat_changes": [],
            "flags_set": [],
            "is_game_over": False,
            "ending": None
        }
```

### 5.2 模型配置

| 用途 | 模型 | 说明 |
|------|------|------|
| 剧情生成 | claude-sonnet-4-6 | 性价比高，速度快，日常剧情生成 |
| 关键剧情节点 | claude-opus-4-7 | 重要决策/结局生成，质量更高 |
| 摘要生成 | claude-sonnet-4-6 | 上下文摘要，低成本 |
| 封面图生成 | SiliconFlow Kolors | 文本生成图片 |

> 模型名通过环境变量配置，支持随时切换。

---

## 六、后端架构实现

### 6.1 项目结构

```
ai-game-platform/
├── app/
│   ├── __init__.py
│   ├── main.py                    # 应用入口
│   ├── config.py                  # 配置（Pydantic Settings）
│   ├── api/
│   │   ├── v1/
│   │   │   ├── auth.py            # 认证路由
│   │   │   ├── users.py           # 用户路由
│   │   │   ├── scripts.py         # 剧本路由
│   │   │   ├── games.py           # 游戏路由
│   │   │   ├── scenes.py          # 场景路由
│   │   │   ├── characters.py      # 角色路由
│   │   │   ├── leaderboards.py    # 排行榜路由
│   │   │   ├── achievements.py    # 成就路由
│   │   │   └── upload.py          # 上传路由
│   │   └── deps.py                # 依赖注入
│   ├── core/
│   │   ├── security.py            # JWT + bcrypt
│   │   ├── exceptions.py          # 异常体系
│   │   └── config.py              # Settings
│   ├── models/                    # SQLAlchemy模型
│   │   ├── user.py
│   │   ├── script.py
│   │   ├── game.py
│   │   ├── scene.py
│   │   └── character.py
│   ├── schemas/                   # Pydantic Schema
│   │   ├── user.py
│   │   ├── script.py
│   │   ├── game.py
│   │   └── common.py
│   ├── services/
│   │   ├── user_service.py
│   │   ├── script_service.py
│   │   ├── game_service.py
│   │   ├── ai_service.py          # AI服务（tool_use）
│   │   └── file_service.py
│   ├── db/
│   │   ├── base.py                # 数据库基础
│   │   ├── session.py             # 异步会话管理
│   │   └── migrations/            # Alembic迁移
│   ├── middleware/
│   │   ├── auth_middleware.py
│   │   ├── rate_limit.py
│   │   └── error_handler.py
│   └── websocket/
│       ├── manager.py             # WebSocket管理
│       └── handlers.py
├── alembic/                       # 数据库迁移
├── tests/
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── requirements.txt
├── pyproject.toml
└── .env.example
```

### 6.2 核心代码

#### 应用入口

```python
# app/main.py

from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.db.session import engine, init_db
from app.api.v1 import auth, users, scripts, games, scenes, characters
from app.middleware.auth_middleware import auth_middleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.core.exceptions import AppException, app_exception_handler

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await engine.dispose()

app = FastAPI(
    title="AI互动游戏平台",
    version="1.0.0",
    lifespan=lifespan,
)

# 中间件
app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)
app.middleware("http")(auth_middleware)

# 异常处理
app.add_exception_handler(AppException, app_exception_handler)

# 路由
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(scripts.router, prefix="/api/v1")
app.include_router(games.router, prefix="/api/v1")
app.include_router(scenes.router, prefix="/api/v1")
app.include_router(characters.router, prefix="/api/v1")
```

#### 数据库会话管理

```python
# app/db/session.py

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,  # postgresql+asyncpg://...
    pool_size=20,
    max_overflow=10,
    pool_recycle=3600,
    echo=settings.DEBUG,
)

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

async def init_db():
    """应用启动时初始化数据库连接"""
    pass  # SQLAlchemy懒连接，无需显式初始化
```

#### WebSocket管理

```python
# app/websocket/manager.py

from typing import Dict, Set
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.game_connections: Dict[int, Set[WebSocket]] = {}
        self.user_connections: Dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, game_id: int, user_id: int):
        await websocket.accept()
        self.game_connections.setdefault(game_id, set()).add(websocket)
        self.user_connections[user_id] = websocket

    def disconnect(self, websocket: WebSocket, game_id: int, user_id: int):
        if game_id in self.game_connections:
            self.game_connections[game_id].discard(websocket)
        self.user_connections.pop(user_id, None)

    async def send_to_user(self, message: dict, user_id: int):
        ws = self.user_connections.get(user_id)
        if ws:
            await ws.send_json(message)

    async def broadcast_to_game(self, message: dict, game_id: int):
        connections = self.game_connections.get(game_id, set())
        for ws in list(connections):
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(ws, game_id, -1)

manager = ConnectionManager()
```

#### 游戏服务

```python
# app/services/game_service.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.game import GameSession, DialogLog
from app.models.script import Script, Scene
from app.services.ai_service import AIService

class GameService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai = AIService()

    async def create_game(self, user_id: int, script_id: int, player_name: str) -> GameSession:
        script = await self.db.get(Script, script_id)
        if not script:
            raise NotFoundError("剧本")

        opening_scene = await self._get_opening_scene(script_id)

        session = GameSession(
            user_id=user_id,
            script_id=script_id,
            current_scene_id=opening_scene.id,
            player_name=player_name,
            player_stats={},
            npc_states=self._init_npc_states(script),
            story_flags={},
            game_phase="opening",
            game_time="第1天 上午",
            status="active",
        )
        self.db.add(session)
        await self.db.flush()
        return session

    async def process_action(
        self, session_id: int, action_type: str,
        target_id: str = None, player_input: str = None
    ) -> Dict[str, Any]:
        session = await self.db.get(GameSession, session_id)
        if not session:
            raise NotFoundError("游戏会话")

        history = await self._get_dialog_history(session_id, limit=5)
        input_text = self._build_input_text(action_type, target_id, player_input)

        # AI生成剧情（tool_use结构化输出）
        ai_response = await self.ai.generate_story(session, input_text, history)

        # 更新游戏状态
        await self._update_game_state(session, ai_response)

        # 保存对话记录
        await self._save_dialog_log(session_id, input_text, ai_response)

        return ai_response

    async def _update_game_state(self, session: GameSession, response: Dict):
        commands = response.get("commands", response)  # 兼容两种格式

        if commands.get("scene_change"):
            session.current_scene_id = commands["scene_change"]["to_scene_id"]

        for change in commands.get("stat_changes", []):
            stat = change["stat"]
            delta = change["change"]
            current = session.player_stats.get(stat, 0)
            session.player_stats[stat] = current + delta

        for flag_item in commands.get("flags_set", []):
            flag = flag_item["flag"] if isinstance(flag_item, dict) else flag_item
            value = flag_item.get("value", True) if isinstance(flag_item, dict) else True
            session.story_flags[flag] = value

        if response.get("is_game_over"):
            session.status = "completed"
            session.current_ending = response.get("ending")

        await self.db.flush()
```

---

## 七、前端架构

### 7.1 项目结构

```
ai-game-client/
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── components/
│   │   ├── common/           # Button, Input, Modal
│   │   ├── game/             # SceneMap, Character, DialogBox, ChoiceMenu, GameUI
│   │   └── layout/           # Header, Sidebar, Footer
│   ├── pages/
│   │   ├── Home/             # 首页
│   │   ├── Scripts/          # 剧本列表
│   │   ├── ScriptDetail/     # 剧本详情
│   │   ├── Game/             # 游戏页面
│   │   ├── Profile/          # 个人中心
│   │   └── Auth/             # 登录/注册
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useGame.ts
│   │   ├── useWebSocket.ts   # 含自动重连逻辑
│   │   └── useScene.ts
│   ├── stores/
│   │   ├── authStore.ts
│   │   ├── gameStore.ts
│   │   └── uiStore.ts
│   ├── services/
│   │   ├── api.ts            # axios实例，含Token刷新拦截器
│   │   ├── auth.ts
│   │   ├── scripts.ts
│   │   ├── games.ts
│   │   └── websocket.ts
│   ├── types/
│   ├── utils/
│   │   ├── pathfinding.ts    # A*寻路（优先队列）
│   │   └── offline.ts       # IndexedDB离线存储
│   └── styles/
├── package.json
├── vite.config.ts
└── tailwind.config.js
```

### 7.2 WebSocket自动重连

```typescript
// src/services/websocket.ts

class GameWebSocket {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // 初始1s，指数退避
  private pendingActions: any[] = []; // 离线期间的操作队列

  connect(sessionId: string, token: string) {
    this.ws = new WebSocket(`ws://api/ws/v1/games/${sessionId}?token=${token}`);

    this.ws.onclose = () => {
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts);
        setTimeout(() => {
          this.reconnectAttempts++;
          this.connect(sessionId, token);
        }, delay);
      }
    };

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      // 重连成功后，发送离线期间的操作
      this.flushPendingActions();
    };
  }

  send(data: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      this.pendingActions.push(data); // 离线时缓存
    }
  }

  private flushPendingActions() {
    while (this.pendingActions.length > 0) {
      const action = this.pendingActions.shift()!;
      this.send(action);
    }
  }
}
```

---

## 八、部署方案

### 8.1 docker-compose.yml

```yaml
version: '3.8'

services:
  api:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:password@db:5432/ai_game
      - REDIS_URL=redis://redis:6379/0
      - CLAUDE_API_KEY=${CLAUDE_API_KEY}
      - CLAUDE_MODEL=claude-sonnet-4-6
    depends_on: [db, redis]

  web:
    build: ./frontend
    ports: ["3000:3000"]
    depends_on: [api]

  db:
    image: postgres:16-alpine
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=ai_game
    volumes: [postgres_data:/var/lib/postgresql/data]
    ports: ["5432:5432"]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  nginx:
    image: nginx:alpine
    ports: ["80:80", "443:443"]
    volumes: [./nginx.conf:/etc/nginx/nginx.conf]
    depends_on: [api, web]

volumes:
  postgres_data:
```

### 8.2 环境变量

```env
# 应用
APP_ENV=production
SECRET_KEY=your-secret-key
DEBUG=false

# 数据库
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/ai_game

# Redis
REDIS_URL=redis://localhost:6379/0

# AI
CLAUDE_API_KEY=sk-ant-api03-...
CLAUDE_MODEL=claude-sonnet-4-6
CLAUDE_MODEL_CRITICAL=claude-opus-4-7
CLAUDE_MAX_TOKENS=4096

# JWT
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# 文件存储
STORAGE_TYPE=oss
OSS_ACCESS_KEY=...
OSS_SECRET_KEY=...
OSS_BUCKET=ai-game-bucket

# 限流
RATE_LIMIT_API=100/minute
RATE_LIMIT_AI=30/minute
```

---

## 九、性能优化

| 优化点 | 措施 |
|--------|------|
| AI流式输出 | SSE/WebSocket流式返回AI回复，tool_use支持流式 |
| AI并发控制 | 信号量限制同时AI请求数（默认10） |
| AI响应缓存 | Redis缓存常见场景的标准回复（可选） |
| Prompt Caching | 系统提示词标记cache_control，减少token计费 |
| 图片懒加载 | 场景图片按需加载，预加载相邻场景 |
| 代码分割 | 按路由分割前端代码 |
| 数据库索引 | 为常用查询字段添加索引（见文档04） |
| 查询优化 | SQLAlchemy selectinload减少N+1查询 |
| Redis缓存 | 热点剧本数据、用户会话缓存 |
| 连接池 | 数据库连接池（20+10 overflow） |

---

## 十、API错误码

| 错误码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权（Token无效/过期） |
| 403 | 禁止访问 |
| 404 | 资源不存在 |
| 429 | 请求过于频繁 |
| 500 | 服务器内部错误 |
| 503 | AI服务不可用 |

---

## 文档修订记录

| 版本 | 日期 | 修订内容 | 修订人 |
|------|------|----------|--------|
| v1.0 | 2026-05-30 | 初始版本 | - |
| v2.0 | 2026-05-30 | 统一为FastAPI+PostgreSQL+SQLAlchemy 2.0 async；AI回复改用tool_use结构化输出替代文本标记解析；补充AI容错/重试/降级策略；补充JWT刷新机制/验证码方案/WebSocket握手验证；补充AI输入安全（长度限制/prompt注入防护）；模型配置化；补充WebSocket自动重连；删除aiohttp/MySQL相关内容 | - |
