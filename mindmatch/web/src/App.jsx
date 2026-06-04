import { Routes, Route, Navigate, BrowserRouter } from 'react-router-dom'
import { useAuthStore } from './stores'
import Login from './pages/Login'
import Home from './pages/Home'
import Match from './pages/Match'
import ChatList from './pages/ChatList'
import Chat from './pages/Chat'
import Profile from './pages/Profile'
import SoulTest from './pages/SoulTest'
import AICompanion from './pages/AICompanion'

function PrivateRoute({ children }) {
  const token = localStorage.getItem('mindmatch-auth')
  return token ? children : <Navigate to="/login" />
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen stars-bg">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<PrivateRoute><Home /></PrivateRoute>} />
          <Route path="/match" element={<PrivateRoute><Match /></PrivateRoute>} />
          <Route path="/chat" element={<PrivateRoute><ChatList /></PrivateRoute>} />
          <Route path="/chat/:roomId" element={<PrivateRoute><Chat /></PrivateRoute>} />
          <Route path="/profile" element={<PrivateRoute><Profile /></PrivateRoute>} />
          <Route path="/soul-test" element={<PrivateRoute><SoulTest /></PrivateRoute>} />
          <Route path="/ai-companion" element={<PrivateRoute><AICompanion /></PrivateRoute>} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}
