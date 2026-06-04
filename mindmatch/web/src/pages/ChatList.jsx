import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useChatStore } from '../stores'
import { MessageCircle, Circle } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'

export default function ChatList() {
  const { chats, fetchChats } = useChatStore()

  useEffect(() => {
    fetchChats()
  }, [])

  return (
    <div className="min-h-screen pb-20">
      {/* 顶部导航 */}
      <header className="sticky top-0 z-40 glass px-4 py-3">
        <div className="max-w-md mx-auto">
          <h1 className="text-lg font-semibold">消息</h1>
        </div>
      </header>

      <main className="max-w-md mx-auto p-4">
        {chats.length > 0 ? (
          <div className="space-y-3">
            {chats.map((chat) => (
              <Link
                key={chat.id}
                to={`/chat/${chat.id}`}
                className="glass-card rounded-2xl p-4 flex items-center gap-4 card-hover"
              >
                <div className="relative">
                  <div className="w-14 h-14 rounded-full overflow-hidden border border-primary/30">
                    <img
                      src={chat.partner_avatar || `https://api.dicebear.com/7.x/avataaars/svg?seed=${chat.partner_name}`}
                      alt={chat.partner_name}
                      className="w-full h-full object-cover"
                    />
                  </div>
                  {chat.unread_count > 0 && (
                    <div className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-primary flex items-center justify-center text-xs">
                      {chat.unread_count}
                    </div>
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <h3 className="font-semibold truncate">{chat.partner_name}</h3>
                    <span className="text-xs text-text-muted">
                      {chat.last_time && formatDistanceToNow(new Date(chat.last_time), { addSuffix: true, locale: zhCN })}
                    </span>
                  </div>
                  <p className="text-sm text-text-secondary truncate">
                    {chat.last_message || '开始聊天吧~'}
                  </p>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="text-center py-20">
            <MessageCircle className="w-16 h-16 mx-auto mb-4 text-text-muted opacity-50" />
            <h2 className="text-lg font-semibold mb-2">暂无消息</h2>
            <p className="text-text-secondary">去发现页匹配感兴趣的人吧</p>
          </div>
        )}
      </main>
    </div>
  )
}
