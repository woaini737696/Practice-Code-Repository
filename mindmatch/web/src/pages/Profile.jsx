import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores'
import { Camera, Sparkles, LogOut } from 'lucide-react'

export default function Profile() {
  const navigate = useNavigate()
  const { user, logout, updateProfile } = useAuthStore()
  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState({
    nickname: user?.nickname || '',
    bio: user?.bio || '',
    interests: user?.interests || []
  })
  const [saving, setSaving] = useState(false)

  const interestOptions = [
    '阅读', '电影', '音乐', '旅行', '摄影', '美食',
    '健身', '游戏', '编程', '设计', '写作', '户外',
    '艺术', '展览', '舞蹈', '社交'
  ]

  const handleSave = async () => {
    setSaving(true)
    try {
      await updateProfile(form)
      setEditing(false)
    } catch (error) {
      console.error('保存失败:', error)
    } finally {
      setSaving(false)
    }
  }

  const toggleInterest = (interest) => {
    setForm(prev => ({
      ...prev,
      interests: prev.interests.includes(interest)
        ? prev.interests.filter(i => i !== interest)
        : [...prev.interests, interest]
    }))
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen pb-20">
      {/* 顶部 */}
      <header className="glass px-4 py-3 flex items-center justify-between">
        <h1 className="text-lg font-semibold">个人中心</h1>
        {!editing && (
          <button onClick={() => setEditing(true)} className="text-primary">
            编辑资料
          </button>
        )}
      </header>

      <main className="max-w-md mx-auto p-4 space-y-6">
        {/* 头像区域 */}
        <div className="text-center">
          <div className="relative inline-block">
            <div className="w-28 h-28 rounded-full overflow-hidden border-4 border-primary/30 mx-auto">
              <img
                src={user?.avatar || `https://api.dicebear.com/7.x/avataaars/svg?seed=${user?.nickname}`}
                alt={user?.nickname}
                className="w-full h-full object-cover"
              />
            </div>
            {editing && (
              <button className="absolute bottom-0 right-0 w-10 h-10 rounded-full bg-primary flex items-center justify-center">
                <Camera className="w-5 h-5" />
              </button>
            )}
          </div>
        </div>

        {/* 基本信息 */}
        {editing ? (
          <div className="glass-card rounded-2xl p-5 space-y-4">
            <div>
              <label className="block text-sm text-text-secondary mb-2">昵称</label>
              <input
                type="text"
                value={form.nickname}
                onChange={(e) => setForm({ ...form, nickname: e.target.value })}
                className="input-field"
              />
            </div>

            <div>
              <label className="block text-sm text-text-secondary mb-2">个人简介</label>
              <textarea
                value={form.bio}
                onChange={(e) => setForm({ ...form, bio: e.target.value })}
                className="input-field resize-none h-24"
                placeholder="介绍一下自己..."
              />
            </div>

            <div>
              <label className="block text-sm text-text-secondary mb-2">兴趣爱好</label>
              <div className="flex flex-wrap gap-2">
                {interestOptions.map((interest) => (
                  <button
                    key={interest}
                    onClick={() => toggleInterest(interest)}
                    className={`px-3 py-1.5 rounded-full text-sm transition-all ${
                      form.interests.includes(interest)
                        ? 'bg-primary text-white'
                        : 'bg-white/10 text-text-secondary'
                    }`}
                  >
                    {interest}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex gap-3 pt-2">
              <button
                onClick={() => setEditing(false)}
                className="btn-secondary flex-1"
              >
                取消
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="btn-primary flex-1"
              >
                {saving ? '保存中...' : '保存'}
              </button>
            </div>
          </div>
        ) : (
          <div className="glass-card rounded-2xl p-5">
            <div className="text-center mb-4">
              <h2 className="text-xl font-bold">{user?.nickname}</h2>
              {user?.soul_type && (
                <span className="soul-tag mt-2 inline-block">{user.soul_type}</span>
              )}
            </div>

            <p className="text-text-secondary text-center mb-4">
              {user?.bio || '还没有个人简介'}
            </p>

            {user?.soul_tags?.length > 0 && (
              <div className="flex flex-wrap justify-center gap-2 mb-4">
                {user.soul_tags.map((tag, i) => (
                  <span key={i} className="soul-tag">{tag}</span>
                ))}
              </div>
            )}
          </div>
        )}

        {/* 兴趣标签 */}
        {!editing && user?.interests?.length > 0 && (
          <div className="glass-card rounded-2xl p-5">
            <h3 className="font-semibold mb-3">兴趣爱好</h3>
            <div className="flex flex-wrap gap-2">
              {user.interests.map((interest, i) => (
                <span key={i} className="px-3 py-1.5 rounded-full bg-white/10 text-sm">
                  {interest}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* 功能入口 */}
        <div className="space-y-3">
          <button
            onClick={() => navigate('/soul-test')}
            className="w-full glass-card rounded-2xl p-4 flex items-center gap-4 card-hover"
          >
            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <div className="text-left flex-1">
              <h3 className="font-semibold">灵魂测试</h3>
              <p className="text-sm text-text-secondary">
                {user?.soul_type ? `已完成 (${user.soul_type})` : '点击开始测试'}
              </p>
            </div>
          </button>
        </div>

        {/* 退出登录 */}
        <button
          onClick={handleLogout}
          className="w-full py-3 rounded-full border border-red-500/50 text-red-400 flex items-center justify-center gap-2 hover:bg-red-500/10 transition-colors"
        >
          <LogOut className="w-5 h-5" />
          退出登录
        </button>
      </main>
    </div>
  )
}
