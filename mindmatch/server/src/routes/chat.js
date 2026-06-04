import { Router } from 'express';
import { dbGet, dbAll, dbRun } from '../models/database.js';
import { authMiddleware } from '../middleware/auth.js';

const router = Router();

// 获取聊天列表
router.get('/list', authMiddleware, (req, res) => {
  try {
    // 获取与当前用户相关的聊天
    const chats = dbAll(`
      SELECT 
        cr.id,
        cr.type,
        cr.created_at,
        u.id as partner_id,
        u.uuid as partner_uuid,
        u.nickname as partner_name,
        u.avatar as partner_avatar,
        (SELECT content FROM messages WHERE room_id = cr.id ORDER BY created_at DESC LIMIT 1) as last_message,
        (SELECT created_at FROM messages WHERE room_id = cr.id ORDER BY created_at DESC LIMIT 1) as last_time
      FROM chat_rooms cr
      JOIN messages msg ON cr.id = msg.room_id
      JOIN users u ON msg.sender_id = u.id AND u.id != ?
      WHERE cr.id IN (
        SELECT DISTINCT room_id FROM messages WHERE sender_id = ?
      )
      GROUP BY cr.id
      ORDER BY last_time DESC
    `, [req.userId, req.userId]);

    res.json({ chats });
  } catch (error) {
    console.error('获取聊天列表错误:', error);
    res.status(500).json({ error: '获取聊天列表失败' });
  }
});

// 获取聊天消息
router.get('/:roomId/messages', authMiddleware, (req, res) => {
  try {
    const { roomId } = req.params;
    const { limit = 50 } = req.query;

    const messages = dbAll(`
      SELECT m.*, u.nickname as sender_name, u.avatar as sender_avatar
      FROM messages m
      JOIN users u ON m.sender_id = u.id
      WHERE m.room_id = ?
      ORDER BY m.created_at DESC
      LIMIT ?
    `, [roomId, parseInt(limit)]);

    res.json({ messages: messages.reverse() });
  } catch (error) {
    console.error('获取消息错误:', error);
    res.status(500).json({ error: '获取消息失败' });
  }
});

// 发送消息
router.post('/:roomId/messages', authMiddleware, (req, res) => {
  try {
    const { roomId } = req.params;
    const { content, type = 'text' } = req.body;

    if (!content || content.trim() === '') {
      return res.status(400).json({ error: '消息内容不能为空' });
    }

    // 验证聊天室存在
    const room = dbGet('SELECT * FROM chat_rooms WHERE id = ?', [roomId]);
    if (!room) {
      return res.status(404).json({ error: '聊天室不存在' });
    }

    const result = dbRun(`
      INSERT INTO messages (room_id, sender_id, type, content)
      VALUES (?, ?, ?, ?)
    `, [roomId, req.userId, type, content]);

    const message = dbGet(`
      SELECT m.*, u.nickname as sender_name, u.avatar as sender_avatar
      FROM messages m
      JOIN users u ON m.sender_id = u.id
      WHERE m.id = ?
    `, [result.lastInsertRowid]);

    res.status(201).json({ message });
  } catch (error) {
    console.error('发送消息错误:', error);
    res.status(500).json({ error: '发送消息失败' });
  }
});

export default router;
