import { Router } from 'express';
import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import { v4 as uuidv4 } from 'uuid';
import { dbGet, dbAll, dbRun } from '../models/database.js';
import { authMiddleware } from '../middleware/auth.js';

const router = Router();

// 注册
router.post('/register', async (req, res) => {
  try {
    const { phone, password, nickname } = req.body;

    if (!phone || !password || !nickname) {
      return res.status(400).json({ error: '请填写所有必填字段' });
    }

    // 检查用户是否已存在
    const existing = dbGet('SELECT id FROM users WHERE phone = ?', [phone]);
    if (existing) {
      return res.status(400).json({ error: '该手机号已注册' });
    }

    // 加密密码
    const passwordHash = await bcrypt.hash(password, 10);

    // 创建用户
    const userUuid = uuidv4();
    const result = dbRun(`
      INSERT INTO users (uuid, phone, password_hash, nickname, avatar)
      VALUES (?, ?, ?, ?, ?)
    `, [
      userUuid,
      phone,
      passwordHash,
      nickname,
      `https://api.dicebear.com/7.x/avataaars/svg?seed=${nickname}`
    ]);

    const user = dbGet(`
      SELECT id, uuid, phone, nickname, avatar, created_at FROM users WHERE id = ?
    `, [result.lastInsertRowid]);

    // 生成Token
    const token = jwt.sign(
      { userId: user.id, uuid: user.uuid },
      process.env.JWT_SECRET,
      { expiresIn: process.env.JWT_EXPIRES_IN }
    );

    res.status(201).json({ user, token });
  } catch (error) {
    console.error('注册错误:', error);
    res.status(500).json({ error: '注册失败' });
  }
});

// 登录
router.post('/login', async (req, res) => {
  try {
    const { phone, password } = req.body;

    if (!phone || !password) {
      return res.status(400).json({ error: '请填写手机号和密码' });
    }

    const user = dbGet('SELECT * FROM users WHERE phone = ?', [phone]);
    if (!user) {
      return res.status(401).json({ error: '手机号或密码错误' });
    }

    const isValid = await bcrypt.compare(password, user.password_hash);
    if (!isValid) {
      return res.status(401).json({ error: '手机号或密码错误' });
    }

    // 更新最后活跃时间
    dbRun('UPDATE users SET last_active = datetime("now") WHERE id = ?', [user.id]);

    // 生成Token
    const token = jwt.sign(
      { userId: user.id, uuid: user.uuid },
      process.env.JWT_SECRET,
      { expiresIn: process.env.JWT_EXPIRES_IN }
    );

    // 移除敏感信息
    delete user.password_hash;

    res.json({ user, token });
  } catch (error) {
    console.error('登录错误:', error);
    res.status(500).json({ error: '登录失败' });
  }
});

// 获取用户资料
router.get('/profile', authMiddleware, (req, res) => {
  try {
    const user = dbGet(`
      SELECT id, uuid, nickname, avatar, gender, bio, soul_type, soul_tags, interests, last_active, created_at
      FROM users WHERE id = ?
    `, [req.userId]);

    if (!user) {
      return res.status(404).json({ error: '用户不存在' });
    }

    // 解析JSON字段
    if (user.soul_tags) user.soul_tags = JSON.parse(user.soul_tags);
    if (user.interests) user.interests = JSON.parse(user.interests);

    res.json({ user });
  } catch (error) {
    console.error('获取资料错误:', error);
    res.status(500).json({ error: '获取资料失败' });
  }
});

// 更新用户资料
router.put('/profile', authMiddleware, (req, res) => {
  try {
    const { nickname, avatar, gender, bio, interests, soul_type, soul_tags } = req.body;

    const updates = [];
    const values = [];

    if (nickname) {
      updates.push('nickname = ?');
      values.push(nickname);
    }
    if (avatar) {
      updates.push('avatar = ?');
      values.push(avatar);
    }
    if (gender) {
      updates.push('gender = ?');
      values.push(gender);
    }
    if (bio !== undefined) {
      updates.push('bio = ?');
      values.push(bio);
    }
    if (interests) {
      updates.push('interests = ?');
      values.push(JSON.stringify(interests));
    }
    if (soul_type) {
      updates.push('soul_type = ?');
      values.push(soul_type);
    }
    if (soul_tags) {
      updates.push('soul_tags = ?');
      values.push(JSON.stringify(soul_tags));
    }

    if (updates.length === 0) {
      return res.status(400).json({ error: '没有要更新的字段' });
    }

    updates.push('updated_at = datetime("now")');
    values.push(req.userId);

    dbRun(`UPDATE users SET ${updates.join(', ')} WHERE id = ?`, values);

    const user = dbGet(`
      SELECT id, uuid, nickname, avatar, gender, bio, soul_type, soul_tags, interests, last_active, created_at
      FROM users WHERE id = ?
    `, [req.userId]);

    if (user.soul_tags) user.soul_tags = JSON.parse(user.soul_tags);
    if (user.interests) user.interests = JSON.parse(user.interests);

    res.json({ user });
  } catch (error) {
    console.error('更新资料错误:', error);
    res.status(500).json({ error: '更新资料失败' });
  }
});

// 灵魂测试
router.post('/soul-test', authMiddleware, (req, res) => {
  try {
    const { answers } = req.body;

    if (!answers || !Array.isArray(answers)) {
      return res.status(400).json({ error: '请提供有效的测试答案' });
    }

    // 简化的MBTI判定逻辑
    const scores = { E: 0, I: 0, S: 0, N: 0, T: 0, F: 0, J: 0, P: 0 };
    
    answers.forEach((answer, index) => {
      const dimension = index % 4;
      switch (dimension) {
        case 0: answer > 3 ? scores.E++ : scores.I++; break;
        case 1: answer > 3 ? scores.S++ : scores.N++; break;
        case 2: answer > 3 ? scores.T++ : scores.F++; break;
        case 3: answer > 3 ? scores.J++ : scores.P++; break;
      }
    });

    const soulType = (
      (scores.E > scores.I ? 'E' : 'I') +
      (scores.S > scores.N ? 'S' : 'N') +
      (scores.T > scores.F ? 'T' : 'F') +
      (scores.J > scores.P ? 'J' : 'P')
    );

    // 生成灵魂标签
    const tagOptions = [
      ['理想主义者', '梦想家', '文艺青年'],
      ['务实派', '行动者', '效率达人'],
      ['思想者', '分析家', '好奇心强'],
      ['社交蝴蝶', '活跃分子', '气氛组'],
      ['安静内敛', '深度思考者', '倾听者'],
      ['温暖体贴', '治愈系', '小太阳']
    ];

    const soulTags = tagOptions[Math.floor(Math.random() * tagOptions.length)];
    const soulVector = JSON.stringify(Array(8).fill(0).map(() => Math.random()));

    // 更新用户
    dbRun(`
      UPDATE users 
      SET soul_type = ?, soul_tags = ?, soul_vector = ?
      WHERE id = ?
    `, [soulType, JSON.stringify(soulTags), soulVector, req.userId]);

    // 保存测试记录
    dbRun(`
      INSERT INTO soul_tests (user_id, answers, result)
      VALUES (?, ?, ?)
    `, [req.userId, JSON.stringify(answers), JSON.stringify({ soulType, soulTags })]);

    res.json({
      soulType,
      soulTags,
      message: `你是 ${soulType} 类型的人！`
    });
  } catch (error) {
    console.error('灵魂测试错误:', error);
    res.status(500).json({ error: '测试失败' });
  }
});

export default router;
