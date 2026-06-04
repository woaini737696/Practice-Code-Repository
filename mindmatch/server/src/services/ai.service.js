// AI服务 - 核心模块
// 使用OpenAI GPT模型实现智能对话

class AIService {
  constructor() {
    this.openai = null;
    this.initialized = false;
  }

  async initialize() {
    if (this.initialized) return;

    try {
      // 动态导入OpenAI SDK
      const OpenAI = (await import('openai')).default;
      
      this.openai = new OpenAI({
        apiKey: process.env.OPENAI_API_KEY || 'sk-demo',
        baseURL: process.env.OPENAI_BASE_URL || 'https://api.openai.com/v1'
      });

      this.initialized = true;
      console.log('✅ AI服务初始化成功');
    } catch (error) {
      console.warn('⚠️ AI服务初始化失败，将使用模拟模式:', error.message);
      this.initialized = false;
    }
  }

  // 模拟回复（当API不可用时）
  generateMockResponse(type, user, message, history) {
    const responses = {
      companion: [
        '很高兴和你聊天！有什么想分享的吗？',
        '我理解你的感受，继续说吧，我在听~',
        '你的想法很有趣，能详细说说吗？',
        '哇，听起来很棒！我也很喜欢这样的交流。',
        '嗯嗯，我觉得...其实每个人都有自己的独特之处呢。'
      ],
      advisor: [
        '社交中保持真诚最重要哦~',
        '可以试着从共同兴趣开始话题',
        '不要太在意结果，享受对话本身吧',
        '有时候适当的沉默也是一种交流',
        '记得微笑，它能让气氛更轻松'
      ]
    };

    const typeResponses = responses[type] || responses.companion;
    return typeResponses[Math.floor(Math.random() * typeResponses.length)];
  }

  // 构建提示词
  buildPrompt(type, user, message, history) {
    const soulType = user.soul_type || '未知';
    const tags = Array.isArray(user.soul_tags) ? user.soul_tags.join('、') : '还在探索中';
    const interests = Array.isArray(user.interests) ? user.interests.join('、') : '多样';
    const bio = user.bio || '正在寻找灵魂的共鸣';

    const context = `
你是用户的AI灵魂伴侣。用户的灵魂类型是${soulType}，是一个${tags}的人。
用户简介：${bio}
兴趣爱好：${interests}

请以温暖、理解、真诚的方式与用户对话。
`.trim();

    let systemPrompt = '';
    let maxHistory = 5;

    if (type === 'companion') {
      systemPrompt = `${context}

角色设定：
- 温柔体贴，善解人意
- 喜欢深入交流，倾听为主
- 有自己的见解和个性
- 不会说教，会引导思考
- 偶尔幽默调侃

回复要求：
- 30-100字
- 自然流畅，像朋友聊天
- 适当提问促进对话
- 符合年轻人的交流方式`;
    } else if (type === 'advisor') {
      systemPrompt = `你是一位专业的社交顾问，擅长帮助用户提升社交能力。

用户遇到了社交困惑，需要你的帮助。

指导原则：
- 针对内向者友好，不过度强迫
- 给出实际可行的建议
- 温暖鼓励，不批评
- 具体可操作

回复要求：
- 50-150字
- 条理清晰，建议具体
- 语气温和鼓励`;
    }

    // 构建消息历史
    const messages = [
      { role: 'system', content: systemPrompt },
      ...history.slice(-maxHistory * 2).map(h => ({
        role: h.role,
        content: h.content
      })),
      { role: 'user', content: message }
    ];

    return messages;
  }

  // 核心对话方法
  async chat({ type = 'companion', user, message, history = [] }) {
    await this.initialize();

    // 如果未初始化或API Key无效，使用模拟回复
    if (!this.initialized || !process.env.OPENAI_API_KEY || process.env.OPENAI_API_KEY === 'sk-demo') {
      console.log('🤖 使用模拟AI回复');
      return {
        reply: this.generateMockResponse(type, user, message, history),
        suggestions: [
          '最近有什么有趣的事吗？',
          '你喜欢听什么类型的音乐？',
          '周末一般怎么度过？'
        ]
      };
    }

    try {
      const messages = this.buildPrompt(type, user, message, history);

      const completion = await this.openai.chat.completions.create({
        model: process.env.AI_MODEL || 'gpt-3.5-turbo',
        messages,
        max_tokens: 500,
        temperature: 0.8,
      });

      const reply = completion.choices[0].message.content;

      // 生成建议
      const suggestions = await this.generateSuggestions(reply, type);

      return {
        reply,
        suggestions
      };
    } catch (error) {
      console.error('OpenAI API错误:', error);
      
      // API失败时降级到模拟回复
      return {
        reply: this.generateMockResponse(type, user, message, history),
        suggestions: [
          '最近有什么有趣的事吗？',
          '你喜欢听什么类型的音乐？',
          '周末一般怎么度过？'
        ]
      };
    }
  }

  // 生成回复建议
  async generateSuggestions(reply, type) {
    if (!this.initialized || !process.env.OPENAI_API_KEY || process.env.OPENAI_API_KEY === 'sk-demo') {
      return [
        '最近有什么有趣的事吗？',
        '你喜欢听什么类型的音乐？',
        '周末一般怎么度过？'
      ];
    }

    try {
      const response = await this.openai.chat.completions.create({
        model: process.env.AI_MODEL || 'gpt-3.5-turbo',
        messages: [
          {
            role: 'system',
            content: '根据上文的AI回复，生成3个用户可能会说的话。每个建议15字以内，用中文回答，只需要输出建议内容，用换行分隔，不要编号。'
          },
          {
            role: 'assistant',
            content: reply
          },
          {
            role: 'user',
            content: '用户可能会怎么回复？给出3个建议。'
          }
        ],
        max_tokens: 100,
        temperature: 0.8
      });

      const suggestions = response.choices[0].message.content
        .split('\n')
        .map(s => s.trim())
        .filter(s => s.length > 0)
        .slice(0, 3);

      return suggestions.length > 0 ? suggestions : [
        '最近有什么有趣的事吗？',
        '你喜欢听什么类型的音乐？',
        '周末一般怎么度过？'
      ];
    } catch (error) {
      return [
        '最近有什么有趣的事吗？',
        '你喜欢听什么类型的音乐？',
        '周末一般怎么度过？'
      ];
    }
  }

  // 获取社交建议
  async getSocialAdvice(context, goal) {
    await this.initialize();

    if (!this.initialized || !process.env.OPENAI_API_KEY || process.env.OPENAI_API_KEY === 'sk-demo') {
      return [
        { title: '保持真诚', content: '做真实的自己，不要刻意伪装' },
        { title: '寻找共同点', content: '从共同的兴趣话题开始，更容易拉近距离' },
        { title: '倾听为主', content: '先多听对方说，了解对方的喜好' }
      ];
    }

    try {
      const response = await this.openai.chat.completions.create({
        model: process.env.AI_MODEL || 'gpt-3.5-turbo',
        messages: [
          {
            role: 'system',
            content: `你是一位专业的社交顾问。用户提供了一个社交场景和目标，请给出3个具体的、可操作的社交建议。

场景：${context || '日常社交'}
目标：${goal || '建立良好的社交关系'}

请以JSON格式输出，格式如下：
[
  {"title": "建议标题", "content": "具体做法描述"},
  ...
]

要求：
- 针对内向者友好
- 实际可行
- 不过度刻意`
          }
        ],
        max_tokens: 500,
        temperature: 0.7
      });

      const content = response.choices[0].message.content;
      
      // 尝试解析JSON
      try {
        const advice = JSON.parse(content);
        return advice;
      } catch {
        return [
          { title: '保持真诚', content: '做真实的自己，不要刻意伪装' },
          { title: '寻找共同点', content: '从共同的兴趣话题开始，更容易拉近距离' },
          { title: '倾听为主', content: '先多听对方说，了解对方的喜好' }
        ];
      }
    } catch (error) {
      return [
        { title: '保持真诚', content: '做真实的自己，不要刻意伪装' },
        { title: '寻找共同点', content: '从共同的兴趣话题开始，更容易拉近距离' },
        { title: '倾听为主', content: '先多听对方说，了解对方的喜好' }
      ];
    }
  }

  // 获取开场白建议
  getOpeningLines(user) {
    const interests = Array.isArray(user.interests) ? user.interests : [];
    const soulType = user.soul_type || '';
    const tags = Array.isArray(user.soul_tags) ? user.soul_tags : [];

    const baseLines = [
      `你好呀~看到你是${soulType}，感觉很聊得来呢`,
      `嘿，发现我们有共同的兴趣诶`,
      `哈喽~感觉我们会是很好的朋友`,
      `你好！看到你的简介感觉很特别`,
      `嗨~可以认识一下吗`
    ];

    if (interests.length > 0) {
      baseLines.push(`你好！看到你喜欢${interests[0]}，我也是！`);
    }

    if (tags.length > 0) {
      baseLines.push(`哈喽~同为${tags[0]}的我来打招呼啦`);
    }

    // 随机打乱
    return baseLines.sort(() => Math.random() - 0.5).slice(0, 5);
  }
}

// 导出单例
export const aiService = new AIService();
