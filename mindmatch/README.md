# 心灵社交 MindMatch

一款类似Soul的AI社交应用，具备灵魂匹配和AI伴侣功能。

## 功能特性

### 核心功能
- ✅ 用户注册/登录
- ✅ 灵魂测试（MBTI风格）
- ✅ 智能匹配推荐
- ✅ 滑动匹配
- ✅ 即时聊天
- ✅ 个人资料管理

### AI交友模块 ⭐
- **AI灵魂伴侣**: 24/7陪伴对话，情感支持
- **AI社交助手**: 社交建议、话题推荐、聊天技巧
- **智能对话**: 基于用户性格的个性化交流

## 快速开始

### 1. 安装依赖

```bash
# 后端
cd server
npm install

# 前端
cd web
npm install
```

### 2. 配置环境

复制 `.env.example` 为 `.env` 并配置：

```bash
cp .env.example .env
```

如果需要AI功能，配置OpenAI API Key：
```bash
OPENAI_API_KEY=sk-your-key-here
```

### 3. 启动服务

```bash
# 终端1: 启动后端 (端口4000)
cd server
npm run dev

# 终端2: 启动前端 (端口5173)
cd web
npm run dev
```

### 4. 访问应用

打开浏览器访问: http://localhost:5173

## 技术栈

### 前端
- React 18
- Vite
- Tailwind CSS
- Framer Motion
- Zustand (状态管理)
- Socket.IO Client

### 后端
- Node.js
- Express
- SQLite
- Socket.IO
- JWT认证
- OpenAI API (可选)

## API接口

### 用户模块
- `POST /api/users/register` - 注册
- `POST /api/users/login` - 登录
- `GET /api/users/profile` - 获取资料
- `PUT /api/users/profile` - 更新资料
- `POST /api/users/soul-test` - 灵魂测试

### 匹配模块
- `GET /api/match/recommendations` - 获取推荐
- `POST /api/match/swipe` - 滑动匹配
- `GET /api/match/mutual` - 已匹配列表

### 聊天模块
- `GET /api/chat/list` - 聊天列表
- `GET /api/chat/:roomId/messages` - 消息历史
- `POST /api/chat/:roomId/messages` - 发送消息

### AI模块 ⭐
- `POST /api/ai/chat` - AI对话
- `GET /api/ai/topics` - 推荐话题
- `POST /api/ai/social-advice` - 社交建议

## 项目结构

```
mindmatch/
├── web/                 # React前端
│   ├── src/
│   │   ├── components/ # UI组件
│   │   ├── pages/      # 页面
│   │   ├── stores/     # 状态管理
│   │   ├── services/   # API服务
│   │   └── styles/     # 样式
│   └── package.json
│
├── server/              # Node.js后端
│   ├── src/
│   │   ├── routes/     # 路由
│   │   ├── services/   # 业务逻辑
│   │   ├── models/     # 数据模型
│   │   └── middleware/  # 中间件
│   └── package.json
│
├── .env                 # 环境变量
└── README.md
```

## 设计文档

- [产品设计规范](./SPEC.md)
- [技术架构方案](./ARCHITECTURE.md)

## License

MIT
