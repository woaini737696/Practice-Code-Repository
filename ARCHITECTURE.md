# 心灵社交 (MindMatch) - 技术架构

## 1. 技术选型

### 1.1 技术栈概览

```
┌─────────────────────────────────────────────────────────┐
│                    技术架构图                            │
├─────────────────────────────────────────────────────────┤
│                                                          │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐          │
│   │  Web端   │    │ iOS端    │    │ Android端 │          │
│   │ (React)  │    │(ReactNav)│    │(ReactNav) │          │
│   └────┬─────┘    └────┬─────┘    └────┬─────┘          │
│        │               │               │                │
│        └───────────────┼───────────────┘                │
│                        │                                │
│                        ▼                                │
│              ┌──────────────────┐                      │
│              │   API Gateway    │                      │
│              │    (Express)     │                      │
│              └────────┬─────────┘                      │
│                       │                                 │
│        ┌──────────────┼──────────────┐                 │
│        ▼              ▼              ▼                 │
│   ┌─────────┐   ┌──────────┐   ┌──────────┐          │
│   │用户服务  │   │匹配服务   │   │聊天服务   │          │
│   │UsersAPI │   │Match API │   │Chat API  │          │
│   └────┬────┘   └────┬─────┘   └────┬─────┘          │
│        │              │              │                │
│        └──────────────┼──────────────┘                │
│                       │                                 │
│                       ▼                                 │
│              ┌──────────────────┐                      │
│              │    AI 服务层     │                      │
│              │ (OpenAI + LangChain)│                   │
│              └────────┬─────────┘                      │
│                       │                                 │
│                       ▼                                 │
│              ┌──────────────────┐                      │
│              │   数据存储层     │                      │
│              │  SQLite/Redis   │                      │
│              └──────────────────┘                      │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 1.2 核心技术选型

| 层级 | 技术 | 原因 |
|------|------|------|
| **前端** | React + Vite + TailwindCSS | 快速开发、响应式、热更新 |
| **移动端** | React Native (可选) | 代码复用、成熟生态 |
| **后端** | Node.js + Express | 轻量、JavaScript统一语言 |
| **AI服务** | OpenAI API / Claude API | 强大的LLM能力 |
| **数据库** | SQLite (开发) / PostgreSQL (生产) | 轻量、SQL完整性 |
| **缓存** | Redis | 高性能、会话存储 |
| **实时通信** | Socket.IO | 成熟的WebSocket方案 |
| **向量存储** | FAISS / ChromaDB | AI向量检索 |
| **部署** | Docker + Docker Compose | 容器化、快速部署 |

---

## 2. 项目结构

```
mindmatch/
├── web/                          # Web前端
│   ├── src/
│   │   ├── components/           # UI组件
│   │   │   ├── common/          # 通用组件
│   │   │   ├── match/           # 匹配组件
│   │   │   ├── chat/            # 聊天组件
│   │   │   ├── profile/         # 个人主页
│   │   │   └── ai/              # AI模块
│   │   ├── pages/               # 页面
│   │   ├── hooks/              # 自定义Hooks
│   │   ├── services/           # API服务
│   │   ├── stores/             # 状态管理
│   │   ├── utils/              # 工具函数
│   │   └── styles/             # 全局样式
│   ├── public/
│   ├── package.json
│   └── vite.config.js
│
├── server/                       # 后端服务
│   ├── src/
│   │   ├── routes/             # 路由
│   │   │   ├── users.js
│   │   │   ├── match.js
│   │   │   ├── chat.js
│   │   │   └── ai.js
│   │   ├── controllers/        # 控制器
│   │   ├── models/            # 数据模型
│   │   ├── services/          # 业务逻辑
│   │   │   ├── ai.service.js  # AI服务
│   │   │   └── match.service.js
│   │   ├── middleware/        # 中间件
│   │   ├── utils/             # 工具
│   │   └── config/            # 配置
│   ├── package.json
│   └── index.js
│
├── shared/                       # 共享代码
│   └── constants.js
│
├── docker-compose.yml
├── README.md
└── SPEC.md
```

---

## 3. API设计

### 3.1 用户模块

```javascript
// 用户注册
POST /api/users/register
Request: { phone, password, nickname }
Response: { user, token }

// 用户登录
POST /api/users/login
Request: { phone, password }
Response: { user, token }

// 获取用户资料
GET /api/users/profile
Headers: { Authorization: Bearer <token> }
Response: { user }

// 更新用户资料
PUT /api/users/profile
Request: { nickname, bio, interests }
Response: { user }

// 灵魂测试
POST /api/users/soul-test
Request: { answers: [...] }
Response: { soulType, tags, vector }

// 获取AI推荐匹配
GET /api/match/recommendations?limit=10
Response: { users: [...] }

// 滑动匹配
POST /api/match/swipe
Request: { targetUserId, action: 'like'|'pass' }
Response: { matched }
```

### 3.2 聊天模块

```javascript
// 获取聊天列表
GET /api/chat/list
Response: { chats: [...] }

// 获取聊天消息
GET /api/chat/:roomId/messages?limit=50
Response: { messages: [...] }

// 发送消息 (REST)
POST /api/chat/:roomId/messages

// WebSocket 实时消息
WS /ws/chat
Events: message, typing, read
```

### 3.3 AI模块 ⭐

```javascript
// AI对话
POST /api/ai/chat
Request: { 
  type: 'companion'|'advisor', 
  message, 
  conversationId? 
}
Response: { 
  reply, 
  conversationId,
  suggestions? 
}

// 获取AI推荐话题
GET /api/ai/topics
Response: { topics: [...] }

// AI社交建议
POST /api/ai/social-advice
Request: { context, goal }
Response: { suggestions: [...] }
```

---

## 4. 数据模型

### 4.1 核心表结构

```sql
-- 用户表
CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  uuid TEXT UNIQUE NOT NULL,
  phone TEXT UNIQUE,
  password_hash TEXT NOT NULL,
  nickname TEXT NOT NULL,
  avatar TEXT,
  gender TEXT CHECK(gender IN ('male','female','secret')),
  bio TEXT,
  soul_type TEXT,          -- MBTI类型
  soul_tags TEXT,          -- JSON数组
  soul_vector TEXT,        -- 向量数据
  interests TEXT,          -- JSON数组
  last_active DATETIME,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 匹配记录表
CREATE TABLE matches (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  target_id INTEGER NOT NULL,
  action TEXT CHECK(action IN ('like','pass')),
  matched_at DATETIME,
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (target_id) REFERENCES users(id)
);

-- 聊天会话表
CREATE TABLE chat_rooms (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  type TEXT DEFAULT 'single',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 聊天消息表
CREATE TABLE messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  room_id INTEGER NOT NULL,
  sender_id INTEGER NOT NULL,
  type TEXT DEFAULT 'text',
  content TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (room_id) REFERENCES chat_rooms(id),
  FOREIGN KEY (sender_id) REFERENCES users(id)
);

-- AI对话历史表
CREATE TABLE ai_conversations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  ai_type TEXT NOT NULL,   -- 'companion'|'advisor'
  messages TEXT NOT NULL,  -- JSON数组
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 灵魂测试记录表
CREATE TABLE soul_tests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  answers TEXT NOT NULL,   -- JSON
  result TEXT NOT NULL,    -- JSON
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id)
);
```

---

## 5. AI服务设计 ⭐

### 5.1 AI服务架构

```
┌─────────────────────────────────────────┐
│              AI 服务层                   │
├─────────────────────────────────────────┤
│                                          │
│  ┌────────────┐  ┌────────────┐         │
│  │ 意图识别   │  │ 情感分析   │         │
│  │ Classifier │  │ Analyzer   │         │
│  └─────┬──────┘  └─────┬──────┘         │
│        │               │                │
│        └───────┬───────┘                │
│                ▼                        │
│        ┌───────────────┐                │
│        │  Prompt工程   │                │
│        │  (Templates)  │                │
│        └───────┬───────┘                │
│                │                        │
│                ▼                        │
│        ┌───────────────┐                │
│        │  LLM 调用     │                │
│        │ OpenAI/Claude│                │
│        └───────┬───────┘                │
│                │                        │
│                ▼                        │
│        ┌───────────────┐                │
│        │ 安全过滤器    │                │
│        │ (Content Mod) │                │
│        └───────────────┘                │
│                                          │
└─────────────────────────────────────────┘
```

### 5.2 AI功能实现

#### 5.2.1 AI灵魂伴侣
```javascript
// prompt模板
const COMPANION_PROMPT = `
你是{soul_type}类型的{soul_tags}的灵魂伴侣。
你的性格特点：{personality_description}
你们共同的兴趣：{shared_interests}

角色设定：
- 温柔体贴，善解人意
- 喜欢深入交流
- 不会说教，会倾听
- 有自己的见解和个性

当前对话背景：{context}
用户说：{message}

请以灵魂伴侣的身份，用温暖自然的方式回复。
回复要求：
- 30-100字
- 符合角色性格
- 自然流畅
- 适当提问促进对话
`;
```

#### 5.2.2 AI社交助手
```javascript
// 社交建议prompt
const ADVISOR_PROMPT = `
用户遇到了社交场景：{scenario}
目标：{goal}

请给出3个具体的、可操作的社交建议。
格式：
1. [建议标题] 具体做法
2. [建议标题] 具体做法
3. [建议标题] 具体做法

注意：
- 针对内向者友好
- 实际可行
- 不做作不刻意
`;
```

---

## 6. 匹配算法

### 6.1 匹配度计算

```javascript
// 计算用户匹配度
function calculateMatchScore(userA, userB) {
  // 1. 性格相似度 (30%)
  const personalityScore = cosineSimilarity(
    JSON.parse(userA.soul_vector),
    JSON.parse(userB.soul_vector)
  ) * 0.3;

  // 2. 兴趣重合度 (40%)
  const interestScore = jaccardSimilarity(
    JSON.parse(userA.interests),
    JSON.parse(userB.interests)
  ) * 0.4;

  // 3. 活跃度匹配 (15%)
  const activityScore = activityCompatibility(
    userA.last_active,
    userB.last_active
  ) * 0.15;

  // 4. 历史交互反馈 (15%)
  const interactionScore = interactionFeedback(userA, userB) * 0.15;

  return {
    total: (personalityScore + interestScore + activityScore + interactionScore) * 100,
    breakdown: {
      personality: personalityScore * 100,
      interest: interestScore * 100,
      activity: activityScore * 100,
      interaction: interactionScore * 100
    }
  };
}
```

---

## 7. 部署架构

### 7.1 开发环境

```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build: ./web
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://localhost:4000
    volumes:
      - ./web:/app
      - /app/node_modules

  server:
    build: ./server
    ports:
      - "4000:4000"
    environment:
      - DATABASE_URL=sqlite:./data/mindmatch.db
      - REDIS_URL=redis://redis:6379
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./server:/app
      - ./data:/app/data
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  vector-db:
    image: chromadb/chroma:latest
    ports:
      - "8000:8000"
```

### 7.2 环境变量

```bash
# .env
NODE_ENV=development
PORT=4000

# 数据库
DATABASE_URL=sqlite:./data/mindmatch.db

# Redis
REDIS_URL=redis://localhost:6379

# AI服务
OPENAI_API_KEY=sk-xxxxx
OPENAI_BASE_URL=https://api.openai.com/v1
AI_MODEL=gpt-3.5-turbo

# JWT
JWT_SECRET=your-secret-key
JWT_EXPIRES_IN=7d

# CORS
ALLOWED_ORIGINS=http://localhost:3000
```

---

## 8. 安全措施

### 8.1 认证授权
- JWT Token认证
- 密码bcrypt加密
- 请求频率限制

### 8.2 AI内容安全
- 输入过滤（敏感词检测）
- 输出审核（内容分类）
- 对话时长限制
- 用户反馈机制

### 8.3 数据安全
- HTTPS加密传输
- SQL参数化查询
- 用户数据脱敏

---

## 9. 快速启动命令

```bash
# 1. 克隆项目
git clone <repo>
cd mindmatch

# 2. 配置环境变量
cp .env.example .env
# 编辑.env填入必要配置

# 3. Docker启动
docker-compose up -d

# 或手动启动
# 前端
cd web && npm install && npm run dev

# 后端
cd server && npm install && npm run dev

# 4. 访问
Web: http://localhost:3000
API: http://localhost:4000
```

---

*文档版本: v1.0*
