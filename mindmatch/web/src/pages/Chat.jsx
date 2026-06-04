import { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useChatStore, useAuthStore } from '../stores'
import { ArrowLeft, Send, MoreVertical } from 'lucide-react'
import { format } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import io from 'socket.io-client'

export default function Chat() {
  const { roomId } = useParams()
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const { currentMessages, fetchMessages, sendMessage, addMessage } = useChatStore()
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const messagesEndRef = useRef(null)
  const socketRef = useRef(null)

  useEffect(() => {
    // 获取聊天信息
    const chatInfo = localStorage.getItem('mindmatch-chats')
    if (chatInfo) {
      const chats = JSON.parse(chatInfo)
      const currentChat = chats.find(c => c.id === parseInt(roomId))
      if (currentChat) {
        // 设置标题等
      }
    }

    fetchMessages(roomId)

    // 连接Socket.IO
    socketRef.current = io('/', {
      transports: ['websocket']
    })

    socketRef.current.emit('joinRoom', roomId)
    socketRef.current.emit('userOnline', user?.id)

    socketRef.current.on('newMessage', (message) => {
      if (message.sender_id !== user?.id) {
        addMessage(message)
      }
    })

    return () => {
      socketRef.current?.disconnect()
    }
  }, [roomId])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [currentMessages])

  const handleSend = async () => {
    if (!input.trim() || sending) return

    setSending(true)
    try {
      await sendMessage(roomId, input.trim())
      setInput('')
      socketRef.current?.emit('sendMessage', { roomId, content: input.trim() })
    } catch (error) {
      console.error('发送失败:', error)
    } finally {
      setSending(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* 顶部导航 */}
      <header className="glass px-4 py-3 flex items-center gap-3">
        <button onClick={() => navigate(-1)} className="p-2 -ml-2">
          <ArrowLeft className="w-6 h-6" />
        </button>
        <div className="flex-1">
          <h1 className="font-semibold">聊天</h1>
        </div>
        <button className="p-2 -mr-2">
          <MoreVertical className="w-6 h-6" />
        </button>
      </header>

      {/* 消息列表 */}
      <main className="flex-1 overflow-y-auto p-4 space-y-4">
        {currentMessages.map((message) => {
          const isMe = message.sender_id === user?.id
          const isSystem = message.type === 'system'

          if (isSystem) {
            return (
              <div key={message.id} className="text-center">
                <span className="inline-block px-4 py-2 rounded-full bg-white/5 text-text-muted text-sm">
                  {JSON.parse(message.content)?.message || message.content}
                </span>
              </div>
            )
          }

          return (
            <div
              key={message.id}
              className={`flex ${isMe ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`max-w-[75%] ${isMe ? 'order-2' : 'order-1'}`}>
                <div
                  className={`px-4 py-3 rounded-2xl ${
                    isMe
                      ? 'bg-gradient-to-br from-primary to-secondary text-white rounded-br-md'
                      : 'glass-card rounded-bl-md'
                  }`}
                >
                  <p className="whitespace-pre-wrap break-words">{message.content}</p>
                </div>
                <p className="text-xs text-text-muted mt-1 text-right">
                  {format(new Date(message.created_at), 'HH:mm', { locale: zhCN })}
                </p>
              </div>
            </div>
          )
        })}
        <div ref={messagesEndRef} />
      </main>

      {/* 输入框 */}
      <div className="glass px-4 py-3">
        <div className="max-w-md mx-auto flex items-end gap-3">
          <div className="flex-1">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="发送消息..."
              rows={1}
              className="input-field resize-none max-h-32"
              style={{ height: 'auto', minHeight: '44px' }}
            />
          </div>
          <button
            onClick={handleSend}
            disabled={!input.trim() || sending}
            className="w-12 h-12 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed hover:scale-105 transition-transform"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  )
}
