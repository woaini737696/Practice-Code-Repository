import { useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore, useMatchStore } from '../stores'
import { Home, Search, MessageCircle, User, Sparkles, Compass } from 'lucide-react'

export default function HomePage() {
  const navigate = useNavigate()
  const { user, fetchProfile } = useAuthStore()
  const { recommendations, matches, fetchRecommendations, fetchMatches } = useMatchStore()

  useEffect(() => {
    fetchProfile()
    fetchRecommendations()
    fetchMatches()
  }, [])

  const hasCompletedSoulTest = user?.soul_type

  return (
    <div className="min-h-screen pb-20">
      {/* 顶部导航 */}
      <header className="sticky top-0 z-40 glass px-4 py-3">
        <div className="max-w-md mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-primary" />
            <h1 className="text-lg font-bold gradient-text">心灵社交</h1>
          </div>
          <Link to="/ai-companion" className="p-2 rounded-full bg-primary/20">
            <Sparkles className="w-5 h-5 text-primary" />
          </Link>
        </div>
      </header>

      <main className="max-w-md mx-auto p-4">
        {/* 灵魂测试提醒 */}
        {!hasCompletedSoulTest && (
          <div className="glass-card rounded-2xl p-6 mb-6 text-center card-hover">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center">
              <Sparkles className="w-8 h-8 text-white" />
            </div>
            <h2 className="text-lg font-semibold mb-2">完成灵魂测试</h2>
            <p className="text-text-secondary text-sm mb-4">
              测试你的灵魂类型，获得更精准的匹配推荐
            </p>
            <button
              onClick={() => navigate('/soul-test')}
              className="btn-primary"
            >
              开始测试
            </button>
          </div>
        )}

        {/* 快速入口 */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <Link
            to="/match"
            className="glass-card rounded-2xl p-5 text-center card-hover"
          >
            <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center">
              <Compass className="w-6 h-6 text-white" />
            </div>
            <h3 className="font-semibold mb-1">发现匹配</h3>
            <p className="text-text-muted text-xs">
              {recommendations.length > 0 ? `${recommendations.length}个新推荐` : '暂无推荐'}
            </p>
          </Link>

          <Link
            to="/ai-companion"
            className="glass-card rounded-2xl p-5 text-center card-hover"
          >
            <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <h3 className="font-semibold mb-1">AI伴侣</h3>
            <p className="text-text-muted text-xs">24/7陪伴支持</p>
          </Link>
        </div>

        {/* 匹配列表预览 */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold">已匹配的好友</h2>
            <Link to="/match" className="text-primary text-sm">查看全部</Link>
          </div>

          {matches.length > 0 ? (
            <div className="flex gap-3 overflow-x-auto pb-2">
              {matches.slice(0, 6).map((match) => (
                <div key={match.id} className="flex-shrink-0 text-center">
                  <div className="w-16 h-16 rounded-full overflow-hidden border-2 border-primary/50 mb-2">
                    <img
                      src={match.avatar || `https://api.dicebear.com/7.x/avataaars/svg?seed=${match.nickname}`}
                      alt={match.nickname}
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <p className="text-xs truncate w-16">{match.nickname}</p>
                </div>
              ))}
            </div>
          ) : (
            <div className="glass-card rounded-2xl p-8 text-center">
              <MessageCircle className="w-12 h-12 mx-auto mb-3 text-text-muted opacity-50" />
              <p className="text-text-secondary">还没有匹配的好友</p>
              <p className="text-text-muted text-sm mt-1">去发现页探索吧</p>
            </div>
          )}
        </div>

        {/* 用户信息卡片 */}
        {user && (
          <div className="glass-card rounded-2xl p-5">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 rounded-full overflow-hidden border-2 border-primary/50">
                <img
                  src={user.avatar || `https://api.dicebear.com/7.x/avataaars/svg?seed=${user.nickname}`}
                  alt={user.nickname}
                  className="w-full h-full object-cover"
                />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-lg">{user.nickname}</h3>
                <p className="text-text-secondary text-sm">
                  {user.soul_type ? (
                    <span className="soul-tag">{user.soul_type}</span>
                  ) : (
                    '未完成灵魂测试'
                  )}
                </p>
              </div>
              <Link to="/profile" className="p-2 rounded-full bg-white/10">
                <User className="w-5 h-5 text-text-secondary" />
              </Link>
            </div>
          </div>
        )}
      </main>

      {/* 底部导航 */}
      <nav className="fixed bottom-0 left-0 right-0 glass border-t border-white/10">
        <div className="max-w-md mx-auto flex justify-around py-3">
          <Link to="/" className="flex flex-col items-center gap-1 text-primary">
            <Home className="w-6 h-6" />
            <span className="text-xs">首页</span>
          </Link>
          <Link to="/match" className="flex flex-col items-center gap-1 text-text-muted">
            <Search className="w-6 h-6" />
            <span className="text-xs">发现</span>
          </Link>
          <Link to="/chat" className="flex flex-col items-center gap-1 text-text-muted">
            <MessageCircle className="w-6 h-6" />
            <span className="text-xs">聊天</span>
          </Link>
          <Link to="/profile" className="flex flex-col items-center gap-1 text-text-muted">
            <User className="w-6 h-6" />
            <span className="text-xs">我的</span>
          </Link>
        </div>
      </nav>
    </div>
  )
}
