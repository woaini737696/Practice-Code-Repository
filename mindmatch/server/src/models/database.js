import initSqlJs from 'sql.js';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';
import bcrypt from 'bcryptjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const dataDir = join(__dirname, '../../data');
const dbPath = join(dataDir, 'mindmatch.db');

// 确保数据目录存在
if (!existsSync(dataDir)) {
  mkdirSync(dataDir, { recursive: true });
}

let db = null;

// 初始化数据库
export async function initDatabase() {
  const SQL = await initSqlJs();

  // 尝试读取现有数据库
  if (existsSync(dbPath)) {
    const buffer = readFileSync(dbPath);
    db = new SQL.Database(buffer);
    console.log('✅ 数据库加载成功');
  } else {
    db = new SQL.Database();
    console.log('✅ 新数据库创建成功');
  }

  // 创建表
  db.run(`
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      uuid TEXT UNIQUE NOT NULL,
      phone TEXT UNIQUE,
      password_hash TEXT NOT NULL,
      nickname TEXT NOT NULL,
      avatar TEXT,
      gender TEXT DEFAULT 'secret',
      bio TEXT,
      soul_type TEXT,
      soul_tags TEXT,
      soul_vector TEXT,
      interests TEXT,
      last_active TEXT DEFAULT CURRENT_TIMESTAMP,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
  `);

  db.run(`
    CREATE TABLE IF NOT EXISTS matches (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL,
      target_id INTEGER NOT NULL,
      action TEXT NOT NULL,
      matched_at TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      UNIQUE(user_id, target_id)
    )
  `);

  db.run(`
    CREATE TABLE IF NOT EXISTS chat_rooms (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      type TEXT DEFAULT 'single',
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
  `);

  db.run(`
    CREATE TABLE IF NOT EXISTS messages (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      room_id INTEGER NOT NULL,
      sender_id INTEGER NOT NULL,
      type TEXT DEFAULT 'text',
      content TEXT NOT NULL,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
  `);

  db.run(`
    CREATE TABLE IF NOT EXISTS ai_conversations (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL,
      ai_type TEXT NOT NULL,
      messages TEXT NOT NULL,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
  `);

  db.run(`
    CREATE TABLE IF NOT EXISTS soul_tests (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL,
      answers TEXT NOT NULL,
      result TEXT NOT NULL,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
  `);

  // 创建索引
  try {
    db.run('CREATE INDEX IF NOT EXISTS idx_users_soul_type ON users(soul_type)');
    db.run('CREATE INDEX IF NOT EXISTS idx_matches_user ON matches(user_id)');
    db.run('CREATE INDEX IF NOT EXISTS idx_messages_room ON messages(room_id)');
  } catch (e) {
    // 索引可能已存在
  }

  saveDatabase();
  console.log('✅ 数据库初始化完成');

  return db;
}

// 保存数据库到文件
export function saveDatabase() {
  if (db) {
    const data = db.export();
    const buffer = Buffer.from(data);
    writeFileSync(dbPath, buffer);
  }
}

// 数据库查询助手
export function dbGet(query, params = []) {
  const stmt = db.prepare(query);
  stmt.bind(params);
  if (stmt.step()) {
    const row = stmt.getAsObject();
    stmt.free();
    return row;
  }
  stmt.free();
  return null;
}

export function dbAll(query, params = []) {
  const results = [];
  const stmt = db.prepare(query);
  stmt.bind(params);
  while (stmt.step()) {
    results.push(stmt.getAsObject());
  }
  stmt.free();
  return results;
}

export function dbRun(query, params = []) {
  db.run(query, params);
  saveDatabase();
  return { lastInsertRowid: db.exec("SELECT last_insert_rowid()")[0]?.values[0]?.[0] || 0 };
}

// 种子数据
export async function seedDatabase() {
  const userCount = dbGet('SELECT COUNT(*) as count FROM users');

  if (userCount && userCount.count > 0) {
    console.log('📊 数据库已有数据，跳过种子数据');
    return;
  }

  console.log('📊 开始创建种子数据...');

  const soulTypes = ['INFP', 'ENFP', 'INTJ', 'ENTP', 'ISFJ', 'ESFJ', 'ISTP', 'ESTP'];
  const interests = [
    ['阅读', '电影', '音乐', '旅行'],
    ['摄影', '美食', '健身', '游戏'],
    ['编程', '设计', '写作', '音乐'],
    ['旅行', '探险', '摄影', '户外'],
    ['艺术', '展览', '电影', '阅读'],
    ['音乐', '舞蹈', '表演', '社交']
  ];
  const tags = [
    ['文艺青年', '梦想家', '理想主义者'],
    ['活跃', '社交达人', '幽默'],
    ['理性', '独立', '思考者'],
    ['创意', '好奇', '爱冒险'],
    ['温柔', '体贴', '倾听者'],
    ['热情', '开朗', '乐天派']
  ];

  const defaultPassword = await bcrypt.hash('123456', 10);

  const users = [
    { nickname: '星空漫步者', gender: 'secret', bio: '在星空下寻找灵魂的共鸣', soul: 0 },
    { nickname: '月光诗人', gender: 'secret', bio: '用文字编织梦想的年轻人', soul: 1 },
    { nickname: '晨曦旅人', gender: 'secret', bio: '热爱生活的探险家', soul: 2 },
    { nickname: '云端幻想家', gender: 'secret', bio: '幻想是心灵的翅膀', soul: 3 },
    { nickname: '深海探索者', gender: 'secret', bio: '探索未知是我的本能', soul: 4 },
    { nickname: '山谷回声', gender: 'secret', bio: '愿我的声音能触动你心', soul: 5 },
  ];

  for (const user of users) {
    const { v4: uuidv4 } = await import('uuid');
    const soulIdx = user.soul;
    const soulVector = JSON.stringify(Array(8).fill(0).map(() => Math.random()));

    dbRun(`
      INSERT INTO users (uuid, nickname, password_hash, avatar, gender, bio, soul_type, soul_tags, interests, soul_vector)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `, [
      uuidv4(),
      user.nickname,
      defaultPassword,
      `https://api.dicebear.com/7.x/avataaars/svg?seed=${user.nickname}`,
      user.gender,
      user.bio,
      soulTypes[soulIdx],
      JSON.stringify(tags[soulIdx]),
      JSON.stringify(interests[soulIdx]),
      soulVector
    ]);
  }

  console.log('✅ 种子数据创建完成，已创建 6 个测试用户');
  console.log('📝 测试账号: 任意用户的手机号注册即可 (密码: 123456)');
}

export { db };
