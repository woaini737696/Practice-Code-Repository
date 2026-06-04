import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import api from '../services/api'

export const useAuthStore = create(
  persist(
    (set, get) => ({
      token: null,
      user: null,
      
      login: async (phone, password) => {
        const response = await api.post('/users/login', { phone, password })
        const { user, token } = response.data
        set({ user, token })
        return { success: true }
      },
      
      register: async (phone, password, nickname) => {
        const response = await api.post('/users/register', { phone, password, nickname })
        const { user, token } = response.data
        set({ user, token })
        return { success: true }
      },
      
      fetchProfile: async () => {
        try {
          const response = await api.get('/users/profile')
          set({ user: response.data.user })
        } catch (error) {
          console.error('获取用户资料失败:', error)
        }
      },
      
      updateProfile: async (data) => {
        const response = await api.put('/users/profile', data)
        set({ user: response.data.user })
      },
      
      logout: () => {
        set({ token: null, user: null })
      },
      
      isAuthenticated: () => !!get().token
    }),
    {
      name: 'mindmatch-auth',
      partialize: (state) => ({ token: state.token, user: state.user })
    }
  )
)

// 匹配相关状态
export const useMatchStore = create((set, get) => ({
  recommendations: [],
  matches: [],
  currentIndex: 0,
  
  fetchRecommendations: async () => {
    try {
      const response = await api.get('/match/recommendations')
      set({ recommendations: response.data.users, currentIndex: 0 })
    } catch (error) {
      console.error('获取推荐失败:', error)
    }
  },
  
  swipe: async (targetId, action) => {
    const response = await api.post('/match/swipe', { targetId, action })
    const { matched } = response.data
    
    // 移动到下一个
    set(state => ({ currentIndex: state.currentIndex + 1 }))
    
    return response.data
  },
  
  fetchMatches: async () => {
    try {
      const response = await api.get('/match/mutual')
      set({ matches: response.data.matches })
    } catch (error) {
      console.error('获取匹配列表失败:', error)
    }
  }
}))

// 聊天相关状态
export const useChatStore = create((set) => ({
  chats: [],
  currentMessages: [],
  
  fetchChats: async () => {
    try {
      const response = await api.get('/chat/list')
      set({ chats: response.data.chats })
    } catch (error) {
      console.error('获取聊天列表失败:', error)
    }
  },
  
  fetchMessages: async (roomId) => {
    try {
      const response = await api.get(`/chat/${roomId}/messages`)
      set({ currentMessages: response.data.messages })
    } catch (error) {
      console.error('获取消息失败:', error)
    }
  },
  
  sendMessage: async (roomId, content) => {
    const response = await api.post(`/chat/${roomId}/messages`, { content })
    set(state => ({
      currentMessages: [...state.currentMessages, response.data.message]
    }))
    return response.data.message
  },
  
  addMessage: (message) => {
    set(state => ({
      currentMessages: [...state.currentMessages, message]
    }))
  }
}))
