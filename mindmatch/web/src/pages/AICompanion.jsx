import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores'
import { motion, AnimatePresence } from 'framer-motion'
import { Sparkles, Send, ArrowLeft, MessageCircle, Lightbulb, Heart, User } from 'lucide-react'
import api from '../services/api'

export default function AICompanion() {
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const [mode, setMode] = useState('companion') // 'companion' | 'advisor'
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [suggestions, setSuggestions] = useState([])
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  // 初始化对话
  useEffect(() => {
    const welcomeMessage = mode === 'companion'
      ? `你好呀，${user?.nickname || '朋友'}！我是你的AI灵魂伴侣 💫\n\n很高兴认识你！无论你想聊天、倾诉还是探讨人生，我都在这里陪伴你。\n\n今天有什么想聊的吗？`
      : `嗨，我是你的AI社交助手 ✨\n\n我可以帮你：\n• 找到合适的聊天话题\n• 给出社交建议\n• 优化你的聊天技巧\n\n有什么社交困惑想聊聊吗？`

    setMessages([
      { role: 'assistant', content: welcomeMessage }
    ])
  }, [mode])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || loading) return

    const userMessage = input.trim()
    setInput('')
    setLoading(true)

    // 添加用户消息
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])

    try {
      const response = await api.post('/ai/chat', {
        type: mode,
        message: userMessage
      })

      const { reply, suggestions: newSuggestions } = response.data

      // 添加AI回复
      setMessages(prev => [...prev, { role: 'assistant', content: reply }])
      
      // 更新建议
      if (newSuggestions?.length > 0) {
        setSuggestions(newSuggestions)
      }
    } catch (error) {
      console.error('AI回复失败:', error)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: '抱歉，我暂时无法回复你。请稍后再试～'
      }])
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleSuggestionClick = (text) => {
    setInput(text)
    inputRef.current?.focus()
  }

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-b from-background-primary to-background-secondary">
      {/* 顶部导航 */}
      <header className="glass px-4 py-3">
        <div className="max-w-lg mx-auto">
          <div className="flex items-center justify-between">
            <button onClick={() => navigate(-1)} className="p-2 -ml-2">
              <ArrowLeft className="w-6 h-6" />
            </button>
            
            {/* 模式切换 */}
            <div className="flex items-center gap-2 bg-white/10 rounded-full p-1">
              <button
                onClick={() => setMode('companion')}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                  mode === 'companion'
                    ? 'bg-primary text-white'
                    : 'text-text-secondary hover:text-white'
                }`}
              >
                <Heart className="w-4 h-4 inline mr-1" />
                灵魂伴侣
              </button>
              <button
                onClick={() => setMode('advisor')}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                  mode === 'advisor'
                    ? 'bg-secondary text-white'
                    : 'text-text-secondary hover:text-white'
                }`}
              >
                <Lightbulb className="w-4 h-4 inline mr-1" />
                社交助手
              </button>
            </div>

            <div className="w-10" />
          </div>
        </div>
      </header>

      {/* 消息区域 */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-lg mx-auto p-4 space-y-4">
          {/* AI欢迎卡片 */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-card rounded-2xl p-5 mb-4"
          >
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="font-semibold">
                  {mode === 'companion' ? 'AI灵魂伴侣' : 'AI社交助手'}
                </h3>
                <p className="text-xs text-text-muted">在线 · 随时陪伴</p>
              </div>
            </div>
            <p className="text-sm text-text-secondary">
              {mode === 'companion'
                ? '我是你的专属AI灵魂伴侣，可以陪你聊天、倾听你的心声、和你探讨各种话题~'
                : '我是你的AI社交顾问，可以帮你找到话题、优化聊天技巧、提升社交能力~'
              }
            </p>
          </motion.div>

          {/* 消息列表 */}
          <AnimatePresence>
            {messages.map((message, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`max-w-[80%] ${message.role === 'user' ? 'order-2' : 'order-1'}`}>
                  {message.role === 'assistant' && (
                    <div className="flex items-end gap-2 mb-2">
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center flex-shrink-0">
                        <Sparkles className="w-4 h-4 text-white" />
                      </div>
                    </div>
                  )}
                  <div
                    className={`px-4 py-3 rounded-2xl ${
                      message.role === 'user'
                        ? 'bg-gradient-to-br from-primary to-secondary text-white rounded-br-md'
                        : 'glass-card rounded-bl-md'
                    }`}
                  >
                    <p className="whitespace-pre-wrap text-sm leading-relaxed">
                      {message.content}
                    </p>
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {/* 加载指示 */}
          {loading && (
            <div className="flex justify-start">
              <div className="glass-card px-4 py-3 rounded-2xl rounded-bl-md">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}

          {/* 快捷建议 */}
          {suggestions.length > 0 && !loading && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="glass-card rounded-2xl p-4"
            >
              <p className="text-xs text-text-muted mb-3">你可以这样回复：</p>
              <div className="flex flex-wrap gap-2">
                {suggestions.map((suggestion, i) => (
                  <button
                    key={i}
                    onClick={() => handleSuggestionClick(suggestion)}
                    className="px-3 py-1.5 rounded-full bg-white/10 text-sm text-text-secondary hover:bg-primary/30 hover:text-white transition-all"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </motion.div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* 输入区域 */}
      <div className="glass border-t border-white/10">
        <div className="max-w-lg mx-auto p-4">
          <div className="flex items-end gap-3">
            <div className="flex-1">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={`给${mode === 'companion' ? 'AI灵魂伴侣' : 'AI社交助手'}发送消息...`}
                rows={1}
                className="input-field resize-none"
                style={{ height: 'auto', minHeight: '48px', maxHeight: '120px' }}
              />
            </div>
            <button
              onClick={handleSend}
              disabled={!input.trim() || loading}
              className="w-12 h-12 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center disabled:opacity-50 hover:scale-105 transition-transform"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
          
          {/* 快捷话题 */}
          <div className="flex gap-2 mt-3 overflow-x-auto pb-2">
            {[
              '聊聊今天的心情',
              '推荐一部电影',
              '如何开始聊天',
              '最近在读什么书'
            ].map((topic, i) => (
              <button
                key={i}
                onClick={() => handleSuggestionClick(topic)}
                className="flex-shrink-0 px-3 py-1.5 rounded-full bg-white/5 text-xs text-text-muted hover:bg-white/10 transition-colors"
              >
                {topic}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
