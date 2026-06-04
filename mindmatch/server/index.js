import express from 'express';
import cors from 'cors';
import { createServer } from 'http';
import { Server } from 'socket.io';
import dotenv from 'dotenv';
import rateLimit from 'express-rate-limit';

// 路由
import usersRouter from './src/routes/users.js';
import matchRouter from './src/routes/match.js';
import chatRouter from './src/routes/chat.js';
import aiRouter from './src/routes/ai.js';

// 中间件
import { errorHandler } from './src/middleware/errorHandler.js';

// 初始化数据库
import { initDatabase, seedDatabase } from './src/models/database.js';

// 配置
dotenv.config();

const app = express();
const httpServer = createServer(app);
const io = new Server(httpServer, {
  cors: {
    origin: process.env.ALLOWED_ORIGINS?.split(','),
    methods: ['GET', 'POST']
  }
});

// 中间件
app.use(cors({
  origin: process.env.ALLOWED_ORIGINS?.split(','),
  credentials: true
}));
app.use(express.json());

// 速率限制
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 100
});
app.use('/api/', limiter);

// API路由
app.use('/api/users', usersRouter);
app.use('/api/match', matchRouter);
app.use('/api/chat', chatRouter);
app.use('/api/ai', aiRouter);

// 健康检查
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Socket.IO
io.on('connection', (socket) => {
  console.log('用户连接:', socket.id);

  socket.on('userOnline', (userId) => {
    socket.userId = userId;
    io.emit('usersOnline', { userId, online: true });
  });

  socket.on('joinRoom', (roomId) => {
    socket.join(roomId);
    console.log(`用户 ${socket.id} 加入房间 ${roomId}`);
  });

  socket.on('sendMessage', (data) => {
    io.to(data.roomId).emit('newMessage', data);
  });

  socket.on('typing', (data) => {
    socket.to(data.roomId).emit('userTyping', {
      userId: socket.userId,
      isTyping: data.isTyping
    });
  });

  socket.on('disconnect', () => {
    if (socket.userId) {
      io.emit('usersOnline', { userId: socket.userId, online: false });
    }
    console.log('用户断开:', socket.id);
  });
});

// 错误处理
app.use(errorHandler);

// 启动服务器
async function start() {
  try {
    // 初始化数据库
    await initDatabase();
    
    // 添加种子数据
    await seedDatabase();

    const PORT = process.env.PORT || 4000;

    httpServer.listen(PORT, () => {
      console.log(`
╔═══════════════════════════════════════════╗
║                                           ║
║   🚀 MindMatch Server 运行中              ║
║   📡 端口: http://localhost:${PORT}         ║
║   🔌 Socket.IO: ws://localhost:${PORT}     ║
║                                           ║
╚═══════════════════════════════════════════╝
      `);
    });
  } catch (error) {
    console.error('启动失败:', error);
    process.exit(1);
  }
}

start();

export { io };
