import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores'
import { Sparkles, Moon, Star } from 'lucide-react'

export default function Login() {
  const navigate = useNavigate()
  const { login, register } = useAuthStore()
  const [isLogin, setIsLogin] = useState(true)
  const [form, setForm] = useState({ phone: '', password: '', nickname: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      if (isLogin) {
        await login(form.phone, form.password)
      } else {
        await register(form.phone, form.password, form.nickname)
      }
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.error || '操作失败，请重试')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      {/* 背景装饰 */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-10 animate-float opacity-30">
          <Star className="w-6 h-6 text-primary" />
        </div>
        <div className="absolute top-40 right-20 animate-float opacity-20" style={{ animationDelay: '1s' }}>
          <Moon className="w-8 h-8 text-secondary" />
        </div>
        <div className="absolute bottom-40 left-1/4 animate-float opacity-25" style={{ animationDelay: '0.5s' }}>
          <Sparkles className="w-5 h-5 text-accent" />
        </div>
      </div>

      <div className="w-full max-w-md relative">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br from-primary to-secondary mb-4 animate-pulse-glow">
            <Sparkles className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-3xl font-bold gradient-text">心灵社交</h1>
          <p className="text-text-secondary mt-2">找到灵魂的共鸣</p>
        </div>

        {/* 表单卡片 */}
        <div className="glass-card rounded-3xl p-8">
          <h2 className="text-xl font-semibold mb-6 text-center">
            {isLogin ? '欢迎回来' : '创建账号'}
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <div>
                <label className="block text-sm text-text-secondary mb-2">昵称</label>
                <input
                  type="text"
                  className="input-field"
                  placeholder="给自己起个名字"
                  value={form.nickname}
                  onChange={(e) => setForm({ ...form, nickname: e.target.value })}
                  required={!isLogin}
                />
              </div>
            )}

            <div>
              <label className="block text-sm text-text-secondary mb-2">手机号</label>
              <input
                type="tel"
                className="input-field"
                placeholder="请输入手机号"
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
                required
              />
            </div>

            <div>
              <label className="block text-sm text-text-secondary mb-2">密码</label>
              <input
                type="password"
                className="input-field"
                placeholder="请输入密码"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                required
              />
            </div>

            {error && (
              <div className="text-red-400 text-sm text-center bg-red-500/10 py-2 rounded-lg">
                {error}
              </div>
            )}

            <button
              type="submit"
              className="btn-primary w-full"
              disabled={loading}
            >
              {loading ? '处理中...' : isLogin ? '登录' : '注册'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <button
              onClick={() => setIsLogin(!isLogin)}
              className="text-primary hover:text-primary-light text-sm transition-colors"
            >
              {isLogin ? '还没有账号？立即注册' : '已有账号？登录'}
            </button>
          </div>

          {/* 测试账号提示 */}
          <div className="mt-4 p-3 bg-white/5 rounded-lg text-xs text-text-muted">
            <p className="font-semibold mb-1">👻 演示账号:</p>
            <p>手机号: 13800138000</p>
            <p>密码: 123456</p>
            <p className="text-text-muted mt-1">(需要先注册任意账号，种子用户稍后可用)</p>
          </div>
        </div>
      </div>
    </div>
  )
}
