import { Router } from 'express';
import { dbGet, dbAll, dbRun } from '../models/database.js';
import { authMiddleware } from '../middleware/auth.js';
import { aiService } from '../services/ai.service.js';

const router = Router();

// AI对话
router.post('/chat', authMiddleware, async (req, res) => {
  try {
    const { type = 'companion', message, conversationId } = req.body;

    if (!message || message.trim() === '') {
      return res.status(400).json({ error: '消息不能为空' });
    }

    // 获取用户信息
    const user = dbGet(`
      SELECT id, nickname, soul_type, soul_tags, interests, bio
      FROM users WHERE id = ?
    `, [req.userId]);

    if (!user) {
      return res.status(404).json({ error: '用户不存在' });
    }

    // 解析JSON字段
    if (user.soul_tags) user.soul_tags = JSON.parse(user.soul_tags);
    if (user.interests) user.interests = JSON.parse(user.interests);

    // 获取或创建对话历史
    let convId = conversationId;
    let conversationHistory = [];

    if (convId) {
      const conversation = dbGet('SELECT * FROM ai_conversations WHERE id = ? AND user_id = ?', [convId, req.userId]);
      
      if (conversation) {
        conversationHistory = JSON.parse(conversation.messages);
      }
    } else {
      // 创建新对话
      const result = dbRun(`
        INSERT INTO ai_conversations (user_id, ai_type, messages)
        VALUES (?, ?, ?)
      `, [req.userId, type, '[]']);
      convId = result.lastInsertRowid;
    }

    // 添加用户消息到历史
    conversationHistory.push({
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    });

    // 调用AI服务
    const aiResponse = await aiService.chat({
      type,
      user,
      message,
      history: conversationHistory
    });

    // 添加AI回复到历史
    conversationHistory.push({
      role: 'assistant',
      content: aiResponse.reply,
      timestamp: new Date().toISOString()
    });

    // 更新对话历史
    dbRun(`
      UPDATE ai_conversations SET messages = ?, updated_at = datetime("now") WHERE id = ?
    `, [JSON.stringify(conversationHistory), convId]);

    res.json({
      reply: aiResponse.reply,
      conversationId: convId,
      suggestions: aiResponse.suggestions || []
    });
  } catch (error) {
    console.error('AI对话错误:', error);
    res.status(500).json({ 
      error: 'AI服务暂时不可用',
      reply: '抱歉，AI服务暂时遇到了问题，请稍后再试。'
    });
  }
});

// 获取AI对话历史
router.get('/history', authMiddleware, (req, res) => {
  try {
    const { type } = req.query;
    
    let query = 'SELECT * FROM ai_conversations WHERE user_id = ?';
    const params = [req.userId];

    if (type) {
      query += ' AND ai_type = ?';
      params.push(type);
    }

    query += ' ORDER BY updated_at DESC LIMIT 20';

    const conversations = dbAll(query, params);

    res.json({ conversations });
  } catch (error) {
    console.error('获取对话历史错误:', error);
    res.status(500).json({ error: '获取对话历史失败' });
  }
});

// 获取社交建议
router.post('/social-advice', authMiddleware, async (req, res) => {
  try {
    const { context, goal } = req.body;

    const advice = await aiService.getSocialAdvice(context, goal);

    res.json({ advice });
  } catch (error) {
    console.error('获取社交建议错误:', error);
    res.status(500).json({ error: '获取建议失败' });
  }
});

// 获取开场白建议
router.get('/opening-lines', authMiddleware, (req, res) => {
  try {
    const user = dbGet(`
      SELECT soul_type, soul_tags, interests, bio FROM users WHERE id = ?
    `, [req.userId]);

    if (user.soul_tags) user.soul_tags = JSON.parse(user.soul_tags);
    if (user.interests) user.interests = JSON.parse(user.interests);

    const lines = aiService.getOpeningLines(user);

    res.json({ openingLines: lines });
  } catch (error) {
    console.error('获取开场白错误:', error);
    res.status(500).json({ error: '获取开场白失败' });
  }
});

// 获取推荐话题
router.get('/topics', authMiddleware, (req, res) => {
  try {
    const user = dbGet(`
      SELECT interests FROM users WHERE id = ?
    `, [req.userId]);

    const interests = user && user.interests ? JSON.parse(user.interests) : [];

    const topics = [
      { icon: '🎵', title: '最近在听什么歌', category: 'music' },
      { icon: '🎬', title: '最近看了什么电影', category: 'movie' },
      { icon: '📚', title: '最近在读什么书', category: 'book' },
      { icon: '✈️', title: '最想去哪里旅行', category: 'travel' },
      { icon: '🍜', title: '最喜欢的美食', category: 'food' },
      { icon: '🎮', title: '平时玩什么游戏', category: 'game' },
      { icon: '🏃', title: '平时有什么爱好', category: 'hobby' },
      { icon: '💼', title: '工作和学习', category: 'work' },
      ...(interests.length > 0 ? interests.map(i => ({ icon: '✨', title: `关于${i}`, category: 'interest' })) : [])
    ];

    res.json({ topics: topics.slice(0, 8) });
  } catch (error) {
    console.error('获取话题错误:', error);
    res.status(500).json({ error: '获取话题失败' });
  }
});

export default router;
