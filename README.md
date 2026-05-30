# Alibi - 无限流AI互动游戏平台

基于 AI 驱动的互动文字冒险游戏平台，玩家通过选择和自由输入与 AI 生成的剧情互动。

## 技术栈

### 后端
- **FastAPI** + SQLAlchemy 2.0 async + PostgreSQL 16
- Anthropic Claude SDK (tool_use 结构化剧情输出)
- JWT 认证 + bcrypt 密码加密
- WebSocket 实时通信
- Redis 缓存 / Docker Compose 部署

### 前端
- **React 18** + TypeScript + Vite
- Ant Design (粉色主题) + Tailwind CSS
- Zustand 状态管理
- PixiJS 场景渲染 / A*寻路算法
- WebSocket + IndexedDB 离线存储

## 项目结构

```
Alibi/
├── backend/              # FastAPI 后端
│   ├── app/
│   │   ├── api/v1/       # API 路由 (auth, users, scripts, games, scenes, characters, ws, upload, achievements, leaderboards)
│   │   ├── core/         # 配置, 安全, 异常
│   │   ├── db/           # 数据库会话 + Base
│   │   ├── models/       # SQLAlchemy 模型
│   │   ├── schemas/      # Pydantic Schema
│   │   ├── services/     # 业务逻辑 (user, script, game, ai, scene, character, favorite, rating, file, achievement, leaderboard)
│   │   ├── middleware/    # 限流中间件
│   │   └── websocket/    # WebSocket 管理 + 处理器
│   ├── alembic/          # 数据库迁移
│   ├── docker-compose.yml
│   └── Dockerfile
├── frontend/             # React 前端
│   └── src/
│       ├── pages/        # Home, ScriptDetail, Game, Auth, Profile
│       ├── components/   # DialogBox, ChoiceMenu, SceneMap, CharacterPanel
│       ├── hooks/        # useAuth, useGame, useWebSocket, useScene
│       ├── stores/       # authStore, gameStore (Zustand)
│       ├── services/     # api, auth, scripts, games, scenes, characters, websocket
│       ├── utils/        # pathfinding (A*), offline (IndexedDB)
│       └── types/        # TypeScript 类型定义
├── docs/                 # 设计文档 01-11
└── .gitignore
```

## 快速开始

### 后端

```bash
cd backend
cp .env.example .env  # 编辑 .env 填入数据库和 API Key 配置
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

### Docker

```bash
cd backend
docker-compose up -d
```

## API 文档

启动后端后访问 `http://localhost:8000/docs` 查看 Swagger 文档。

## 设计文档

| 文档 | 内容 |
|------|------|
| 01 | 游戏概述与架构设计 |
| 02 | 场景地图与交互系统 |
| 03 | 前后端API与技术实现 |
| 04 | 技术栈更新与数据库设计 |
| 05 | 高级可爱风UI设计 |
| 06 | 场景与角色模块设计 |
| 07 | 剧本互动功能设计 |
| 08 | WebSocket与实时通信设计 |
| 09 | 中间件与文件上传设计 |
| 10 | 成就与排行榜设计 |
| 11 | 前端组件与交互设计 |