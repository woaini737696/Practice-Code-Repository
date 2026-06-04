import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useMatchStore } from '../stores'
import { X, Heart, MessageCircle, Sparkles, ChevronLeft, ChevronRight } from 'lucide-react'

export default function Match() {
  const navigate = useNavigate()
  const { recommendations, currentIndex, fetchRecommendations, swipe } = useMatchStore()
  const [currentCard, setCurrentCard] = useState(0)
  const [isAnimating, setIsAnimating] = useState(false)
  const [showMatch, setShowMatch] = useState(false)

  useEffect(() => {
    if (recommendations.length === 0) {
      fetchRecommendations()
    }
  }, [])

  const currentUser = recommendations[currentCard]

  const handleSwipe = async (action) => {
    if (!currentUser || isAnimating) return

    setIsAnimating(true)
    
    const direction = action === 'like' ? 1 : -1
    
    // 动画效果
    setCurrentCard(prev => prev + 1)
    
    try {
      const result = await swipe(currentUser.id, action)
      if (result.matched) {
        setShowMatch(true)
        setTimeout(() => setShowMatch(false), 3000)
      }
    } catch (error) {
      console.error('滑动失败:', error)
    }
    
    setTimeout(() => setIsAnimating(false), 300)
  }

  if (recommendations.length === 0 || currentIndex >= recommendations.length) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-4">
        <div className="text-center">
          <Sparkles className="w-16 h-16 mx-auto mb-4 text-primary opacity-50" />
          <h2 className="text-xl font-semibold mb-2">暂无更多推荐</h2>
          <p className="text-text-secondary mb-6">稍后再来看看吧~</p>
          <button onClick={() => fetchRecommendations()} className="btn-primary">
            刷新推荐
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen pb-24">
      {/* 顶部 */}
      <header className="sticky top-0 z-40 glass px-4 py-3">
        <div className="max-w-md mx-auto">
          <h1 className="text-center font-semibold">发现</h1>
        </div>
      </header>

      <main className="max-w-md mx-auto p-4">
        <div className="relative h-[500px]">
          <AnimatePresence>
            {recommendations.slice(currentCard, currentCard + 2).map((user, index) => {
              const isFirst = index === 0
              return (
                <motion.div
                  key={user.id}
                  initial={{ scale: 0.95, opacity: 0 }}
                  animate={{ 
                    scale: isFirst ? 1 : 0.95,
                    opacity: isFirst ? 1 : 0.5
                  }}
                  exit={{ x: isFirst ? (currentUser && currentUser.action === 'like' ? 300 : -300) : 0 }}
                  transition={{ duration: 0.3 }}
                  className="absolute inset-0 glass-card rounded-3xl overflow-hidden"
                >
                  {/* 用户头像 */}
                  <div className="h-3/4 relative">
                    <img
                      src={user.avatar || `https://api.dicebear.com/7.x/avataaars/svg?seed=${user.nickname}`}
                      alt={user.nickname}
                      className="w-full h-full object-cover"
                    />
                    
                    {/* 渐变遮罩 */}
                    <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent" />
                    
                    {/* 匹配度 */}
                    <div className="absolute top-4 right-4">
                      <span className={`match-badge ${user.matchScore >= 80 ? 'high' : user.matchScore >= 50 ? 'medium' : 'low'}`}>
                        {user.matchScore}% 匹配
                      </span>
                    </div>

                    {/* 用户信息 */}
                    <div className="absolute bottom-4 left-4 right-4">
                      <h2 className="text-2xl font-bold mb-2">
                        {user.nickname}
                        {user.soul_type && (
                          <span className="ml-2 text-sm font-normal text-primary">{user.soul_type}</span>
                        )}
                      </h2>
                      
                      <p className="text-sm text-gray-200 mb-3 line-clamp-2">
                        {user.bio || '这个人很神秘，没有个人简介'}
                      </p>
                      
                      {/* 标签 */}
                      <div className="flex flex-wrap gap-2">
                        {user.soul_tags?.map((tag, i) => (
                          <span key={i} className="soul-tag">{tag}</span>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* 兴趣 */}
                  <div className="h-1/4 p-4">
                    <p className="text-sm text-text-secondary mb-2">共同兴趣</p>
                    <div className="flex flex-wrap gap-2">
                      {user.interests?.slice(0, 4).map((interest, i) => (
                        <span
                          key={i}
                          className={`px-3 py-1 rounded-full text-xs ${
                            user.commonInterests?.includes(interest)
                              ? 'bg-primary/30 text-primary'
                              : 'bg-white/10 text-text-secondary'
                          }`}
                        >
                          {interest}
                        </span>
                      ))}
                    </div>
                  </div>
                </motion.div>
              )
            })}
          </AnimatePresence>
        </div>

        {/* 操作按钮 */}
        <div className="flex justify-center gap-6 mt-8">
          <button
            onClick={() => handleSwipe('pass')}
            className="w-16 h-16 rounded-full bg-white/10 border-2 border-red-500/50 flex items-center justify-center hover:bg-red-500/20 transition-all hover:scale-110"
          >
            <X className="w-8 h-8 text-red-500" />
          </button>
          
          <button
            onClick={() => handleSwipe('like')}
            className="w-20 h-20 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center hover:scale-110 transition-all animate-pulse-glow"
          >
            <Heart className="w-10 h-10 text-white" />
          </button>
          
          <button
            onClick={() => navigate(`/chat/${user?.id}`)}
            className="w-16 h-16 rounded-full bg-white/10 border-2 border-secondary/50 flex items-center justify-center hover:bg-secondary/20 transition-all hover:scale-110"
          >
            <MessageCircle className="w-8 h-8 text-secondary" />
          </button>
        </div>

        <p className="text-center text-text-muted text-sm mt-4">
          左滑跳过 · 右滑喜欢 · 点击聊天
        </p>
      </main>

      {/* 匹配成功弹窗 */}
      <AnimatePresence>
        {showMatch && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/70"
          >
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0 }}
              className="glass-card rounded-3xl p-8 text-center max-w-sm mx-4"
            >
              <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center animate-pulse-glow">
                <Heart className="w-10 h-10 text-white" />
              </div>
              <h2 className="text-2xl font-bold mb-2">匹配成功！</h2>
              <p className="text-text-secondary mb-6">你们都喜欢对方，快开始聊天吧</p>
              <button
                onClick={() => setShowMatch(false)}
                className="btn-primary w-full"
              >
                开始聊天
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
