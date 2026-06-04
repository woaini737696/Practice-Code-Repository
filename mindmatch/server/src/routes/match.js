import { Router } from 'express';
import { dbGet, dbAll, dbRun } from '../models/database.js';
import { authMiddleware } from '../middleware/auth.js';

const router = Router();

// 获取推荐匹配列表
router.get('/recommendations', authMiddleware, (req, res) => {
  try {
    const { limit = 10 } = req.query;

    // 获取当前用户的灵魂向量
    const currentUser = dbGet('SELECT soul_vector, interests FROM users WHERE id = ?', [req.userId]);
    
    if (!currentUser || !currentUser.soul_vector) {
      return res.json({ 
        users: [],
        message: '请先完成灵魂测试以获得更好的匹配推荐'
      });
    }

    const currentVector = JSON.parse(currentUser.soul_vector);
    const currentInterests = currentUser.interests ? JSON.parse(currentUser.interests) : [];

    // 获取已匹配和已拒绝的用户ID
    const existingActions = dbAll('SELECT target_id FROM matches WHERE user_id = ?', [req.userId]);
    const excludeIds = existingActions.map(m => m.target_id);
    excludeIds.push(req.userId); // 排除自己

    // 获取潜在匹配用户
    const placeholders = excludeIds.length > 0 
      ? `AND id NOT IN (${excludeIds.map(() => '?').join(',')})` 
      : '';
    
    const candidates = dbAll(`
      SELECT id, uuid, nickname, avatar, gender, bio, soul_type, soul_tags, interests, last_active
      FROM users
      WHERE soul_vector IS NOT NULL ${placeholders}
      LIMIT ?
    `, [...excludeIds, parseInt(limit)]);

    // 计算匹配度
    const recommendations = candidates.map(candidate => {
      let matchScore = 0;
      
      if (candidate.soul_vector) {
        const candidateVector = JSON.parse(candidate.soul_vector);
        // 简化的余弦相似度
        let dotProduct = 0;
        let normA = 0;
        let normB = 0;
        
        for (let i = 0; i < currentVector.length; i++) {
          dotProduct += currentVector[i] * candidateVector[i];
          normA += currentVector[i] * currentVector[i];
          normB += candidateVector[i] * candidateVector[i];
        }
        
        const similarity = dotProduct / (Math.sqrt(normA) * Math.sqrt(normB) || 1);
        matchScore = Math.round((similarity + 1) / 2 * 100); // 转换为0-100
      }

      const candidateInterests = candidate.interests ? JSON.parse(candidate.interests) : [];
      const commonInterests = currentInterests.filter(i => candidateInterests.includes(i));

      return {
        ...candidate,
        soul_tags: candidate.soul_tags ? JSON.parse(candidate.soul_tags) : [],
        interests: candidateInterests,
        matchScore,
        commonInterests
      };
    });

    // 按匹配度排序
    recommendations.sort((a, b) => b.matchScore - a.matchScore);

    res.json({ users: recommendations });
  } catch (error) {
    console.error('获取推荐错误:', error);
    res.status(500).json({ error: '获取推荐失败' });
  }
});

// 滑动匹配
router.post('/swipe', authMiddleware, (req, res) => {
  try {
    const { targetId, action } = req.body;

    if (!targetId || !['like', 'pass'].includes(action)) {
      return res.status(400).json({ error: '无效的操作' });
    }

    // 检查目标用户是否存在
    const targetUser = dbGet('SELECT id FROM users WHERE id = ?', [targetId]);
    if (!targetUser) {
      return res.status(404).json({ error: '用户不存在' });
    }

    // 记录匹配行为
    const existingMatch = dbGet('SELECT id FROM matches WHERE user_id = ? AND target_id = ?', [req.userId, targetId]);

    if (existingMatch) {
      return res.json({ matched: false, message: '已处理过此匹配' });
    }

    dbRun('INSERT INTO matches (user_id, target_id, action) VALUES (?, ?, ?)', [req.userId, targetId, action]);

    let matched = false;

    // 如果是喜欢，检查是否双向喜欢
    if (action === 'like') {
      const mutualLike = dbGet('SELECT id FROM matches WHERE user_id = ? AND target_id = ? AND action = ?', [targetId, req.userId, 'like']);

      if (mutualLike) {
        matched = true;
        
        // 更新匹配记录
        dbRun('UPDATE matches SET matched_at = datetime("now") WHERE user_id = ? AND target_id = ?', [req.userId, targetId]);
        dbRun('UPDATE matches SET matched_at = datetime("now") WHERE user_id = ? AND target_id = ?', [targetId, req.userId]);

        // 创建聊天房间
        const result = dbRun('INSERT INTO chat_rooms (type) VALUES (?)', ['single']);
        
        // 初始化聊天消息
        dbRun(`
          INSERT INTO messages (room_id, sender_id, type, content)
          VALUES (?, ?, ?, ?)
        `, [result.lastInsertRowid, req.userId, 'system', JSON.stringify({
          type: 'match',
          message: '你们匹配成功了！开始聊天吧~'
        })]);
      }
    }

    res.json({ 
      matched,
      message: matched ? '恭喜！匹配成功' : action === 'like' ? '等待对方喜欢' : '已跳过'
    });
  } catch (error) {
    console.error('滑动匹配错误:', error);
    res.status(500).json({ error: '匹配失败' });
  }
});

// 获取已匹配用户
router.get('/mutual', authMiddleware, (req, res) => {
  try {
    const matches = dbAll(`
      SELECT DISTINCT u.id, u.uuid, u.nickname, u.avatar, u.bio, u.soul_type, u.soul_tags,
             m.matched_at
      FROM matches m
      JOIN users u ON m.target_id = u.id
      WHERE m.user_id = ? AND m.matched_at IS NOT NULL
      ORDER BY m.matched_at DESC
    `, [req.userId]);

    res.json({ matches });
  } catch (error) {
    console.error('获取匹配错误:', error);
    res.status(500).json({ error: '获取匹配列表失败' });
  }
});

export default router;
